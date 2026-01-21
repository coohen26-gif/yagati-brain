from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DayStrategyDecision:
    """Represents a decision-ready view of an evaluated day strategy."""
    strategy_id: str
    score: float
    label: str
    notes: Optional[str] = field(default=None)


@dataclass
class SwingStrategyDecision:
    """Represents a decision-ready view of an evaluated swing strategy."""
    strategy_id: str
    score: float
    label: str
    notes: Optional[str] = field(default=None)
