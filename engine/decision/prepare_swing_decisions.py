from typing import List
from engine.evaluation.evaluation_models import SwingStrategyEvaluation
from .decision_models import SwingStrategyDecision


def prepare_swing_decisions(evaluations: List[SwingStrategyEvaluation]) -> List[SwingStrategyDecision]:
    """
    Convert evaluated swing strategies into decision-ready objects.

    Args:
        evaluations: List[SwingStrategyEvaluation] – evaluated swing strategies.

    Returns:
        List[SwingStrategyDecision]: Decision-ready representations for human interpretation.
    """
    decisions: List[SwingStrategyDecision] = []
    for eval_obj in evaluations:
        # Compose a simple note summarizing the evaluation for readability.
        note = (
            f"Strategy {eval_obj.strategy_id} has label '{eval_obj.label}' "
            f"with a score of {eval_obj.score:.2f}."
        )
        decision = SwingStrategyDecision(
            strategy_id=eval_obj.strategy_id,
            score=eval_obj.score,
            label=eval_obj.label,
            notes=note,
        )
        decisions.append(decision)
    return decisions
