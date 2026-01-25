"""
Airtable Logger for Setups Forming (V1.1.3-01)

Writes detected market setups to a new Airtable table: setups_forming

Features:
- Deduplication: One setup per (symbol, timeframe, setup_type)
- State tracking: Only writes on new setup or confidence change
- Market context: Adds global market context (NORMAL/VOLATILE/PANIC)

Table Schema:
- symbol (text): Market symbol (e.g., "BTCUSDT")
- timeframe (text): Timeframe (e.g., "1h", "4h", "1d")
- setup_type (text): Type of setup (volatility_expansion, range_break_attempt, etc.)
- status (text): Setup status (always "FORMING" for now)
- confidence (text): Confidence level (LOW, MEDIUM, HIGH)
- detected_at (datetime): When the setup was detected
- context (text): Additional context about the setup
- market_context (text): Global market context (NORMAL, VOLATILE, PANIC)
"""

import os
import requests
from datetime import datetime, timezone


class SetupsAirtableLogger:
    """
    Airtable logger for market setups with deduplication and state tracking.
    """
    
    def __init__(self):
        """Initialize Airtable logger with environment variables."""
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = "setups_forming"
        self.configured = False
        
        # State cache: {(symbol, timeframe, setup_type): {record_id, confidence, last_updated}}
        self.state_cache = {}
        
        # Check configuration without blocking
        if not self.api_key or not self.base_id:
            return
        
        # Construct API URL
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        
        # Setup headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.configured = True
        
        # Load existing setups into cache
        self._load_existing_setups()
    
    def _load_existing_setups(self):
        """
        Load existing setups from Airtable into state cache.
        This enables deduplication and state change detection.
        """
        if not self.configured:
            return
        
        try:
            # Fetch all existing records with status FORMING
            # Using fixed status value to avoid injection
            params = {
                "filterByFormula": "{status} = 'FORMING'",
                "fields": ["symbol", "timeframe", "setup_type", "confidence", "detected_at"]
            }
            
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if 200 <= response.status_code < 300:
                data = response.json()
                records = data.get("records", [])
                
                for record in records:
                    record_id = record.get("id")
                    fields = record.get("fields", {})
                    
                    symbol = fields.get("symbol")
                    timeframe = fields.get("timeframe")
                    setup_type = fields.get("setup_type")
                    confidence = fields.get("confidence")
                    detected_at = fields.get("detected_at")
                    
                    # Only cache if all required fields are present
                    if symbol and timeframe and setup_type:
                        key = (symbol, timeframe, setup_type)
                        self.state_cache[key] = {
                            "record_id": record_id,
                            "confidence": confidence,
                            "detected_at": detected_at
                        }
                
                print(f"📋 Loaded {len(self.state_cache)} existing setups into cache")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load existing setups: {e}")
            # Continue without cache - will create new records
    
    def _should_write_setup(self, setup):
        """
        Determine if setup should be written to Airtable.
        Only writes on state changes (new setup or confidence change).
        
        Args:
            setup (dict): Setup to check
            
        Returns:
            tuple: (should_write: bool, record_id: str or None, action: str)
        """
        # Safely extract required fields
        symbol = setup.get("symbol")
        timeframe = setup.get("timeframe")
        setup_type = setup.get("setup_type")
        
        # Validate required fields are present
        if not all([symbol, timeframe, setup_type]):
            return (False, None, "INVALID")
        
        key = (symbol, timeframe, setup_type)
        
        # Check if setup exists in cache
        if key not in self.state_cache:
            return (True, None, "CREATE")
        
        # Setup exists - check if confidence changed
        cached = self.state_cache[key]
        current_confidence = setup.get("confidence")
        cached_confidence = cached.get("confidence")
        
        if current_confidence != cached_confidence:
            return (True, cached.get("record_id"), "UPDATE")
        
        # No change - skip write
        return (False, None, "SKIP")
    
    def _update_record(self, record_id, setup):
        """
        Update an existing Airtable record.
        
        Args:
            record_id (str): Airtable record ID
            setup (dict): Setup data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare update payload
            record = {
                "fields": {
                    "confidence": setup.get("confidence"),
                    "detected_at": setup.get("detected_at"),
                    "context": setup.get("context", ""),
                    "market_context": setup.get("market_context", "NORMAL")
                }
            }
            
            # Update record
            url = f"{self.api_url}/{record_id}"
            response = requests.patch(
                url,
                headers=self.headers,
                json=record,
                timeout=10
            )
            
            if 200 <= response.status_code < 300:
                symbol = setup.get("symbol", "?")
                timeframe = setup.get("timeframe", "?")
                setup_type = setup.get("setup_type", "?")
                confidence = setup.get("confidence", "?")
                print(f"🔄 Setup updated: {symbol} {timeframe} - {setup_type} (confidence: {confidence})")
                
                # Update cache - safely extract key components
                symbol_key = setup.get("symbol")
                timeframe_key = setup.get("timeframe")
                setup_type_key = setup.get("setup_type")
                
                if symbol_key and timeframe_key and setup_type_key:
                    key = (symbol_key, timeframe_key, setup_type_key)
                    self.state_cache[key]["confidence"] = setup.get("confidence")
                    self.state_cache[key]["detected_at"] = setup.get("detected_at")
                
                return True
            else:
                print(f"⚠️ Airtable update failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error updating record: {e}")
            return False
    
    def _create_record(self, setup):
        """
        Create a new Airtable record.
        
        Args:
            setup (dict): Setup data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare record
            record = {
                "fields": {
                    "symbol": setup.get("symbol"),
                    "timeframe": setup.get("timeframe"),
                    "setup_type": setup.get("setup_type"),
                    "status": setup.get("status", "FORMING"),
                    "confidence": setup.get("confidence"),
                    "detected_at": setup.get("detected_at"),
                    "context": setup.get("context", ""),
                    "market_context": setup.get("market_context", "NORMAL")
                }
            }
            
            # Send to Airtable
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=record,
                timeout=10
            )
            
            if 200 <= response.status_code < 300:
                symbol = setup.get("symbol", "?")
                timeframe = setup.get("timeframe", "?")
                setup_type = setup.get("setup_type", "?")
                confidence = setup.get("confidence", "?")
                print(f"✅ Setup logged: {symbol} {timeframe} - {setup_type} (confidence: {confidence})")
                
                # Add to cache - safely extract key components
                symbol_key = setup.get("symbol")
                timeframe_key = setup.get("timeframe")
                setup_type_key = setup.get("setup_type")
                
                if symbol_key and timeframe_key and setup_type_key:
                    key = (symbol_key, timeframe_key, setup_type_key)
                    record_data = response.json()
                    self.state_cache[key] = {
                        "record_id": record_data.get("id"),
                        "confidence": setup.get("confidence"),
                        "detected_at": setup.get("detected_at")
                    }
                
                return True
            else:
                print(f"⚠️ Airtable setup logging failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error logging setup to Airtable: {e}")
            return False
    
    def log_setup(self, setup):
        """
        Log a single setup to Airtable.
        Uses deduplication and only writes on state changes.
        
        Args:
            setup (dict): Setup dictionary with keys:
                - symbol
                - timeframe
                - setup_type
                - status
                - confidence
                - detected_at
                - context
                - market_context
                
        Returns:
            bool: True if written/updated, False if skipped or failed
        """
        # Skip if not configured
        if not self.configured:
            return False
        
        # Check if we should write this setup
        should_write, record_id, action = self._should_write_setup(setup)
        
        if not should_write:
            # Skip - no state change
            return False
        
        if action == "CREATE":
            return self._create_record(setup)
        elif action == "UPDATE":
            return self._update_record(record_id, setup)
        
        return False
    
    def log_setups_batch(self, setups):
        """
        Log multiple setups to Airtable.
        Only writes setups with state changes (new or confidence change).
        
        Args:
            setups (list): List of setup dictionaries
            
        Returns:
            dict: Statistics {created: int, updated: int, skipped: int}
        """
        stats = {"created": 0, "updated": 0, "skipped": 0}
        
        for setup in setups:
            should_write, record_id, action = self._should_write_setup(setup)
            
            if not should_write:
                stats["skipped"] += 1
                continue
            
            if action == "CREATE":
                if self._create_record(setup):
                    stats["created"] += 1
            elif action == "UPDATE":
                if self._update_record(record_id, setup):
                    stats["updated"] += 1
        
        return stats


