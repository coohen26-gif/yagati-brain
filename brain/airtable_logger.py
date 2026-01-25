"""
Airtable Logger for YAGATI Brain
Minimal integration to log brain heartbeat traces to Airtable.
"""

import os
import requests
from datetime import datetime, timezone


class AirtableLogger:
    """
    Simple Airtable logger for brain activity traces.
    Uses environment variables for configuration.
    """
    
    def __init__(self):
        """Initialize Airtable logger with environment variables."""
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = "brain_logs"
        
        # Validate configuration
        if not self.api_key:
            raise RuntimeError("AIRTABLE_API_KEY environment variable is required")
        if not self.base_id:
            raise RuntimeError("AIRTABLE_BASE_ID environment variable is required")
        
        # Construct API URL
        self.api_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        
        # Setup headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def log_heartbeat(self, cycle_type="heartbeat", context="GLOBAL", status="ok", note=None):
        """
        Log a heartbeat record to Airtable.
        
        Args:
            cycle_type (str): Type of cycle (default: "heartbeat")
            context (str): Context of the activity (default: "GLOBAL")
            status (str): Status of the activity (default: "ok")
            note (str, optional): Additional note
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare record with current timestamp
            timestamp = datetime.now(timezone.utc).isoformat()
            
            record = {
                "fields": {
                    "timestamp": timestamp,
                    "cycle_type": cycle_type,
                    "context": context,
                    "status": status
                }
            }
            
            # Add note if provided
            if note:
                record["fields"]["note"] = note
            
            # Send to Airtable
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=record,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Brain heartbeat logged to Airtable: {timestamp}")
                return True
            else:
                print(f"⚠️ Airtable logging failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error logging to Airtable: {e}")
            return False


def log_brain_heartbeat():
    """
    Convenience function to log the canonical YAGATI-BRAIN-001 heartbeat.
    This is the minimal trace that confirms brain execution.
    """
    try:
        logger = AirtableLogger()
        return logger.log_heartbeat(
            cycle_type="heartbeat",
            context="GLOBAL",
            status="ok",
            note="initial brain heartbeat"
        )
    except Exception as e:
        print(f"⚠️ Airtable logger not configured or unavailable: {e}")
        return False
