"""
Statistical utilities for trade analysis.

This module provides pure, deterministic helpers for computing
basic statistics from trade data.
"""

from typing import Any, Dict, List


def count_trades(trades: List[Any]) -> int:
    """
    Count the total number of trades.
    
    Args:
        trades: List of trade objects
        
    Returns:
        Total count of trades
    """
    return len(trades) if trades else 0


def win_loss_counts(trades: List[Any]) -> Dict[str, int]:
    """
    Count wins and losses from trades.
    
    Args:
        trades: List of trade objects with outcome or result information
        
    Returns:
        Dictionary with 'wins' and 'losses' counts
    """
    wins = 0
    losses = 0
    
    for trade in trades:
        # Check for various result field names
        result = None
        if isinstance(trade, dict):
            # Use explicit None checks to handle 0 values correctly
            if "final_result_percent" in trade:
                result = trade["final_result_percent"]
            elif "result" in trade:
                result = trade["result"]
            elif "rr" in trade:
                result = trade["rr"]
        
        if result is not None:
            if result > 0:
                wins += 1
            elif result < 0:
                losses += 1
            # result == 0 is breakeven, not counted as win or loss
    
    return {"wins": wins, "losses": losses}


def win_rate(trades: List[Any]) -> float:
    """
    Calculate win rate as a percentage.
    
    Args:
        trades: List of trade objects
        
    Returns:
        Win rate as a float (0.0 to 100.0)
    """
    if not trades:
        return 0.0
    
    wl = win_loss_counts(trades)
    total = wl["wins"] + wl["losses"]
    
    if total == 0:
        return 0.0
    
    return (wl["wins"] / total) * 100.0


def avg_rr(trades: List[Any]) -> float:
    """
    Calculate average risk-reward ratio.
    
    Args:
        trades: List of trade objects with rr field
        
    Returns:
        Average RR as a float
    """
    if not trades:
        return 0.0
    
    rr_values = []
    
    for trade in trades:
        if isinstance(trade, dict):
            rr = trade.get("rr")
            if rr is not None:
                rr_values.append(float(rr))
    
    if not rr_values:
        return 0.0
    
    return sum(rr_values) / len(rr_values)
