"""
Governance Logger Module

Explicit logging of all brain activity.
No silent errors - everything must be logged.
"""

from datetime import datetime, timezone
from typing import Optional


class GovernanceLogger:
    """
    Governance logger for Brain YAGATI v2.
    Logs all activities explicitly for auditability.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize governance logger.
        
        Args:
            verbose: Print logs to console
        """
        self.verbose = verbose
        self.logs = []
    
    def _log(self, level: str, message: str, context: Optional[dict] = None):
        """
        Internal logging method.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            context: Additional context
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "context": context or {}
        }
        self.logs.append(log_entry)
        
        if self.verbose:
            context_str = f" | {context}" if context else ""
            print(f"[{timestamp}] [{level}] {message}{context_str}")
    
    def info(self, message: str, context: Optional[dict] = None):
        """Log info message"""
        self._log("INFO", message, context)
    
    def warning(self, message: str, context: Optional[dict] = None):
        """Log warning message"""
        self._log("WARNING", message, context)
    
    def error(self, message: str, context: Optional[dict] = None):
        """Log error message - MUST NOT BE SILENT"""
        self._log("ERROR", message, context)
    
    def log_startup(self):
        """Log brain startup"""
        self.info("Brain YAGATI v2 starting up")
    
    def log_cycle_start(self, cycle_num: int):
        """Log analysis cycle start"""
        self.info(f"Analysis cycle {cycle_num} started")
    
    def log_cycle_end(self, cycle_num: int, stats: dict):
        """Log analysis cycle end"""
        self.info(f"Analysis cycle {cycle_num} completed", context=stats)
    
    def log_market_data_fetch(self, symbol: str, timeframe: str, success: bool):
        """Log market data fetch attempt"""
        if success:
            self.info(f"Market data fetched: {symbol} {timeframe}")
        else:
            self.error(f"Market data fetch failed: {symbol} {timeframe}")
    
    def log_decision(self, decision: dict):
        """Log a decision"""
        symbol = decision.get("symbol", "?")
        timeframe = decision.get("timeframe", "?")
        status = decision.get("status", "?")
        score = decision.get("score", 0)
        
        if status == "forming":
            self.info(
                f"Decision: FORMING - {symbol} {timeframe}",
                context={"score": score, "status": status}
            )
        else:
            self.info(
                f"Decision: REJECT - {symbol} {timeframe}",
                context={"score": score, "status": status}
            )
    
    def log_airtable_write(self, table: str, success: bool, details: str = ""):
        """Log Airtable write attempt"""
        if success:
            self.info(f"Airtable write successful: {table}", context={"details": details})
        else:
            self.error(f"Airtable write failed: {table}", context={"details": details})
    
    def log_error_explicit(self, error: Exception, context: str):
        """
        Explicitly log an error - NEVER SILENT.
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
        self.error(
            f"Error in {context}: {str(error)}",
            context={"error_type": type(error).__name__, "error_msg": str(error)}
        )
    
    def get_logs(self):
        """Get all logs"""
        return self.logs
    
    def clear_logs(self):
        """Clear logs"""
        self.logs = []


# Global logger instance
_logger = None


def get_logger() -> GovernanceLogger:
    """Get global logger instance"""
    global _logger
    if _logger is None:
        _logger = GovernanceLogger(verbose=True)
    return _logger