def log_setups_to_airtable(setups):
    """
    Convenience function to log setups to Airtable.
    Uses deduplication and only writes on state changes.
    Fails gracefully if Airtable is not configured.
    
    Args:
        setups (list): List of setup dictionaries
        
    Returns:
        dict: Statistics {created: int, updated: int, skipped: int}
    """
    try:
        logger = SetupsAirtableLogger()
        
        if not logger.configured:
            print("⚠️ Airtable not configured - setup logging skipped")
            return {"created": 0, "updated": 0, "skipped": 0}
        
        if not setups:
            print("ℹ️ No setups to log")
            return {"created": 0, "updated": 0, "skipped": 0}
        
        stats = logger.log_setups_batch(setups)
        
        # Print summary
        total_written = stats["created"] + stats["updated"]
        if total_written > 0:
            print(f"✅ Written {total_written} setups: {stats['created']} new, {stats['updated']} updated, {stats['skipped']} skipped")
        else:
            print(f"ℹ️ No state changes detected - {stats['skipped']} setups skipped")
        
        return stats
        
    except Exception as e:
        print(f"⚠️ Setup logging failed (non-blocking): {e}")
        return {"created": 0, "updated": 0, "skipped": 0}


if __name__ == "__main__":
    """
    Test the setups logger.
    """
    print("=" * 50)
    print("Setups Airtable Logger Test")
    print("=" * 50)
    
    # Test with a sample setup
    test_setup = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "setup_type": "volatility_expansion",
        "status": "FORMING",
        "confidence": "HIGH",
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "context": "test setup - current_vol=5.0% vs avg=2.0%",
        "market_context": "VOLATILE"
    }
    
    result = log_setups_to_airtable([test_setup])
    
    if result["created"] > 0 or result["updated"] > 0:
        print("\n✅ Test successful! Check your Airtable base:")
        print(f"  https://airtable.com/{os.getenv('AIRTABLE_BASE_ID')}")
        print("\nLook for new/updated record in 'setups_forming' table")
    else:
        print("\n❌ Test failed - check configuration and table setup")
