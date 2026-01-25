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
        # Skip if not configured
        if not self.configured:
            return False
            
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
            
            if 200 <= response.status_code < 300:
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
    Fails gracefully if Airtable is not configured.
    """
    try:
        logger = AirtableLogger()
        if not logger.configured:
            print("⚠️ Airtable not configured - heartbeat skipped")
            return False
        return logger.log_heartbeat(
            cycle_type="heartbeat",
            context="GLOBAL",
            status="ok",
            note="initial brain heartbeat"
        )
    except Exception as e:
        print(f"⚠️ Airtable heartbeat failed (non-blocking): {e}")
        return False


def log_brain_scan(symbol, note=None):
    """
    Convenience function to log a market scan event.
    
    Args:
        symbol (str): Market symbol being scanned (e.g. "BTCUSDT")
        note (str, optional): Additional note (default: "market scanned")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger = AirtableLogger()
        if not logger.configured:
            print("⚠️ Airtable not configured - scan skipped")
            return False
        return logger.log_heartbeat(
            cycle_type="scan",
            context=symbol,
            status="ok",
            note=note or "market scanned"
        )
    except Exception as e:
        print(f"⚠️ Airtable scan failed (non-blocking): {e}")
        return False


def log_brain_observation(symbol, status, note):
    """
    Convenience function to log a market observation event.
    
    Args:
        symbol (str): Market symbol being observed (e.g. "BTCUSDT")
        status (str): Observation status ("weak" or "neutral")
        note (str): Descriptive label (e.g. "RSI divergence", "regime transition detected")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger = AirtableLogger()
        if not logger.configured:
            print("⚠️ Airtable not configured - observation skipped")
            return False
        return logger.log_heartbeat(
            cycle_type="observation",
            context=symbol,
            status=status,
            note=note
        )
    except Exception as e:
        print(f"⚠️ Airtable observation failed (non-blocking): {e}")
        return False
