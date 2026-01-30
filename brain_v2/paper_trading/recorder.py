"""
Airtable Recorder Module

Handles all Airtable read/write operations for paper trading.
Manages paper_account, paper_open_trades, and paper_closed_trades tables.
"""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from brain_v2.config.settings import AIRTABLE_API_KEY, AIRTABLE_BASE_ID


# Table names
TABLE_PAPER_ACCOUNT = "paper_account"
TABLE_PAPER_OPEN_TRADES = "paper_open_trades"
TABLE_PAPER_CLOSED_TRADES = "paper_closed_trades"
TABLE_SETUPS_FORMING = "setups_forming"


class AirtableRecorder:
    """Manages Airtable read/write operations for paper trading"""
    
    def __init__(self):
        """Initialize Airtable recorder"""
        self.api_key = AIRTABLE_API_KEY
        self.base_id = AIRTABLE_BASE_ID
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        
        # Normalize token: strip whitespace and remove all existing "Bearer " prefixes
        token = self.api_key.strip()
        while token.lower().startswith("bearer "):
            token = token[len("bearer "):].strip()
        
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _write_record(self, table_name: str, fields: Dict) -> Optional[Dict]:
        """
        Write a single record to Airtable.
        
        Args:
            table_name: Table name
            fields: Record fields
            
        Returns:
            Created record with ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{table_name}"
            payload = {"fields": fields}
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if 200 <= response.status_code < 300:
                return response.json()
            else:
                print(f"⚠️ Paper Trading: Airtable write failed ({table_name}): {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ Paper Trading: Airtable write error ({table_name}): {e}")
            return None
    
    def _update_record(self, table_name: str, record_id: str, fields: Dict) -> bool:
        """
        Update a record in Airtable.
        
        Args:
            table_name: Table name
            record_id: Record ID to update
            fields: Fields to update
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/{table_name}/{record_id}"
            payload = {"fields": fields}
            
            response = requests.patch(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            return 200 <= response.status_code < 300
                
        except Exception as e:
            print(f"⚠️ Paper Trading: Airtable update error ({table_name}): {e}")
            return False
    
    def _read_records(self, table_name: str, filter_formula: Optional[str] = None) -> List[Dict]:
        """
        Read records from Airtable.
        
        Args:
            table_name: Table name
            filter_formula: Optional Airtable filter formula
            
        Returns:
            List of records
        """
        try:
            url = f"{self.base_url}/{table_name}"
            params = {}
            if filter_formula:
                params["filterByFormula"] = filter_formula
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if 200 <= response.status_code < 300:
                data = response.json()
                return data.get("records", [])
            else:
                print(f"⚠️ Paper Trading: Airtable read failed ({table_name}): {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️ Paper Trading: Airtable read error ({table_name}): {e}")
            return []
    
    def _delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from Airtable.
        
        Args:
            table_name: Table name
            record_id: Record ID to delete
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.base_url}/{table_name}/{record_id}"
            
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=10
            )
            
            return 200 <= response.status_code < 300
                
        except Exception as e:
            print(f"⚠️ Paper Trading: Airtable delete error ({table_name}): {e}")
            return False
    
    # Account operations
    def get_account(self) -> Optional[Dict]:
        """Get paper account record"""
        records = self._read_records(TABLE_PAPER_ACCOUNT)
        if records:
            return records[0]  # Should only be one account record
        return None
    
    def create_account(self, initial_capital: float) -> Optional[Dict]:
        """Create paper account record"""
        fields = {
            "equity": initial_capital,
            "initial_capital": initial_capital,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        return self._write_record(TABLE_PAPER_ACCOUNT, fields)
    
    def update_account(self, record_id: str, equity: float, total_trades: int, 
                      winning_trades: int, losing_trades: int) -> bool:
        """Update paper account record"""
        fields = {
            "equity": equity,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        return self._update_record(TABLE_PAPER_ACCOUNT, record_id, fields)
    
    # Trade operations
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        return self._read_records(TABLE_PAPER_OPEN_TRADES)
    
    def save_open_trade(self, trade_data: Dict) -> Optional[Dict]:
        """Save a new open trade"""
        fields = {
            "symbol": trade_data["symbol"],
            "direction": trade_data["direction"],
            "entry_price": trade_data["entry_price"],
            "position_size": trade_data["position_size"],
            "stop_loss": trade_data["stop_loss"],
            "take_profit": trade_data["take_profit"],
            "risk_amount": trade_data["risk_amount"],
            "equity_at_open": trade_data["equity_at_open"],
            "opened_at": trade_data["opened_at"],
            "setup_id": trade_data.get("setup_id", ""),
            # Water marks for MFE/MAE tracking
            "high_water_mark_price": trade_data.get("high_water_mark_price", trade_data["entry_price"]),
            "low_water_mark_price": trade_data.get("low_water_mark_price", trade_data["entry_price"]),
            # Contextual snapshot at entry
            "entry_context_volatility": trade_data.get("entry_context_volatility"),
            "entry_context_trend": trade_data.get("entry_context_trend"),
            "entry_context_rsi": trade_data.get("entry_context_rsi"),
            "entry_market_regime": trade_data.get("entry_market_regime"),
            "entry_snapshot_version": trade_data.get("entry_snapshot_version", "v1.0"),
        }
        return self._write_record(TABLE_PAPER_OPEN_TRADES, fields)
    
    def delete_open_trade(self, record_id: str) -> bool:
        """Delete an open trade (after closing)"""
        return self._delete_record(TABLE_PAPER_OPEN_TRADES, record_id)
    
    def update_water_marks(self, record_id: str, high_water_mark: float, low_water_mark: float) -> bool:
        """
        Update water marks for an open trade.
        
        Args:
            record_id: Record ID to update
            high_water_mark: High water mark price
            low_water_mark: Low water mark price
            
        Returns:
            True if successful
        """
        fields = {
            "high_water_mark_price": high_water_mark,
            "low_water_mark_price": low_water_mark,
        }
        return self._update_record(TABLE_PAPER_OPEN_TRADES, record_id, fields)
    
    def save_closed_trade(self, trade_data: Dict) -> Optional[Dict]:
        """Save a closed trade to history"""
        fields = {
            # Identity block
            "symbol": trade_data["symbol"],
            "direction": trade_data["direction"],
            "timeframe": trade_data.get("timeframe", ""),
            "opened_at": trade_data["opened_at"],
            "closed_at": trade_data["closed_at"],
            "duration_minutes": trade_data.get("duration_minutes", 0),
            # Performance block
            "entry_price": trade_data["entry_price"],
            "exit_price": trade_data["exit_price"],
            "position_size": trade_data["position_size"],
            "stop_loss": trade_data["stop_loss"],
            "take_profit": trade_data["take_profit"],
            "risk_amount": trade_data["risk_amount"],
            "equity_at_open": trade_data["equity_at_open"],
            "pnl": trade_data["pnl"],
            "pnl_percent": trade_data["pnl_percent"],
            "pnl_usdt": trade_data.get("pnl_usdt", trade_data["pnl"]),  # Alias for clarity in Airtable UI
            "mfe_percent": trade_data.get("mfe_percent", 0),
            "mae_percent": trade_data.get("mae_percent", 0),
            "exit_reason": trade_data["exit_reason"],
            "setup_id": trade_data.get("setup_id", ""),
            # Contextual snapshot block (copied from entry)
            "entry_context_volatility": trade_data.get("entry_context_volatility"),
            "entry_context_trend": trade_data.get("entry_context_trend"),
            "entry_context_rsi": trade_data.get("entry_context_rsi"),
            "entry_market_regime": trade_data.get("entry_market_regime"),
            "entry_snapshot_version": trade_data.get("entry_snapshot_version", "v1.0"),
        }
        return self._write_record(TABLE_PAPER_CLOSED_TRADES, fields)
    
    # Setup reading
    def get_forming_setups(self) -> List[Dict]:
        """Get forming setups from setups_forming table"""
        # Read all forming setups
        records = self._read_records(TABLE_SETUPS_FORMING)
        return records
