from typing import List, Dict
from .decision_models import DecisionModel


def prepare_swing_decisions(evaluated_strategies: List[Dict]) -> List[DecisionModel]:
    """Prepare decision objects from evaluated swing strategies.

    Args:
        evaluated_strategies (List[Dict]): List of evaluated strategy dictionaries.
            Each dictionary should contain keys like 'strategy_id', 'score', 'label', and optionally 'notes'.

    Returns:
        List[DecisionModel]: List of DecisionModel instances capturing the evaluation details.

    This function does not enforce any thresholds or take actions. It simply
    structures the evaluated strategy data into DecisionModel instances for
    human interpretation.
    """
    decisions: List[DecisionModel] = []
    for strategy in evaluated_strategies:
        strategy_id = strategy.get("strategy_id")
        score = strategy.get("score")
        label = strategy.get("label", "")
        notes = strategy.get("notes")
        decisions.append(DecisionModel(strategy_id=strategy_id, score=score, label=label, notes=notes))
    return decisions
