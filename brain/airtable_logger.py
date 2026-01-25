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


def log_brain_scan(symbol, note="market scanned"):
    """
    Log a scan event when the brain reads market data.
    
    Uses the existing log_heartbeat() infrastructure to write to the brain_logs table.
    Fails gracefully if Airtable is not configured, following the same pattern as log_brain_heartbeat().
    
    Args:
        symbol (str): Market symbol being scanned (e.g., "BTCUSDT", "BTC", "GLOBAL")
        note (str): Short factual text describing the scan (default: "market scanned")
        
    Returns:
        bool: True if successful, False otherwise (including when Airtable is not configured)
    """
    try:
        logger = AirtableLogger()
        if not logger.configured:
            return False
        return logger.log_heartbeat(
            cycle_type="scan",
            context=symbol,
            status="ok",
            note=note
        )
    except Exception as e:
        print(f"⚠️ Scan event failed (non-blocking): {e}")
        return False


def log_brain_observation(symbol, status="weak", note="pattern detected"):
    """
    Log an observation event for weak/preliminary patterns.
    
    Uses the existing log_heartbeat() infrastructure to write to the brain_logs table.
    Fails gracefully if Airtable is not configured, following the same pattern as log_brain_heartbeat().
    
    Args:
        symbol (str): Market symbol where observation was made
        status (str): Status of the observation ("weak" or "neutral")
        note (str): Short descriptive label (e.g., "RSI divergence", "EMA crossover detected")
        
    Returns:
        bool: True if successful, False otherwise (including when Airtable is not configured)
    """
    try:
        logger = AirtableLogger()
        if not logger.configured:
            return False
        return logger.log_heartbeat(
            cycle_type="observation",
            context=symbol,
            status=status,
            note=note
        )
    except Exception as e:
        print(f"⚠️ Observation event failed (non-blocking): {e}")
        return False
