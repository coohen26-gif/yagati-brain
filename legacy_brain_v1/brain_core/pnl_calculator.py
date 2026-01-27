from typing import Optional

from brain_core.trade_model import TradeModel
from brain_core.trade_state_types import TradeState


class PnLCalculator:
    """
    Calcul du PnL réel en R.
    """

    @staticmethod
    def calculate_r(
        trade: TradeModel,
        exit_price: float,
    ) -> Optional[float]:
        """
        R = (exit - entry) / (entry - stop)
        Adapté LONG / SHORT automatiquement.
        """

        if trade.entry_price is None or trade.stop_loss is None:
            return None

        risk = abs(trade.entry_price - trade.stop_loss)
        if risk == 0:
            return None

        if trade.direction.value == "long":
            r = (exit_price - trade.entry_price) / risk
        else:
            r = (trade.entry_price - exit_price) / risk

        return round(r, 3)

    @staticmethod
    def finalize_trade(
        trade: TradeModel,
        exit_price: float,
    ) -> TradeModel:
        """
        Clôture un trade et calcule le R final.
        """

        r = PnLCalculator.calculate_r(trade, exit_price)
        trade.realized_r = r

        # Harmonisation état final
        if trade.state not in {
            TradeState.TP_FINAL_HIT,
            TradeState.STOP_LOSS_HIT,
            TradeState.POSITION_CLOSED,
        }:
            trade.state = TradeState.POSITION_CLOSED

        return trade
