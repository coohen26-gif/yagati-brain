from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class MemoryEvent:
    ts: datetime
    symbol: str
    strategy_id: str
    event_type: str
    meta: dict = field(default_factory=dict)


class BrainMemory:
    def __init__(self):
        self.events: List[MemoryEvent] = []

    def add_event(self, symbol: str, strategy_id: str, event_type: str, meta: Optional[dict] = None) -> None:
        self.events.append(
            MemoryEvent(
                ts=datetime.utcnow(),
                symbol=symbol,
                strategy_id=strategy_id,
                event_type=event_type,
                meta=meta or {},
            )
        )

    def prune(self, max_age_hours: int = 72) -> None:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        self.events = [e for e in self.events if e.ts >= cutoff]
