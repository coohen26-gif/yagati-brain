from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from brain_core.trade_state_types import TradeState, TradeDirection


@dataclass
class TradeModel:
    """
    Modèle central d’un trade.
    """

    trade_id: str
    symbol: str
    direction: TradeDirection

    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None

    state: TradeState = TradeState.IDLE

    created_at: datetime = field(default_factory=datetime.utcnow)
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    realized_r: Optional[float] = None
    notes: Optional[str] = None

    def is_open(self) -> bool:
        return self.state in {
            TradeState.ENTRY_CONFIRMED,
            TradeState.POSITION_OPEN,
            TradeState.PARTIAL_TP_HIT,
            TradeState.BREAKEVEN,
        }

    def is_closed(self) -> bool:
        return self.state in {
            TradeState.TP_FINAL_HIT,
            TradeState.STOP_LOSS_HIT,
            TradeState.POSITION_CLOSED,
        }
