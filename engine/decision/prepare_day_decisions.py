from typing import List
from engine.evaluation.evaluation_models import DayStrategyEvaluation
from .decision_models import DayStrategyDecision


def prepare_day_decisions(evaluations: List[DayStrategyEvaluation]) -> List[DayStrategyDecision]:
    """
    Convert evaluated day strategies into decision-ready objects.

    This function takes a list of DayStrategyEvaluation objects and returns a list
    of DayStrategyDecision objects containing the same basic information plus a
    human-readable note. No automated decisions are made here.
    """
    decisions: List[DayStrategyDecision] = []
    for eval_obj in evaluations:
        note = (
            f"Strategy {eval_obj.strategy_id} has label '{eval_obj.label}' "
            f"with a score of {eval_obj.score:.2f}."
        )
        decision = DayStrategyDecision(
            strategy_id=eval_obj.strategy_id,
            score=eval_obj.score,
            label=eval_obj.label,
            notes=note,
        )
        decisions.append(decision)
    return decisions
