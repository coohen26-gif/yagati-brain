"""
Airtable Logger for Setups Forming (V1.1.3-01)

Writes detected market setups to a new Airtable table: setups_forming

Table Schema:
- symbol (text): Market symbol (e.g., "BTCUSDT")
- timeframe (text): Timeframe (e.g., "1h", "4h", "1d")
- setup_type (text): Type of setup (volatility_expansion, range_break_attempt, etc.)
- status (text): Setup status (always "FORMING" for now)
- confidence (text): Confidence level (LOW, MEDIUM, HIGH)
- detected_at (datetime): When the setup was detected
- context (text): Additional context about the setup
"""

import os
import requests
from datetime import datetime, timezone


class SetupsAirtableLogger:
    """
    Airtable logger for market setups.
    """
    
    def __init__(self):
        """Initialize Airtable logger with environment variables."""
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = "setups_forming"
        self.configured = False
        
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
    
    def log_setup(self, setup):
        """
        Log a single setup to Airtable.
        
        Args:
            setup (dict): Setup dictionary with keys:
                - symbol
                - timeframe
                - setup_type
                - status
                - confidence
                - detected_at
                - context
                
        Returns:
            bool: True if successful, False otherwise
        """
        # Skip if not configured
        if not self.configured:
            return False
            
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
                    "context": setup.get("context", "")
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
                print(f"✅ Setup logged: {setup['symbol']} {setup['timeframe']} - {setup['setup_type']}")
                return True
            else:
                print(f"⚠️ Airtable setup logging failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error logging setup to Airtable: {e}")
            return False
    
    def log_setups_batch(self, setups):
        """
        Log multiple setups to Airtable.
        
        Args:
            setups (list): List of setup dictionaries
            
        Returns:
            int: Number of successfully logged setups
        """
        success_count = 0
        
        for setup in setups:
            if self.log_setup(setup):
                success_count += 1
        
        return success_count


def log_setups_to_airtable(setups):
    """
    Convenience function to log setups to Airtable.
    Fails gracefully if Airtable is not configured.
    
    Args:
        setups (list): List of setup dictionaries
        
    Returns:
        int: Number of successfully logged setups
    """
    try:
        logger = SetupsAirtableLogger()
        
        if not logger.configured:
            print("⚠️ Airtable not configured - setup logging skipped")
            return 0
        
        if not setups:
            print("ℹ️ No setups to log")
            return 0
        
        success_count = logger.log_setups_batch(setups)
        print(f"✅ Logged {success_count}/{len(setups)} setups to Airtable")
        
        return success_count
        
    except Exception as e:
        print(f"⚠️ Setup logging failed (non-blocking): {e}")
        return 0


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
        "context": "test setup - current_vol=5.0% vs avg=2.0%"
    }
    
    result = log_setups_to_airtable([test_setup])
    
    if result > 0:
        print("\n✅ Test successful! Check your Airtable base:")
        print(f"  https://airtable.com/{os.getenv('AIRTABLE_BASE_ID')}")
        print("\nLook for new record in 'setups_forming' table")
    else:
        print("\n❌ Test failed - check configuration and table setup")
