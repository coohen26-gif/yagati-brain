from typing import Dict, Any

from brain_core.trade_model import TradeModel
from brain_core.trade_state_types import TradeEvent, TradeDirection
from brain_core.trade_state_machine import TradeStateMachine
from brain_core.brain_events import BrainEventBus
from brain_core.risk_manager import RiskManager
from brain_core.brain_memory import BrainMemory


class BrainCoreIntegration:
    """
    Pont propre entre le runtime existant et le brain_core.
    """

    def __init__(self):
        self.risk_manager = RiskManager()
        self.memory = BrainMemory()

    def build_trade_from_signal(self, signal: Dict[str, Any]) -> TradeModel:
        trade = TradeModel(
            trade_id=signal["id"],
            symbol=signal["symbol"],
            direction=TradeDirection(signal["direction"]),
            entry_price=signal.get("entry_price"),
            stop_loss=signal.get("stop_loss"),
            tp1=signal.get("tp1"),
            tp2=signal.get("tp2"),
        )
        TradeStateMachine.transition(trade, TradeEvent.SETUP_DETECTED)
        return trade

    def confirm_entry(
        self,
        trade: TradeModel,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Confirme une entrée si le risk manager l'autorise.
        """
        allowed, reason = self.risk_manager.can_open_new_position(
            symbol=trade.symbol,
            direction=trade.direction.value,
            open_positions_total=context["open_positions_total"],
            open_positions_by_symbol=context["open_positions_by_symbol"],
            open_positions_by_direction=context["open_positions_by_direction"],
            brain_decision=context["brain_decision"],
        )

        if not allowed:
            self.memory.add_event(
                symbol=trade.symbol,
                strategy_id=context.get("strategy_id", "unknown"),
                event_type="ENTRY_REFUSED",
                meta={"reason": reason},
            )
            return {"allowed": False, "reason": reason}

        TradeStateMachine.transition(trade, TradeEvent.ENTRY_CONFIRMED)
        event = BrainEventBus.build_event(TradeEvent.ENTRY_CONFIRMED, trade)

        self.memory.add_event(
            symbol=trade.symbol,
            strategy_id=context.get("strategy_id", "unknown"),
            event_type="ENTRY_CONFIRMED",
            meta=event,
        )

        return {"allowed": True, "event": event}
