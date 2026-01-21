from dataclasses import dataclass


@dataclass
class DayStrategyEvaluation:
    """Represents an evaluated day strategy."""
    strategy_id: str
    score: float
    label: str


@dataclass
class SwingStrategyEvaluation:
    """Represents an evaluated swing strategy."""
    strategy_id: str
    score: float
    label: str
