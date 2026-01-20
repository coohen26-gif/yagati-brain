"""Strategy-level evaluator.

Exposes exactly one public function:
    evaluate_strategy(trades: list) -> dict

This file corrects a previous implementation that introduced fixed numeric thresholds
inside the evaluator (e.g. 0.6). Per project handover rules, the evaluator must not
invent or freeze new decision thresholds. Instead this implementation:
 - Aggregates metrics (total, wins, losses, win_rate, avg_rr)
 - Uses explicit per-trade `decision` values when available (plurality wins)
 - Falls back to numeric outcome aggregation but remains conservative: without
   explicit trade-level decisions the evaluator will not produce an aggressive
   KILL; it prefers ADJUST when outcomes are mixed or negative.

Only the logic in this file was changed to remove hard-coded thresholds. No other
files were modified.
"""

from typing import Any, Dict, List


def evaluate_strategy(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate a list of trades and return a strategy-level decision and metrics.

    Args:
        trades: list of trade dictionaries. Trades may contain:
            - decision: "KEEP" | "KILL" | "ADJUST"
            - realized_r: numeric (R units)
            - rr: numeric (risk/reward estimate)
            - final_result_percent: numeric percentage (legacy)

    Returns:
        dict with exactly the following shape:
        {
          "decision": "KEEP|ADJUST|KILL",
          "metrics": {
            "total_trades": int,
            "wins": int,
            "losses": int,
            "win_rate": float,
            "avg_rr": float
          },
          "reason": "clear human explanation"
        }

    Notes:
    - This implementation intentionally avoids introducing new fixed thresholds.
      It prefers explicit per-trade `decision` values when available and otherwise
      falls back to a conservative, qualitative assessment based on numeric outcomes.
    - Low sample sizes do not trigger an aggressive KILL unless the trades
      themselves explicitly recorded KILL decisions.
    """
    # Defensive normalization
    if not isinstance(trades, list):
        trades = []

    total_trades = len(trades)

    # Counters
    explicit_keep = 0
    explicit_kill = 0
    explicit_adjust = 0
    wins = 0
    losses = 0
    rr_values: List[float] = []

    for t in trades:
        if not isinstance(t, dict):
            continue

        # Count explicit decisions first
        dec = t.get("decision")
        if isinstance(dec, str):
            d = dec.strip().upper()
            if d == "KEEP":
                explicit_keep += 1
            elif d == "KILL":
                explicit_kill += 1
            elif d == "ADJUST":
                explicit_adjust += 1

        # Determine win/loss from numeric fields (used for metrics and fallback)
        outcome_counted = False
        if t.get("realized_r") is not None:
            try:
                v = float(t.get("realized_r"))
                if v > 0:
                    wins += 1
                else:
                    losses += 1
                outcome_counted = True
            except Exception:
                outcome_counted = False

        if not outcome_counted:
            frp = t.get("final_result_percent")
            if frp is not None:
                try:
                    v = float(frp)
                    if v > 0:
                        wins += 1
                    else:
                        losses += 1
                    outcome_counted = True
                except Exception:
                    pass

        # Collect RR values for averaging: prefer realized_r, else rr
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

    # Metrics calculations
    denom = total_trades if total_trades > 0 else 1
    win_rate = round((wins / denom) * 100.0, 2)
    avg_rr = round(sum(rr_values) / len(rr_values), 2) if rr_values else 0.0

    # Decision logic - no new fixed numeric thresholds are introduced here.
    # - If explicit per-trade decisions exist, select the plurality (most common).
    #   Ties or unclear pluralities fall back to ADJUST.
    # - If no explicit decisions are present, use numeric outcomes conservatively:
    #   * wins > losses -> KEEP
    #   * losses >= wins -> ADJUST (conservative: do not return KILL solely
    #     on numeric outcomes to avoid aggressive actions on limited data)

    explicit_total = explicit_keep + explicit_kill + explicit_adjust
    decision_out = "ADJUST"
    reason = "No clear decision — default ADJUST"

    if explicit_total > 0:
        # Determine plurality among explicit decisions
        counts = {
            "KEEP": explicit_keep,
            "KILL": explicit_kill,
            "ADJUST": explicit_adjust,
        }
        # Find the decision(s) with the maximum count
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count and v > 0]

        if len(winners) == 1:
            decision_out = winners[0]
            reason = (
                f"Explicit decisions: KEEP={explicit_keep}, KILL={explicit_kill}, ADJUST={explicit_adjust}; "
                f"selected {decision_out} by plurality"
            )
        else:
            # Tie or no majority -> ADJUST conservatively
            decision_out = "ADJUST"
            reason = (
                f"Explicit decisions tied or unclear: KEEP={explicit_keep}, KILL={explicit_kill}, ADJUST={explicit_adjust}; "
                f"fallback to ADJUST"
            )
    else:
        # No explicit decisions — use numeric outcomes but remain conservative
        if wins > losses:
            decision_out = "KEEP"
            reason = f"Aggregated outcomes: {wins}/{total_trades} wins vs {losses} losses — KEEP (positive bias)"
        elif losses > wins:
            decision_out = "ADJUST"
            reason = (
                f"Aggregated outcomes: {wins}/{total_trades} wins vs {losses} losses — "
                f"prefer ADJUST over KILL in absence of explicit KILL votes"
            )
        else:
            decision_out = "ADJUST"
            reason = f"No decisive outcome ({wins} wins, {losses} losses) — ADJUST"

    # Final returned structure must match exact shape
    return {
        "decision": decision_out,
        "metrics": {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": float(win_rate),
            "avg_rr": float(avg_rr),
        },
        "reason": reason,
    }