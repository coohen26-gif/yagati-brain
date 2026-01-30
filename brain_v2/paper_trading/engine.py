"""
Paper Trading Engine

Main engine for paper trading. Completely isolated from the main trading flow.
Manages the full lifecycle of paper trades: signal detection, position opening,
monitoring, and closing.
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional
from brain_v2.paper_trading.account import PaperAccount
from brain_v2.paper_trading.position import PositionCalculator
from brain_v2.paper_trading.recorder import AirtableRecorder
from brain_v2.ingest.market_data import MarketDataFetcher
from brain_v2.features.technical import compute_features


class PaperTradingEngine:
    """Main paper trading engine"""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize paper trading engine.
        
        Args:
            initial_capital: Initial capital (default: 100,000 USDT)
        """
        self.recorder = AirtableRecorder()
        self.account = PaperAccount(self.recorder)
        self.calculator = PositionCalculator(risk_percent=0.01, rr_ratio=2.0)
        self.initial_capital = initial_capital
        self.fetcher = MarketDataFetcher()
        
        # Initialize account on first run
        self.account.initialize(initial_capital)
    
    def run_cycle(self):
        """
        Execute one paper trading cycle.
        Called at the end of main analysis cycle.
        """
        try:
            print("\n" + "="*60)
            print("📊 Paper Trading Cycle")
            print("="*60)
            
            # Get current account state
            stats = self.account.get_stats()
            equity = stats["equity"]
            
            print(f"Equity: {equity:.2f} USDT")
            print(f"Trades: {stats['total_trades']} ({stats['winning_trades']}W/{stats['losing_trades']}L)")
            
            # 1. Manage open trades (check for SL/TP hits)
            self._manage_open_trades()
            
            # 2. Check for new signals if no trade is open
            if not self._has_open_trades():
                self._check_new_signals()
            else:
                print("ℹ️  Paper Trading: Trade already open, skipping new signals")
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error in cycle: {e}")
            # Don't raise - keep it isolated
    
    def _is_valid_trade(self, trade_record: Dict) -> bool:
        """
        Check if a trade record has valid data.
        
        Args:
            trade_record: Trade record from Airtable
            
        Returns:
            True if trade has valid symbol and entry_price > 0
        """
        try:
            fields = trade_record.get('fields', {})
            symbol = fields.get('symbol')
            entry_price = float(fields.get('entry_price', 0))
            
            # Validate symbol exists and is not empty/whitespace
            if not symbol or not symbol.strip():
                return False
            
            # Validate entry_price is greater than 0
            if entry_price <= 0:
                return False
            
            return True
        except Exception as e:
            # Log validation failures due to data issues
            print(f"⚠️ Paper Trading: Invalid trade data: {e}")
            return False
    
    def _get_valid_open_trades(self) -> List[Dict]:
        """
        Get all valid open trades (filtering out invalid/placeholder trades).
        
        Returns:
            List of valid trade records
        """
        try:
            open_trades = self.recorder.get_open_trades()
            return [trade for trade in open_trades if self._is_valid_trade(trade)]
        except Exception as e:
            print(f"⚠️ Paper Trading: Error getting valid trades: {e}")
            return []
    
    def _has_open_trades(self) -> bool:
        """Check if there are any valid open trades"""
        try:
            valid_trades = self._get_valid_open_trades()
            return len(valid_trades) > 0
        except Exception as e:
            print(f"⚠️ Paper Trading: Error checking open trades: {e}")
            return False
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol.
        Reuses existing MarketDataFetcher to avoid new API calls.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            
        Returns:
            Current price or None if error
        """
        try:
            # Fetch recent candles (we just need the last close price)
            # Use 4h timeframe as it's commonly available
            candles = self.fetcher.fetch_ohlc(symbol, "4h", limit=1)
            
            if candles and len(candles) > 0:
                return float(candles[-1]["close"])
            
            return None
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error fetching price for {symbol}: {e}")
            return None
    
    def _get_market_features(self, symbol: str) -> Optional[Dict]:
        """
        Get market features for contextual snapshot.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Features dictionary or None if error
        """
        try:
            # Fetch candles for feature computation
            candles = self.fetcher.fetch_ohlc(symbol, "4h", limit=100)
            
            if not candles:
                return None
            
            # Compute features
            features = compute_features(candles)
            return features
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error fetching features for {symbol}: {e}")
            return None
    
    def _manage_open_trades(self):
        """Check and manage open trades for SL/TP hits"""
        try:
            valid_trades = self._get_valid_open_trades()
            
            if not valid_trades:
                print("ℹ️  Paper Trading: No open trades")
                return
            
            print(f"📈 Paper Trading: Monitoring {len(valid_trades)} open trade(s)")
            
            for trade_record in valid_trades:
                trade = trade_record['fields']
                record_id = trade_record['id']
                
                symbol = trade.get('symbol')
                direction = trade.get('direction')
                entry_price = float(trade.get('entry_price', 0))
                stop_loss = float(trade.get('stop_loss', 0))
                take_profit = float(trade.get('take_profit', 0))
                position_size = float(trade.get('position_size', 0))
                high_water_mark = float(trade.get('high_water_mark_price', entry_price))
                low_water_mark = float(trade.get('low_water_mark_price', entry_price))
                
                print(f"   {symbol} {direction} @ {entry_price:.2f}")
                print(f"   SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
                
                # Get current price
                current_price = self._get_current_price(symbol)
                
                if current_price is None:
                    print(f"   ⚠️  Could not fetch current price for {symbol}")
                    continue
                
                print(f"   Current: {current_price:.2f}")
                
                # Update water marks
                updated_marks = self.calculator.update_water_marks(
                    current_price,
                    high_water_mark,
                    low_water_mark,
                    direction
                )
                
                new_high = updated_marks["high_water_mark"]
                new_low = updated_marks["low_water_mark"]
                
                # Persist updated water marks to Airtable
                if new_high != high_water_mark or new_low != low_water_mark:
                    self.recorder.update_water_marks(record_id, new_high, new_low)
                    print(f"   💧 Water marks updated: High={new_high:.2f}, Low={new_low:.2f}")
                
                # Check for SL/TP hit
                hit_result = self.calculator.check_sl_tp_hit(
                    current_price,
                    direction,
                    stop_loss,
                    take_profit
                )
                
                if hit_result:
                    exit_price = current_price
                    exit_reason = hit_result
                    
                    # Close the trade
                    self._close_trade(trade_record, exit_price, exit_reason)
                else:
                    print(f"   ✅ Trade still open")
                
        except Exception as e:
            print(f"⚠️ Paper Trading: Error managing open trades: {e}")
    
    def _check_new_signals(self):
        """Check for new trading signals from setups_forming"""
        try:
            print("🔍 Paper Trading: Checking for new signals...")
            
            # Get forming setups
            setups = self.recorder.get_forming_setups()
            
            if not setups:
                print("   No forming setups found")
                return
            
            print(f"   Found {len(setups)} forming setup(s)")
            
            # Filter valid setups
            valid_setups = self._filter_valid_setups(setups)
            
            if not valid_setups:
                print("   No valid setups to trade")
                return
            
            # Take the first valid setup
            setup = valid_setups[0]
            fields = setup['fields']
            
            print(f"   📌 Selected setup: {fields.get('symbol')} - {fields.get('setup_type')}")
            
            # For now, we can't open a trade without current price data
            # In a real implementation, we would:
            # 1. Get current market price
            # 2. Calculate position with stop loss at a reasonable level
            # 3. Open the trade
            
            # TODO: Implement trade opening when price data is available
            print(f"   ⏳ Trade opening requires price data (not yet implemented)")
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error checking signals: {e}")
    
    def _filter_valid_setups(self, setups: List[Dict]) -> List[Dict]:
        """
        Filter setups to find valid trading opportunities.
        
        Args:
            setups: List of setup records from Airtable
            
        Returns:
            List of valid setups
        """
        valid = []
        
        for setup in setups:
            try:
                fields = setup.get('fields', {})
                
                # Check if setup has required fields
                if not fields.get('symbol'):
                    continue
                
                # Check if status is FORMING
                status = fields.get('status', '')
                if status != 'FORMING':
                    continue
                
                # Setup is valid
                valid.append(setup)
                
            except Exception as e:
                print(f"⚠️ Paper Trading: Error filtering setup: {e}")
                continue
        
        return valid
    
    def _open_trade(self, setup: Dict, position_params: Dict):
        """
        Open a new paper trade.
        
        Args:
            setup: Setup record from Airtable
            position_params: Calculated position parameters
        """
        try:
            fields = setup.get('fields', {})
            setup_id = setup.get('id', '')
            symbol = position_params["symbol"]
            
            # Get current equity
            equity = self.account.get_equity()
            
            # Get market features for contextual snapshot
            features = self._get_market_features(symbol)
            
            # Extract contextual data (with safe defaults)
            entry_context_volatility = None
            entry_context_trend = None
            entry_context_rsi = None
            entry_market_regime = None
            
            if features:
                entry_context_volatility = features.get('volatility')
                entry_context_trend = features.get('trend_strength')
                entry_context_rsi = features.get('rsi')
                entry_market_regime = features.get('market_regime')
            
            # Prepare trade data
            trade_data = {
                "symbol": position_params["symbol"],
                "direction": position_params["direction"],
                "entry_price": position_params["entry_price"],
                "position_size": position_params["position_size"],
                "stop_loss": position_params["stop_loss"],
                "take_profit": position_params["take_profit"],
                "risk_amount": position_params["risk_amount"],
                "equity_at_open": equity,
                "opened_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "setup_id": setup_id,
                # Initialize water marks at entry price
                "high_water_mark_price": position_params["entry_price"],
                "low_water_mark_price": position_params["entry_price"],
                # Contextual snapshot
                "entry_context_volatility": entry_context_volatility,
                "entry_context_trend": entry_context_trend,
                "entry_context_rsi": entry_context_rsi,
                "entry_market_regime": entry_market_regime,
                "entry_snapshot_version": "v1.0",
            }
            
            # Save to Airtable
            result = self.recorder.save_open_trade(trade_data)
            
            if result:
                print(f"✅ Paper Trading: Trade opened")
                print(f"   {trade_data['symbol']} {trade_data['direction']}")
                print(f"   Entry: {trade_data['entry_price']:.2f}")
                print(f"   Size: {trade_data['position_size']:.4f}")
                print(f"   SL: {trade_data['stop_loss']:.2f} | TP: {trade_data['take_profit']:.2f}")
                print(f"   Risk: {trade_data['risk_amount']:.2f} USDT ({self.calculator.risk_percent * 100}%)")
                if features and entry_context_volatility is not None:
                    print(f"   Context: Vol={entry_context_volatility:.2f}% | RSI={entry_context_rsi:.1f} | Regime={entry_market_regime}")
                else:
                    print("   Context: Not available")
            else:
                print(f"❌ Paper Trading: Failed to save trade")
                
        except Exception as e:
            print(f"❌ Paper Trading: Error opening trade: {e}")
    
    def _close_trade(self, trade_record: Dict, exit_price: float, reason: str):
        """
        Close a paper trade.
        
        Args:
            trade_record: Trade record from Airtable
            exit_price: Exit price
            reason: Exit reason (TP_HIT, SL_HIT, MANUAL)
        """
        try:
            trade = trade_record['fields']
            record_id = trade_record['id']
            
            # Extract trade details
            symbol = trade.get('symbol')
            direction = trade.get('direction')
            entry_price = float(trade.get('entry_price', 0))
            position_size = float(trade.get('position_size', 0))
            equity_at_open = float(trade.get('equity_at_open', 0))
            high_water_mark = float(trade.get('high_water_mark_price', entry_price))
            low_water_mark = float(trade.get('low_water_mark_price', entry_price))
            opened_at = trade.get('opened_at')
            
            # Calculate P&L
            pnl_data = self.calculator.calculate_pnl(
                entry_price,
                exit_price,
                position_size,
                direction
            )
            
            pnl = pnl_data["pnl"]
            pnl_percent = pnl_data["pnl_percent"]
            
            # Calculate MFE/MAE
            mfe_mae_data = self.calculator.calculate_mfe_mae(
                entry_price,
                high_water_mark,
                low_water_mark,
                direction
            )
            
            mfe_percent = mfe_mae_data["mfe_percent"]
            mae_percent = mfe_mae_data["mae_percent"]
            
            # Calculate duration
            closed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            duration_minutes = 0
            if opened_at:
                try:
                    opened_dt = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))
                    closed_dt = datetime.now(timezone.utc)
                    duration_minutes = int((closed_dt - opened_dt).total_seconds() / 60)
                except Exception as e:
                    print(f"⚠️ Paper Trading: Error calculating duration: {e}")
            
            # Update equity
            current_equity = self.account.get_equity()
            new_equity = current_equity + pnl
            is_win = pnl > 0
            
            # Prepare closed trade data
            closed_trade_data = {
                **trade,  # Copy all fields from open trade
                "exit_price": exit_price,
                "closed_at": closed_at,
                "duration_minutes": duration_minutes,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "pnl_usdt": pnl,
                "mfe_percent": mfe_percent,
                "mae_percent": mae_percent,
                "exit_reason": reason,
            }
            
            # Save to closed trades
            closed_result = self.recorder.save_closed_trade(closed_trade_data)
            
            if not closed_result:
                print(f"⚠️ Paper Trading: Failed to save closed trade")
                return
            
            # Delete from open trades
            delete_result = self.recorder.delete_open_trade(record_id)
            
            if not delete_result:
                print(f"⚠️ Paper Trading: Failed to delete open trade")
            
            # Update account equity
            update_result = self.account.update_equity(new_equity, is_win)
            
            if update_result:
                print(f"✅ Trade closed: {symbol} {direction}")
                print(f"   Reason: {reason}")
                print(f"   Entry: {entry_price:.2f} | Exit: {exit_price:.2f}")
                print(f"   P&L: {pnl:+.2f} USDT ({pnl_percent:+.2f}%)")
                print(f"   MFE: {mfe_percent:+.2f}% | MAE: {mae_percent:+.2f}%")
                print(f"   Duration: {duration_minutes} minutes")
                print(f"   New Equity: {new_equity:.2f} USDT")
            else:
                print(f"❌ Paper Trading: Failed to update equity")
                
        except Exception as e:
            print(f"❌ Paper Trading: Error closing trade: {e}")
