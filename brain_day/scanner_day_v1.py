import os
import json
import time
import uuid
from datetime import datetime, timezone, time as dtime
from typing import Dict, Any, List
import requests

# =====================================================
# SCANNER DAY — V1.1 (API SUPABASE + DIAGNOSTICS)
# - Brain VPS only
# - Reads intraday_context.json + swing_bias.json
# - Writes DAY signals to day_signals (API)
# - Writes explicit diagnostics to day_scanner_diagnostics (API)
# - NO trades, NO orders
# =====================================================

BASE_DIR = os.path.dirname(__file__)
CONTEXT_FILE = os.path.join(BASE_DIR, "intraday_context.json")
SWING_BIAS_FILE = os.path.join(BASE_DIR, "swing_bias.json")

ENTRY_TF = "5m"
FILTER_TF = "15m"

# ---- V1.1 FILTERS (FIXED) ----
MAX_DIST_EMA_PCT = 0.8        # %
RSI_LONG_MAX = 70.0
RSI_SHORT_MIN = 30.0
SESSION_START_UTC = dtime(7, 0)
SESSION_END_UTC   = dtime(20, 0)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

# ---------------- UTILS ----------------

def utc_now():
    return datetime.now(timezone.utc)

def utc_now_iso() -> str:
    return utc_now().isoformat()

def in_session(now_utc: datetime) -> bool:
    t = now_utc.time()
    return SESSION_START_UTC <= t <= SESSION_END_UTC

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def aligned(direction: str, pvs: str) -> bool:
    return (direction == "LONG" and pvs == "above") or (direction == "SHORT" and pvs == "below")

def ema_status(tf_block: Dict[str, Any]) -> str:
    if tf_block.get("ema200") is not None and tf_block.get("status") in ("ok", "observation"):
        return "MATURE"
    if tf_block.get("ema200") is not None:
        return "WARMING"
    return "COLD"

def dist_pct(price: float, ema: float) -> float:
    return abs((price - ema) / ema) * 100.0

# ---------------- API WRITES ----------------

def upsert_signals_api(signals: List[Dict[str, Any]]) -> None:
    url = f"{SUPABASE_URL}/rest/v1/day_signals"
    r = requests.post(
        url,
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
        json=signals,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase upsert failed: {r.status_code} {r.text}")

def clear_absent_api():
    url = f"{SUPABASE_URL}/rest/v1/day_signals?timeframe=eq.{ENTRY_TF}"
    r = requests.delete(url, headers=HEADERS, timeout=30)
    if not r.ok:
        raise RuntimeError(f"Clear signals failed: {r.status_code} {r.text}")

def post_diagnostics_api(run_id: str, diagnostics: list):
    url = f"{SUPABASE_URL}/rest/v1/day_scanner_diagnostics"
    payload = []
    for d in diagnostics:
        payload.append({
            "run_id": run_id,
            "coingecko_id": d["coingecko_id"],
            "symbol": d["symbol"],
            "final_decision": d["final_decision"],
            "rejection_reasons": d["rejection_reasons"],
            "swing_bias_check": d["checks"]["swing_bias"],
            "filter_15m_check": d["checks"]["filter_15m"],
            "entry_5m_check": d["checks"]["entry_5m"],
            "ema_distance_check": d["checks"]["ema_distance"],
            "rsi_check": d["checks"]["rsi"],
            "session_check": d["checks"]["session"],
            "created_at": utc_now_iso(),
        })

    if not payload:
        return

    r = requests.post(
        url,
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Diagnostics insert failed: {r.status_code} {r.text}")

# ---------------- CORE LOGIC ----------------

def build_signals_and_diagnostics(context: Dict[str, Any], swing_bias: Dict[str, str]):
    signals = []
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
            "value": tf15.get("price_vs_ema200") if tf15 else None
        }
        if not checks["filter_15m"]["passed"]:
            reasons.append("FILTER_15M")

        checks["entry_5m"] = {
            "passed": bool(tf5 and aligned(bias, tf5.get("price_vs_ema200"))),
            "value": tf5.get("price_vs_ema200") if tf5 else None
        }
        if not checks["entry_5m"]["passed"]:
            reasons.append("ENTRY_5M")

        ema = tf5.get("ema200") if tf5 else None
        price = tf5.get("last_close") if tf5 else None
        dist_ok = bool(ema and price and dist_pct(price, ema) <= MAX_DIST_EMA_PCT)
        checks["ema_distance"] = {
            "passed": dist_ok,
            "value": None if not ema or not price else f"{dist_pct(price, ema):.2f}%"
        }
        if not dist_ok:
            reasons.append("EMA_DISTANCE")

        rsi = tf5.get("rsi_14") if tf5 else None
        rsi_ok = bool(
            rsi is not None and (
                (bias == "LONG" and rsi <= RSI_LONG_MAX) or
                (bias == "SHORT" and rsi >= RSI_SHORT_MIN)
            )
        )
        checks["rsi"] = {"passed": rsi_ok, "value": rsi}
        if not rsi_ok:
            reasons.append("RSI")

        sess_ok = in_session(now)
        checks["session"] = {"passed": sess_ok, "value": now.time().isoformat()}
        if not sess_ok:
            reasons.append("SESSION")

        accepted = len(reasons) == 0

        diagnostics.append({
            "coingecko_id": asset.get("coingecko_id"),
            "symbol": symbol,
            "final_decision": "ACCEPTED" if accepted else "REJECTED",
            "rejection_reasons": reasons,
            "checks": checks,
        })

        if accepted:
            signals.append({
                "coingecko_id": asset.get("coingecko_id"),
                "symbol": symbol,
                "timeframe": ENTRY_TF,
                "bias": bias,
                "swing_bias": bias,
                "entry_zone": None,
                "stop_loss": None,
                "tp1": None,
                "rsi_14": rsi,
                "ema200_status": ema_status(tf5),
                "confluence_score": 5,
                "updated_at": utc_now_iso(),
            })

    return signals, diagnostics

# ---------------- MAIN ----------------

def main():
    t0 = time.time()
    run_id = str(uuid.uuid4())

    context = load_json(CONTEXT_FILE)
    swing = load_json(SWING_BIAS_FILE).get("bias", {})

    signals, diagnostics = build_signals_and_diagnostics(context, swing)

    if signals:
        upsert_signals_api(signals)
    # else:
    #     clear_absent_api()

    # post_diagnostics_api(run_id, diagnostics)

    print(f"[DAY][SCANNER][DIAGNOSTICS] run={run_id} signals={len(signals)} duration_ms={int((time.time()-t0)*1000)}")

if __name__ == "__main__":
    main()
