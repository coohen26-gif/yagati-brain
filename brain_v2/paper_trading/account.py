"""
Paper Account Management

Manages the paper trading account state, including equity tracking
and statistics.
"""

from typing import Optional, Dict
from brain_v2.paper_trading.recorder import AirtableRecorder


class PaperAccount:
    """Manages paper trading account state"""
    
    def __init__(self, recorder: AirtableRecorder):
        """
        Initialize paper account manager.
        
        Args:
            recorder: AirtableRecorder instance
        """
        self.recorder = recorder
        self._account_cache = None
    
    def initialize(self, initial_capital: float = 100000.0) -> bool:
        """
        Initialize the account if it doesn't exist.
        
        Args:
            initial_capital: Starting capital (default: 100,000 USDT)
            
        Returns:
            True if initialized or already exists
        """
        try:
            # Check if account already exists
            account = self.recorder.get_account()
            if account:
                self._account_cache = account
                print(f"✅ Paper Trading: Account already exists with equity: {account['fields']['equity']:.2f} USDT")
                return True
            
            # Create new account
            print(f"📊 Paper Trading: Initializing account with {initial_capital:.2f} USDT")
            created = self.recorder.create_account(initial_capital)
            if created:
                self._account_cache = created
                print(f"✅ Paper Trading: Account created successfully")
                return True
            else:
                print(f"❌ Paper Trading: Failed to create account")
                return False
                
        except Exception as e:
            print(f"❌ Paper Trading: Error initializing account: {e}")
            return False
    
    def get_equity(self) -> float:
        """
        Get current equity.
        
        Returns:
            Current equity in USDT
        """
        try:
            account = self.recorder.get_account()
            if account:
                self._account_cache = account
                return float(account['fields']['equity'])
            return 0.0
        except Exception as e:
            print(f"⚠️ Paper Trading: Error getting equity: {e}")
            return 0.0
    
    def get_stats(self) -> Dict:
        """
        Get account statistics.
        
        Returns:
            Dictionary with account stats
        """
        try:
            account = self.recorder.get_account()
            if account:
                self._account_cache = account
                fields = account['fields']
                return {
                    "equity": float(fields.get('equity', 0)),
                    "initial_capital": float(fields.get('initial_capital', 0)),
                    "total_trades": int(fields.get('total_trades', 0)),
                    "winning_trades": int(fields.get('winning_trades', 0)),
                    "losing_trades": int(fields.get('losing_trades', 0)),
                }
            return {
                "equity": 0.0,
                "initial_capital": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
            }
        except Exception as e:
            print(f"⚠️ Paper Trading: Error getting stats: {e}")
            return {
                "equity": 0.0,
                "initial_capital": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
            }
    
    def update_equity(self, new_equity: float, is_win: bool) -> bool:
        """
        Update equity after a trade closes.
        
        Args:
            new_equity: New equity value
            is_win: True if the trade was a win
            
        Returns:
            True if updated successfully
        """
        try:
            account = self.recorder.get_account()
            if not account:
                print(f"⚠️ Paper Trading: No account found to update")
                return False
            
            record_id = account['id']
            fields = account['fields']
            
            # Update statistics
            total_trades = int(fields.get('total_trades', 0)) + 1
            winning_trades = int(fields.get('winning_trades', 0))
            losing_trades = int(fields.get('losing_trades', 0))
            
            if is_win:
                winning_trades += 1
            else:
                losing_trades += 1
            
            # Update account
            success = self.recorder.update_account(
                record_id,
                new_equity,
                total_trades,
                winning_trades,
                losing_trades
            )
            
            if success:
                print(f"✅ Paper Trading: Equity updated to {new_equity:.2f} USDT")
                print(f"   Stats: {total_trades} trades, {winning_trades} wins, {losing_trades} losses")
                return True
            else:
                print(f"❌ Paper Trading: Failed to update equity")
                return False
                
        except Exception as e:
            print(f"❌ Paper Trading: Error updating equity: {e}")
            return False
