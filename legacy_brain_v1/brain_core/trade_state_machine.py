from datetime import datetime

from brain_core.trade_state_types import TradeState, TradeEvent
from brain_core.trade_model import TradeModel


class TradeStateMachine:
    """
    Machine à états stricte pour un trade.
    """

    @staticmethod
    def transition(trade: TradeModel, event: TradeEvent) -> None:
        current = trade.state

        if event == TradeEvent.SETUP_DETECTED:
            trade.state = TradeState.SETUP_DETECTED

        elif event == TradeEvent.ENTRY_CONFIRMED:
            trade.state = TradeState.ENTRY_CONFIRMED
            trade.opened_at = datetime.utcnow()

        elif event == TradeEvent.POSITION_OPENED:
            trade.state = TradeState.POSITION_OPEN

        elif event == TradeEvent.PARTIAL_TP_HIT:
            trade.state = TradeState.PARTIAL_TP_HIT

        elif event == TradeEvent.BREAKEVEN_REACHED:
            trade.state = TradeState.BREAKEVEN

        elif event == TradeEvent.TP_FINAL_HIT:
            trade.state = TradeState.TP_FINAL_HIT
            trade.closed_at = datetime.utcnow()

        elif event == TradeEvent.STOP_LOSS_HIT:
            trade.state = TradeState.STOP_LOSS_HIT
            trade.closed_at = datetime.utcnow()

        elif event == TradeEvent.POSITION_CLOSED:
            trade.state = TradeState.POSITION_CLOSED
            trade.closed_at = datetime.utcnow()

        else:
            raise ValueError(f"Transition non supportée: {event}")

        trade.notes = f"{current.name} → {trade.state.name}"
