from typing import Optional
from datetime import datetime


class BrainGlobalStateUpdater:
    """
    Mise à jour du brain_global_state.
    """

    @staticmethod
    def build_state(
        decision: str,
        reason: str,
        market_regime: str,
        market_phase: str,
        active_strategy: Optional[str] = None,
    ) -> dict:
        return {
            "decision": decision,
            "reason": reason,
            "market_regime": market_regime,
            "market_phase": market_phase,
            "active_strategy": active_strategy,
            "updated_at": datetime.utcnow().isoformat(),
        }
