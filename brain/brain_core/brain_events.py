from typing import Dict, Any
from datetime import datetime

from brain_core.trade_state_types import TradeEvent
from brain_core.trade_model import TradeModel


class BrainEventBus:
    """
    Bus d’événements du Brain.
    """

    @staticmethod
    def build_event(event: TradeEvent, trade: TradeModel) -> Dict[str, Any]:
        return {
            "event_type": event.name,
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "direction": trade.direction.value,
            "state": trade.state.name,
            "entry_price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "tp1": trade.tp1,
            "tp2": trade.tp2,
            "timestamp": datetime.utcnow().isoformat(),
        }
