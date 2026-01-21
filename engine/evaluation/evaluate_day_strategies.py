"""Evaluate day trading strategies.

This module provides a simple function to turn score breakdowns into
structured evaluation objects. It does not make any decisions or
trigger any actions.
"""
from typing import Dict, List

from .evaluation_models import DayStrategyEvaluation


def evaluate_day_strategies(score_breakdowns: List[Dict]) -> List[DayStrategyEvaluation]:
    """Convert raw score breakdowns into DayStrategyEvaluation objects.

    Args:
        score_breakdowns: A list of dictionaries with at least ``strategy_id`` and ``score`` keys.

    Returns:
        A list of DayStrategyEvaluation instances with simple labels based on score bands.
    """
    evaluations: List[DayStrategyEvaluation] = []
    for breakdown in score_breakdowns:
        strategy_id = breakdown.get("strategy_id")
        score = breakdown.get("score")
        # Determine a simple label based on score bands. Adjust bands as needed.
        if score is None:
            label = "unknown"
        elif score >= 70:
            label = "high"
        elif score >= 40:
            label = "medium"
        else:
            label = "low"
        evaluations.append(
            DayStrategyEvaluation(strategy_id=strategy_id, score=score, label=label)
        )
    return evaluations
