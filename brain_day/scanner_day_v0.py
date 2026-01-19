import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# =====================================================
# SCANNER DAY — V0 (READ-ONLY)
# - Reads intraday_context.json
# - Timeframe: 5m only
# - Rule: price vs EMA200
# - Outputs DAY signals (NO trades)
# =====================================================

BASE_DIR = os.path.dirname(__file__)
CONTEXT_FILE = os.path.join(BASE_DIR, "intraday_context.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "day_signals_v0.json")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_context() -> Dict[str, Any]:
    if not os.path.exists(CONTEXT_FILE):
        raise RuntimeError("intraday_context.json not found")
    with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def build_signals(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []
    assets = context.get("assets", {})

    for symbol, asset_block in assets.items():
        tf_block = asset_block.get("timeframes", {}).get("5m")
        if not tf_block:
            continue

        status = tf_block.get("status")
        if status != "ok":
            continue

        ema = tf_block.get("ema200")
        pvs = tf_block.get("price_vs_ema200")
        slope = tf_block.get("ema200_slope")

        if ema is None or pvs not in ("above", "below"):
            continue

        direction = "LONG" if pvs == "above" else "SHORT"

        signals.append({
            "symbol": symbol,
            "timeframe": "5m",
            "direction": direction,
            "ema200": ema,
            "ema200_slope": slope,
            "generated_at": utc_now_iso(),
            "kind": "DAY_SIGNAL_V0",
        })

    return signals

def write_output(signals: List[Dict[str, Any]]) -> None:
    payload = {
        "generated_at": utc_now_iso(),
        "count": len(signals),
        "signals": signals,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def main() -> None:
    context = load_context()
    signals = build_signals(context)
    write_output(signals)

    print(f"[DAY][SCANNER_V0] signals={len(signals)}")
    for s in signals:
        print(f" - {s['symbol']} {s['timeframe']} {s['direction']} (EMA200 slope={s['ema200_slope']})")

if __name__ == "__main__":
    main()
