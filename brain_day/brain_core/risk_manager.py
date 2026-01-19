from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RiskLimits:
    max_open_positions_total: int = 1
    max_open_positions_per_symbol: int = 1
    max_same_direction_positions: int = 1
    allow_trade_when_observation: bool = False


class RiskManager:
    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()

    def can_open_new_position(
        self,
        symbol: str,
        direction: str,
        open_positions_total: int,
        open_positions_by_symbol: Dict[str, int],
        open_positions_by_direction: Dict[str, int],
        brain_decision: str,
    ) -> (bool, str):

        if brain_decision == "OBSERVATION" and not self.limits.allow_trade_when_observation:
            return False, "risk_gate_observation"

        if open_positions_total >= self.limits.max_open_positions_total:
            return False, "risk_gate_max_open_total"

        if open_positions_by_symbol.get(symbol, 0) >= self.limits.max_open_positions_per_symbol:
            return False, "risk_gate_max_open_per_symbol"

        if open_positions_by_direction.get(direction, 0) >= self.limits.max_same_direction_positions:
            return False, "risk_gate_max_same_direction"

        return True, "risk_ok"
