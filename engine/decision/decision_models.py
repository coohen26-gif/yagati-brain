from dataclasses import dataclass, field
from typing import Optional

@dataclass
class StrategyDecision:
    """
    Represents a decision-ready view of an evaluated strategy. This dataclass contains
    the minimal set of fields needed for human interpretation. It does not trigger any
    automated trading actions.
    """
    strategy_id: str
    score: float
    label: str
    notes: Optional[str] = field(default=None)
