import os
import json
import time
import uuid
from datetime import datetime, timezone, time as dtime
from typing import Dict, Any, List
import requests

# =====================================================
# SCANNER DAY — ARENA
# SAFE / BALANCED / AGGRESSIVE
# - Même données
# - Règles différentes
# - Aucune exécution de trade
# - Écrit diagnostics explicites
# =====================================================

BASE_DIR = os.path.dirname(__file__)
CONTEXT_FILE = os.path.join(BASE_DIR, "intraday_context.json")
SWING_BIAS_FILE = os.path.join(BASE_DIR, "swing_bias.json")

ENTRY_TF = "5m"
FILTER_TF = "15m"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

# =====================================================
# STRATÉGIES DE L’ARÈNE (FIGÉES)
# =====================================================

STRATEGIES = [
    {
        "id": "DAY_SAFE_V1",
        "max_dist": 0.5,
        "rsi_long_max": 65,
        "rsi_short_min": 35,
        "session_start": dtime(8, 0),
        "session_end": dtime(18, 0),
    },
    {
        "id": "DAY_BAL_V1",
        "max_dist": 0.8,
        "rsi_long_max": 70,
        "rsi_short_min": 30,
        "session_start": dtime(7, 0),
        "session_end": dtime(20, 0),
    },
    {
        "id": "DAY_AGG_V1",
        "max_dist": 1.2,
        "rsi_long_max": 75,
        "rsi_short_min": 25,
        "session_start": dtime(6, 0),
        "session_end": dtime(22, 0),
    },
]

# =====================================================
# UTILS
# =====================================================

def utc_now():
    return datetime.now(timezone.utc)

def utc_now_iso():
    return utc_now().isoformat()

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def aligned(direction: str, pvs: str) -> bool:
    return (direction == "LONG" and pvs == "above") or (direction == "SHORT" and pvs == "below")

def in_session(now_utc: datetime, start: dtime, end: dtime) -> bool:
    t = now_utc.time()
    return start <= t <= end

def dist_pct(price: float, ema: float) -> float:
    return abs((price - ema) / ema) * 100.0

# =====================================================
# API WRITE
# =====================================================

def post_diagnostics_api(payload: List[Dict[str, Any]]):
    if not payload:
        return
    url = f"{SUPABASE_URL}/rest/v1/day_scanner_diagnostics"
    r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    if not r.ok:
        raise RuntimeError(f"Diagnostics insert failed: {r.status_code} {r.text}")

# =====================================================
# CORE LOGIC
# =====================================================

def run_strategy(strategy: Dict[str, Any], context: Dict[str, Any], swing_bias: Dict[str, str], run_id: str):
    diagnostics = []
    assets = context.get("assets", {})
    now = utc_now()

    for symbol, asset in assets.items():
        reasons = []
        checks = {}

        bias = swing_bias.get(symbol, "NONE")
        checks["swing_bias"] = {"passed": bias in ("LONG", "SHORT"), "value": bias}
        if bias not in ("LONG", "SHORT"):
            reasons.append("SWING_BIAS")

        tf5 = asset.get("timeframes", {}).get(ENTRY_TF)
        tf15 = asset.get("timeframes", {}).get(FILTER_TF)

        checks["filter_15m"] = {
            "passed": bool(tf15 and aligned(bias, tf15.get("price_vs_ema200"))),
            "value": tf15.get("price_vs_ema200") if tf15 else None,
        }
        if not checks["filter_15m"]["passed"]:
            reasons.append("FILTER_15M")

        checks["entry_5m"] = {
            "passed": bool(tf5 and aligned(bias, tf5.get("price_vs_ema200"))),
            "value": tf5.get("price_vs_ema200") if tf5 else None,
        }
        if not checks["entry_5m"]["passed"]:
            reasons.append("ENTRY_5M")

        ema = tf5.get("ema200") if tf5 else None
        price = tf5.get("last_close") if tf5 else None
        dist_ok = bool(ema and price and dist_pct(price, ema) <= strategy["max_dist"])
        checks["ema_distance"] = {
            "passed": dist_ok,
            "value": None if not ema or not price else f"{dist_pct(price, ema):.2f}%",
        }
        if not dist_ok:
            reasons.append("EMA_DISTANCE")

        rsi = tf5.get("rsi_14") if tf5 else None
        rsi_ok = bool(
            rsi is not None and (
                (bias == "LONG" and rsi <= strategy["rsi_long_max"]) or
                (bias == "SHORT" and rsi >= strategy["rsi_short_min"])
            )
        )
        checks["rsi"] = {"passed": rsi_ok, "value": rsi}
        if not rsi_ok:
            reasons.append("RSI")

        sess_ok = in_session(now, strategy["session_start"], strategy["session_end"])
        checks["session"] = {"passed": sess_ok, "value": now.time().isoformat()}
        if not sess_ok:
            reasons.append("SESSION")

        accepted = len(reasons) == 0

        diagnostics.append({
            "run_id": run_id,
            "strategy_id": strategy["id"],
            "coingecko_id": asset.get("coingecko_id"),
            "symbol": symbol,
            "final_decision": "ACCEPTED" if accepted else "REJECTED",
            "rejection_reasons": reasons,
            "swing_bias_check": checks["swing_bias"],
            "filter_15m_check": checks["filter_15m"],
            "entry_5m_check": checks["entry_5m"],
            "ema_distance_check": checks["ema_distance"],
            "rsi_check": checks["rsi"],
            "session_check": checks["session"],
            "created_at": utc_now_iso(),
        })

    return diagnostics

# =====================================================
# MAIN
# =====================================================

def main():
    t0 = time.time()
    run_id = str(uuid.uuid4())

    context = load_json(CONTEXT_FILE)
    swing = load_json(SWING_BIAS_FILE).get("bias", {})

    all_diagnostics = []

    for strat in STRATEGIES:
        diags = run_strategy(strat, context, swing, run_id)
        all_diagnostics.extend(diags)

    post_diagnostics_api(all_diagnostics)

    print(f"[DAY][ARENA] run={run_id} strategies={len(STRATEGIES)} duration_ms={int((time.time()-t0)*1000)}")

if __name__ == "__main__":
    main()
