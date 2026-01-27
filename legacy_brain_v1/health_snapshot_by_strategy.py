"""
Health snapshot utilities grouped by strategy.

This module provides helpers to compute health snapshots per strategy,
building on the base health_snapshot utilities. It contains no business rules,
thresholds, or decision logic.
"""

from typing import Any, Dict, List

from .health_snapshot import compute_health_snapshot

__all__ = ["compute_health_snapshot_by_strategy"]


def compute_health_snapshot_by_strategy(trades: List[Any]) -> Dict[str, Any]:
    """
    Compute health snapshots grouped by strategy_id.
    
    Args:
        trades: List of trade objects, each potentially having a 'strategy_id' field
        
    Returns:
        Dictionary mapping strategy_id to health snapshot
    """
    if not trades:
        return {}
    
    # Group trades by strategy_id
    by_strategy: Dict[str, List[Any]] = {}
    
    for trade in trades:
        if isinstance(trade, dict):
            strategy_id = trade.get("strategy_id")
            if strategy_id:
                if strategy_id not in by_strategy:
                    by_strategy[strategy_id] = []
                by_strategy[strategy_id].append(trade)
    
    # Compute snapshot for each strategy
    result = {}
    for strategy_id, strategy_trades in by_strategy.items():
        result[strategy_id] = compute_health_snapshot(strategy_trades)
    
    return result
