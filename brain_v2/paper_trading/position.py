"""
Position Calculator

Calculates position sizes, stop loss, and take profit levels
based on account equity and risk management rules.
"""

from typing import Dict, Optional


class PositionCalculator:
    """Calculates position sizes and risk/reward parameters"""
    
    def __init__(self, risk_percent: float = 0.01, rr_ratio: float = 2.0):
        """
        Initialize position calculator.
        
        Args:
            risk_percent: Risk per trade as decimal (default: 0.01 = 1%)
            rr_ratio: Risk/Reward ratio (default: 2.0 = 1:2)
        """
        self.risk_percent = risk_percent
        self.rr_ratio = rr_ratio
    
    def calculate_position(
        self,
        setup: Dict,
        equity: float
    ) -> Optional[Dict]:
        """
        Calculate position parameters for a setup.
        
        Args:
            setup: Setup dictionary with entry, stop_loss, direction
            equity: Current account equity
            
        Returns:
            Dictionary with position_size, stop_loss, take_profit, risk_amount
            or None if calculation fails
        """
        try:
            # Extract setup data
            fields = setup.get('fields', {})
            
            # For now, we'll use simplified assumptions since setups_forming
            # may not have all fields. We'll assume:
            # - Entry at current price (we'll need to get this from market)
            # - Stop loss based on volatility or fixed percentage
            # - Direction from setup if available
            
            symbol = fields.get('symbol')
            if not symbol:
                return None
            
            # Get setup type and direction
            setup_type = fields.get('setup_type', '')
            
            # Determine direction from setup type
            # Assume LONG for bullish setups, SHORT for bearish
            direction = 'LONG'  # Default
            if 'short' in setup_type.lower() or 'bear' in setup_type.lower() or 'sell' in setup_type.lower():
                direction = 'SHORT'
            elif 'long' in setup_type.lower() or 'bull' in setup_type.lower() or 'buy' in setup_type.lower():
                direction = 'LONG'
            
            # For now, use a simplified approach:
            # - Assume we need price data to calculate exact levels
            # - Return None to indicate we need price data
            # This will be enhanced when we have access to current prices
            
            print(f"⚠️ Paper Trading: Position calculation needs current price for {symbol}")
            return None
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error calculating position: {e}")
            return None
    
    def calculate_position_with_price(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        equity: float
    ) -> Optional[Dict]:
        """
        Calculate position with explicit price levels.
        
        Args:
            symbol: Trading symbol
            direction: LONG or SHORT
            entry_price: Entry price
            stop_loss: Stop loss price
            equity: Current account equity
            
        Returns:
            Dictionary with position parameters
        """
        try:
            # Validate inputs
            if entry_price <= 0 or stop_loss <= 0 or equity <= 0:
                print(f"⚠️ Paper Trading: Invalid price/equity values")
                return None
            
            # Calculate risk amount (1% of equity)
            risk_amount = equity * self.risk_percent
            
            # Calculate distance to stop loss
            distance_to_sl = abs(entry_price - stop_loss)
            
            if distance_to_sl == 0:
                print(f"⚠️ Paper Trading: Stop loss equals entry price")
                return None
            
            # Calculate position size
            # risk_amount = position_size * distance_to_sl
            # position_size = risk_amount / distance_to_sl
            position_size = risk_amount / distance_to_sl
            
            # Calculate take profit (RR 1:2)
            if direction == 'LONG':
                take_profit = entry_price + (distance_to_sl * self.rr_ratio)
            else:  # SHORT
                take_profit = entry_price - (distance_to_sl * self.rr_ratio)
            
            # Ensure take profit is valid
            if take_profit <= 0:
                print(f"⚠️ Paper Trading: Invalid take profit calculated")
                return None
            
            return {
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "position_size": position_size,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": risk_amount,
                "distance_to_sl": distance_to_sl,
            }
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error in position calculation: {e}")
            return None
    
    def check_sl_tp_hit(
        self,
        current_price: float,
        direction: str,
        stop_loss: float,
        take_profit: float
    ) -> Optional[str]:
        """
        Check if stop loss or take profit is hit.
        
        Args:
            current_price: Current market price
            direction: LONG or SHORT
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            'SL_HIT', 'TP_HIT', or None
        """
        try:
            if direction == 'LONG':
                if current_price <= stop_loss:
                    return 'SL_HIT'
                elif current_price >= take_profit:
                    return 'TP_HIT'
            else:  # SHORT
                if current_price >= stop_loss:
                    return 'SL_HIT'
                elif current_price <= take_profit:
                    return 'TP_HIT'
            
            return None
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error checking SL/TP: {e}")
            return None
    
    def calculate_pnl(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float,
        direction: str
    ) -> Dict:
        """
        Calculate profit/loss for a closed trade.
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            position_size: Position size
            direction: LONG or SHORT
            
        Returns:
            Dictionary with pnl and pnl_percent
        """
        try:
            # Calculate price difference
            if direction == 'LONG':
                price_diff = exit_price - entry_price
            else:  # SHORT
                price_diff = entry_price - exit_price
            
            # Calculate P&L
            pnl = price_diff * position_size
            
            # Calculate P&L percentage
            pnl_percent = (price_diff / entry_price) * 100 if entry_price > 0 else 0
            
            return {
                "pnl": pnl,
                "pnl_percent": pnl_percent
            }
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error calculating PnL: {e}")
            return {"pnl": 0, "pnl_percent": 0}
    
    def calculate_mfe_mae(
        self,
        entry_price: float,
        high_water_mark: float,
        low_water_mark: float,
        direction: str
    ) -> Dict:
        """
        Calculate Maximum Favorable Excursion (MFE) and Maximum Adverse Excursion (MAE).
        
        Args:
            entry_price: Entry price
            high_water_mark: Highest price reached during trade
            low_water_mark: Lowest price reached during trade
            direction: LONG or SHORT
            
        Returns:
            Dictionary with mfe_percent and mae_percent
        """
        try:
            if entry_price <= 0:
                return {"mfe_percent": 0, "mae_percent": 0}
            
            if direction == 'LONG':
                # For LONG trades:
                # MFE = highest point reached (favorable)
                # MAE = lowest point reached (adverse)
                mfe_percent = ((high_water_mark - entry_price) / entry_price) * 100
                mae_percent = ((low_water_mark - entry_price) / entry_price) * 100
            else:  # SHORT
                # For SHORT trades:
                # MFE = lowest point reached (favorable)
                # MAE = highest point reached (adverse)
                mfe_percent = ((entry_price - low_water_mark) / entry_price) * 100
                mae_percent = ((entry_price - high_water_mark) / entry_price) * 100
            
            return {
                "mfe_percent": mfe_percent,
                "mae_percent": mae_percent
            }
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error calculating MFE/MAE: {e}")
            return {"mfe_percent": 0, "mae_percent": 0}
    
    def update_water_marks(
        self,
        current_price: float,
        high_water_mark: float,
        low_water_mark: float,
        direction: str
    ) -> Dict:
        """
        Update water marks based on current price.
        
        Args:
            current_price: Current market price
            high_water_mark: Current high water mark
            low_water_mark: Current low water mark
            direction: LONG or SHORT
            
        Returns:
            Dictionary with updated high_water_mark and low_water_mark
        """
        try:
            new_high = high_water_mark
            new_low = low_water_mark
            
            if direction == 'LONG':
                new_high = max(high_water_mark, current_price)
                new_low = min(low_water_mark, current_price)
            else:  # SHORT
                new_low = min(low_water_mark, current_price)
                new_high = max(high_water_mark, current_price)
            
            return {
                "high_water_mark": new_high,
                "low_water_mark": new_low
            }
            
        except Exception as e:
            print(f"⚠️ Paper Trading: Error updating water marks: {e}")
            return {
                "high_water_mark": high_water_mark,
                "low_water_mark": low_water_mark
            }
