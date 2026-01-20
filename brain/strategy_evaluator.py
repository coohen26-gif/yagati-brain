"""Strategy-level evaluator.

This module exposes exactly one public function: evaluate_strategy(trades: list) -> dict

The function aggregates trade outcomes for a single strategy (or a list of trades belonging to a strategy)
and returns a decision (KEEP, ADJUST, KILL) along with simple metrics and a human reason.
"""
from typing import List, Dict, Any


def evaluate_strategy(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate a list of trades and return a strategy-level decision and metrics.

    Args:
        trades: List of trade dictionaries produced by other parts of the system. Trades may
                contain fields such as `decision`, `realized_r`, `rr`, `final_result_percent`.
                Missing fields are handled gracefully.

    Returns:
        A dict with the exact shape required by the integration tests / consumers.
    """
    # Defensive defaults
    if not isinstance(trades, list):
        trades = []

    total = len(trades)
    wins = 0
    losses = 0
    rr_values = []

    for t in trades:
        if not isinstance(t, dict):
            continue

        # Count wins/losses: prefer explicit `decision` field when provided
        decision = (t.get("decision") or "").upper() if t.get("decision") is not None else None
        counted = False
        if decision in ("KEEP", "KILL"):
            if decision == "KEEP":
                wins += 1
            else:
                losses += 1
            counted = True

        # If no explicit decision, fall back to numeric outcome fields
        if not counted:
            # Primary numeric outcome: realized_r (R units)
            rr_outcome = t.get("realized_r")
            if rr_outcome is None:
                # Some legacy places use final_result_percent — use sign only
                frp = t.get("final_result_percent")
                if frp is not None:
                    try:
                        val = float(frp)
                        if val > 0:
                            wins += 1
                        else:
                            losses += 1
                        counted = True
                    except Exception:
                        pass
            else:
                try:
                    val = float(rr_outcome)
                    if val > 0:
                        wins += 1
                    else:
                        losses += 1
                    counted = True
                except Exception:
                    pass

        # Collect RR values for averaging (prefer realized_r, else rr)
        rr_val = None
        if t.get("realized_r") is not None:
            try:
                rr_val = float(t.get("realized_r"))
            except Exception:
                rr_val = None
        elif t.get("rr") is not None:
            try:
                rr_val = float(t.get("rr"))
            except Exception:
                rr_val = None

        if rr_val is not None:
            rr_values.append(rr_val)

    # Prevent division by zero; total is number of trades provided
    total_nonzero = total if total > 0 else 1

    # Win rate as percentage (0-100)
    win_rate = round((wins / total_nonzero) * 100.0, 2)

    # Average RR
    if rr_values:
        avg_rr = round(sum(rr_values) / len(rr_values), 2)
    else:
        avg_rr = 0.0

    # Decision thresholds (must not be changed elsewhere):
    # - KILL if losses / total > 0.6
    # - KEEP if wins / total > 0.6
    # - otherwise ADJUST
    loss_ratio = (losses / total_nonzero) if total > 0 else 0.0
    win_ratio = (wins / total_nonzero) if total > 0 else 0.0

    if loss_ratio > 0.6:
        decision_out = "KILL"
    elif win_ratio > 0.6:
        decision_out = "KEEP"
    else:
        decision_out = "ADJUST"

    reason = (
        f"{wins}/{total} wins, {losses}/{total} losses — win_rate={win_rate}%, avg_rr={avg_rr}"
    )

    return {
        "decision": decision_out,
        "metrics": {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": float(win_rate),
            "avg_rr": float(avg_rr),
        },
        "reason": reason,
    }
