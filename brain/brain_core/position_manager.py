from typing import Dict, Optional
from datetime import datetime

from brain_core.trade_model import TradeModel
from brain_core.trade_state_types import TradeState, TradeEvent
from brain_core.trade_state_machine import TradeStateMachine


class PositionManager:
    """
    Gestionnaire des positions ouvertes / clôturées.
    Source de vérité LIVE.
    """

    def __init__(self):
        # trade_id -> TradeModel
        self.open_positions: Dict[str, TradeModel] = {}
        self.closed_positions: Dict[str, TradeModel] = {}

    def open_position(self, trade: TradeModel) -> None:
        TradeStateMachine.transition(trade, TradeEvent.POSITION_OPENED)
        self.open_positions[trade.trade_id] = trade

    def mark_tp1(self, trade_id: str) -> Optional[TradeModel]:
        trade = self.open_positions.get(trade_id)
        if not trade:
            return None
        TradeStateMachine.transition(trade, TradeEvent.PARTIAL_TP_HIT)
        return trade

    def mark_breakeven(self, trade_id: str) -> Optional[TradeModel]:
        trade = self.open_positions.get(trade_id)
        if not trade:
            return None
        TradeStateMachine.transition(trade, TradeEvent.BREAKEVEN_REACHED)
        return trade

    def close_tp(self, trade_id: str) -> Optional[TradeModel]:
        trade = self.open_positions.pop(trade_id, None)
        if not trade:
            return None
        TradeStateMachine.transition(trade, TradeEvent.TP_FINAL_HIT)
        self.closed_positions[trade.trade_id] = trade
        return trade

    def close_sl(self, trade_id: str) -> Optional[TradeModel]:
        trade = self.open_positions.pop(trade_id, None)
        if not trade:
            return None
        TradeStateMachine.transition(trade, TradeEvent.STOP_LOSS_HIT)
        self.closed_positions[trade.trade_id] = trade
        return trade

    def force_close(self, trade_id: str, note: str = "manual_close") -> Optional[TradeModel]:
        trade = self.open_positions.pop(trade_id, None)
        if not trade:
            return None
        TradeStateMachine.transition(trade, TradeEvent.POSITION_CLOSED)
        trade.notes = note
        self.closed_positions[trade.trade_id] = trade
        return trade

    def count_open(self) -> int:
        return len(self.open_positions)

    def count_closed(self) -> int:
        return len(self.closed_positions)

    def get_open_by_symbol(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for t in self.open_positions.values():
            out[t.symbol] = out.get(t.symbol, 0) + 1
        return out

    def get_open_by_direction(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for t in self.open_positions.values():
            d = t.direction.value
            out[d] = out.get(d, 0) + 1
        return out
