import json
import os
from typing import Dict, List

from brain_core.trade_model import TradeModel
from brain_core.trade_state_types import TradeState


class TradeRepository:
    """
    Persistance simple des trades (V1).
    JSON local, compatible upgrade Supabase plus tard.
    """

    def __init__(self, base_path: str = "/root/brain/data"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.open_path = os.path.join(self.base_path, "open_trades.json")
        self.closed_path = os.path.join(self.base_path, "closed_trades.json")

    def _load(self, path: str) -> Dict[str, dict]:
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _save(self, path: str, data: Dict[str, dict]) -> None:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def save_open(self, trade: TradeModel) -> None:
        data = self._load(self.open_path)
        data[trade.trade_id] = self._serialize(trade)
        self._save(self.open_path, data)

    def save_closed(self, trade: TradeModel) -> None:
        open_data = self._load(self.open_path)
        open_data.pop(trade.trade_id, None)
        self._save(self.open_path, open_data)

        closed_data = self._load(self.closed_path)
        closed_data[trade.trade_id] = self._serialize(trade)
        self._save(self.closed_path, closed_data)

    def load_open_trades(self) -> List[TradeModel]:
        data = self._load(self.open_path)
        return [self._deserialize(v) for v in data.values()]

    def load_closed_trades(self) -> List[TradeModel]:
        data = self._load(self.closed_path)
        return [self._deserialize(v) for v in data.values()]

    def _serialize(self, trade: TradeModel) -> dict:
        return {
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "direction": trade.direction.value,
            "entry_price": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "tp1": trade.tp1,
            "tp2": trade.tp2,
            "state": trade.state.name,
            "created_at": trade.created_at.isoformat() if trade.created_at else None,
            "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
            "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
            "realized_r": trade.realized_r,
            "notes": trade.notes,
        }

    def _deserialize(self, data: dict) -> TradeModel:
        trade = TradeModel(
            trade_id=data["trade_id"],
            symbol=data["symbol"],
            direction=data["direction"],
            entry_price=data.get("entry_price"),
            stop_loss=data.get("stop_loss"),
            tp1=data.get("tp1"),
            tp2=data.get("tp2"),
        )
        trade.state = TradeState[data["state"]]
        trade.realized_r = data.get("realized_r")
        trade.notes = data.get("notes")
        return trade
