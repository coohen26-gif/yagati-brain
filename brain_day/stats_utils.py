"""
Statistics utilities for trade analysis.

This module provides pure, deterministic helper functions for computing
trade statistics (count, win/loss counts, win rate, average R:R).
"""

from typing import Any, Dict, List


def count_trades(trades: List[Any]) -> int:
    """
    Count the total number of trades.
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Total count of trades
    """
    return len(trades) if trades else 0


def win_loss_counts(trades: List[Any]) -> Dict[str, int]:
    """
    Count wins and losses from a list of trades.
    
    A trade is considered a win if it has a positive realized_r or final_result_percent.
    A trade is considered a loss if it has a negative or zero realized_r or final_result_percent.
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Dictionary with 'wins' and 'losses' counts
    """
    wins = 0
    losses = 0
    
    if not trades:
        return {"wins": 0, "losses": 0}
    
    for trade in trades:
        # Try to get realized_r first (from dict or attribute)
        rr = None
        if isinstance(trade, dict):
            rr = trade.get("realized_r")
            if rr is None:
                rr = trade.get("rr")
            if rr is None:
                rr = trade.get("final_result_percent")
        else:
            rr = getattr(trade, "realized_r", None)
            if rr is None:
                rr = getattr(trade, "rr", None)
            if rr is None:
                rr = getattr(trade, "final_result_percent", None)
        
        if rr is None:
            continue
            
        if rr > 0:
            wins += 1
        else:
            losses += 1
    
    return {"wins": wins, "losses": losses}


def win_rate(trades: List[Any]) -> float:
    """
    Calculate win rate as a fraction.
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Win rate as a float between 0.0 and 1.0 (not percentage)
    """
    if not trades:
        return 0.0
    
    wl = win_loss_counts(trades)
    wins = wl["wins"]
    losses = wl["losses"]
    total = wins + losses
    
    if total == 0:
        return 0.0
    
    return wins / total


def avg_rr(trades: List[Any]) -> float:
    """
    Calculate average R:R (Risk-Reward ratio) from a list of trades.
    
    Args:
        trades: List of trade objects (dict or object with attributes)
        
    Returns:
        Average R:R as a float
    """
    if not trades:
        return 0.0
    
    total_rr = 0.0
    count = 0
    
    for trade in trades:
        # Try to get realized_r first (from dict or attribute)
        rr = None
        if isinstance(trade, dict):
            rr = trade.get("realized_r")
            if rr is None:
                rr = trade.get("rr")
            if rr is None:
                rr = trade.get("final_result_percent")
        else:
            rr = getattr(trade, "realized_r", None)
            if rr is None:
                rr = getattr(trade, "rr", None)
            if rr is None:
                rr = getattr(trade, "final_result_percent", None)
        
        if rr is not None:
            total_rr += rr
            count += 1
    
    if count == 0:
        return 0.0
    
    return total_rr / count
