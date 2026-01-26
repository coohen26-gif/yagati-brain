"""
Airtable Writer Module

Writes to Airtable tables:
- brain_logs: Startup, cycles, decisions
- setups_forming: Detected setups (only if forming)
"""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional
from brain_v2.config.settings import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    TABLE_BRAIN_LOGS,
    TABLE_SETUPS_FORMING,
)


class AirtableWriter:
    """Write to Airtable tables"""
    
    def __init__(self):
        """Initialize Airtable writer"""
        self.api_key = AIRTABLE_API_KEY
        self.base_id = AIRTABLE_BASE_ID
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _write_record(self, table_name: str, fields: Dict) -> bool:
        """
        Write a single record to Airtable.
        
        Args:
            table_name: Table name
            fields: Record fields
            
        Returns:
            True if successful, False otherwise
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
                return True
            else:
                print(f"⚠️ Airtable write failed ({table_name}): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Airtable write error ({table_name}): {e}")
            return False
    
    def write_brain_log(
        self,
        cycle_type: str,
        context: str,
        status: str,
        note: Optional[str] = None
    ) -> bool:
        """
        Write to brain_logs table.
        
        Args:
            cycle_type: Type of cycle (heartbeat, scan, decision)
            context: Context (GLOBAL, symbol, etc.)
            status: Status (ok, error, etc.)
            note: Optional note
            
        Returns:
            True if successful
        """
        fields = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_type": cycle_type,
            "context": context,
            "status": status,
        }
        
        if note:
            fields["note"] = note
        
        return self._write_record(TABLE_BRAIN_LOGS, fields)
    
    def write_startup_log(self) -> bool:
        """
        Write startup heartbeat to brain_logs.
        
        Returns:
            True if successful
        """
        return self.write_brain_log(
            cycle_type="heartbeat",
            context="GLOBAL",
            status="ok",
            note="Brain YAGATI v2 startup"
        )
    
    def write_cycle_log(self, cycle_num: int, stats: Dict) -> bool:
        """
        Write analysis cycle log.
        
        Args:
            cycle_num: Cycle number
            stats: Cycle statistics
            
        Returns:
            True if successful
        """
        note = f"Cycle {cycle_num}: {stats.get('symbols_analyzed', 0)} symbols, " \
               f"{stats.get('setups_detected', 0)} setups, " \
               f"{stats.get('decisions_forming', 0)} forming, " \
               f"{stats.get('decisions_rejected', 0)} rejected"
        
        return self.write_brain_log(
            cycle_type="scan",
            context="GLOBAL",
            status="ok",
            note=note
        )
    
    def write_decision_log(self, decision: Dict) -> bool:
        """
        Write decision log to brain_logs.
        
        Args:
            decision: Decision dictionary
            
        Returns:
            True if successful
        """
        symbol = decision.get("symbol", "?")
        timeframe = decision.get("timeframe", "?")
        status = decision.get("status", "?")
        score = decision.get("score", 0)
        justification = decision.get("justification", "")
        
        context = f"{symbol}_{timeframe}"
        note = f"{status.upper()} (score: {score}) - {justification}"
        
        return self.write_brain_log(
            cycle_type="decision",
            context=context,
            status=status,
            note=note
        )
    
    def write_setup_forming(self, decision: Dict) -> bool:
        """
        Write forming setup to setups_forming table.
        
        Only writes if status is "forming".
        
        Args:
            decision: Decision dictionary
            
        Returns:
            True if successful
        """
        # Only write if forming
        if decision.get("status") != "forming":
            return False
        
        fields = {
            "symbol": decision.get("symbol"),
            "timeframe": decision.get("timeframe"),
            "setup_type": decision.get("setup_type"),
            "status": "FORMING",
            "confidence": decision.get("confidence"),
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "context": decision.get("justification", ""),
            "market_context": "NORMAL",  # Can be enhanced later
        }
        
        return self._write_record(TABLE_SETUPS_FORMING, fields)
    
    def write_error_log(self, error_msg: str, context: str) -> bool:
        """
        Write error log to brain_logs.
        
        Args:
            error_msg: Error message
            context: Error context
            
        Returns:
            True if successful
        """
        return self.write_brain_log(
            cycle_type="error",
            context=context,
            status="error",
            note=error_msg
        )


def write_startup() -> bool:
    """Write startup log to Airtable"""
    try:
        writer = AirtableWriter()
        return writer.write_startup_log()
    except Exception as e:
        print(f"⚠️ Failed to write startup log: {e}")
        return False


def write_cycle(cycle_num: int, stats: Dict) -> bool:
    """Write cycle log to Airtable"""
    try:
        writer = AirtableWriter()
        return writer.write_cycle_log(cycle_num, stats)
    except Exception as e:
        print(f"⚠️ Failed to write cycle log: {e}")
        return False


def write_decisions(decisions: List[Dict]) -> Dict[str, int]:
    """
    Write decisions to Airtable.
    
    Args:
        decisions: List of decisions
        
    Returns:
        Stats: {logged: count, forming: count}
    """
    writer = AirtableWriter()
    stats = {"logged": 0, "forming": 0}
    
    for decision in decisions:
        try:
            # Write decision log
            if writer.write_decision_log(decision):
                stats["logged"] += 1
            
            # Write setup_forming if forming
            if decision.get("status") == "forming":
                if writer.write_setup_forming(decision):
                    stats["forming"] += 1
        except Exception as e:
            print(f"⚠️ Failed to write decision: {e}")
    
    return stats
