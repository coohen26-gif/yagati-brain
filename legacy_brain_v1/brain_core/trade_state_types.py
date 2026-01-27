from enum import Enum, auto


class TradeState(Enum):
    """
    États possibles du cycle de vie complet d’un trade.
    Source de vérité unique.
    """

    IDLE = auto()
    SETUP_DETECTED = auto()
    ENTRY_CONFIRMED = auto()
    POSITION_OPEN = auto()
    PARTIAL_TP_HIT = auto()
    BREAKEVEN = auto()
    TP_FINAL_HIT = auto()
    STOP_LOSS_HIT = auto()
    POSITION_CLOSED = auto()


class TradeEvent(Enum):
    """
    Événements générés par le Brain.
    """

    SETUP_DETECTED = auto()
    ENTRY_CONFIRMED = auto()
    POSITION_OPENED = auto()
    PARTIAL_TP_HIT = auto()
    BREAKEVEN_REACHED = auto()
    TP_FINAL_HIT = auto()
    STOP_LOSS_HIT = auto()
    POSITION_CLOSED = auto()


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"
