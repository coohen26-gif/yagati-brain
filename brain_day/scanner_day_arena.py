# -*- coding: utf-8 -*-
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
STRATEGIES_DIR = os.path.join(BASE_DIR, "strategies_day")

ENTRY_TF = "5m"
FILTER_TF = "15m"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Feature flag: DISABLE_SUPABASE=1|true|yes will disable Supabase exports.
_disable_flag = os.getenv("DISABLE_SUPABASE", "").strip().lower()
DISABLE_SUPABASE = _disable_flag in ("1", "true", "yes")

if DISABLE_SUPABASE:
    print("[WARN] Supabase export disabled via DISABLE_SUPABASE environment variable.")
elif not SUPABASE_URL or not SERVICE_ROLE_KEY:
    # Do NOT raise: scanner must continue even if Supabase is not configured.
    print("[WARN] Supabase not configured (SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing). Exports will be skipped.")
else:
    print("[INFO] Supabase configured; diagnostics will be exported.")

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}" if SERVICE_ROLE_KEY else None,
    "Content-Type": "application/json",
}

# =====================================================
# STRATEGY LOADING FROM JSON FILES
# =====================================================

def load_strategies_from_dir(strategies_dir: str) -> List[Dict[str, Any]]:
    """Load all strategy JSON files from the strategies_day directory.
    Skips malformed JSON files and logs errors.
    Returns list of loaded strategies.
    """
    strategies = []
    
    if not os.path.exists(strategies_dir):
        print(f"[WARN] Strategies directory not found: {strategies_dir}")
        return strategies
    
    json_files = sorted([f for f in os.listdir(strategies_dir) if f.endswith('.json')])
    
    for filename in json_files:
        filepath = os.path.join(strategies_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                strategy = json.load(f)
                
            # Validate required fields
            if "strategy_key" not in strategy:
                print(f"[WARN] Skipping {filename}: missing 'strategy_key' field")
                continue
                
            strategies.append(strategy)
            print(f"[INFO] Loaded strategy: {strategy['strategy_key']} from {filename}")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse {filename}: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
    
    print(f"[INFO] Successfully loaded {len(strategies)} strategies from {strategies_dir}")
    return strategies

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
    """Post diagnostics payload to Supabase if configured and enabled.
    Non-blocking: logs warnings on failures and returns without raising.
    """
    if not payload:
        return

    if DISABLE_SUPABASE:
        print("[WARN] Supabase export disabled; skipping diagnostics upload.")
        return

    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        print("[WARN] Supabase not configured; skipping diagnostics upload.")
        return

    url = f"{SUPABASE_URL}/rest/v1/day_scanner_diagnostics"
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        if not r.ok:
            print(f"[WARN] Diagnostics insert failed: {r.status_code} {r.text}")
        else:
        print(f"[INFO] Diagnostics uploaded: count={len(payload)}")
    except requests.RequestException as e:
        print(f"[WARN] Supabase request failed: {e}")

# =====================================================
# CORE LOGIC
# =====================================================

def run_strategy(strategy: Dict[str, Any], context: Dict[str, Any], swing_bias: Dict[str, str], run_id: str):
    """Run simplified diagnostic checks for a strategy.
    
    NOTE: This is a simplified scanner that performs basic validation checks.
    The full strategy parameters from JSON (entry.ema_fast, entry.ema_slow, 
    filters.atr_min, etc.) are loaded and available for future implementation
    of complete strategy logic. Currently, the scanner uses simplified checks
    compatible with both old and new strategy formats.
    """
    diagnostics = []
    assets = context.get("assets", {})
    now = utc_now()

    # Extract strategy ID (support both old 'id' and new 'strategy_key' fields)
    strategy_id = strategy.get("strategy_key", strategy.get("id", "UNKNOWN"))

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

        # Handle both old and new strategy formats
        max_dist = strategy.get("max_dist", 1.0)
        ema = tf5.get("ema200") if tf5 else None
        price = tf5.get("last_close") if tf5 else None
        dist_ok = bool(ema and price and dist_pct(price, ema) <= max_dist)
        checks["ema_distance"] = {
            "passed": dist_ok,
            "value": None if not ema or not price else f"{dist_pct(price, ema):.2f}%",
        }
        if not dist_ok:
            reasons.append("EMA_DISTANCE")

        # Handle RSI checks for both old and new formats
        rsi = tf5.get("rsi_14") if tf5 else None
        rsi_long_max = strategy.get("rsi_long_max", 70)
        rsi_short_min = strategy.get("rsi_short_min", 30)
        
        rsi_ok = bool(
            rsi is not None and (
                (bias == "LONG" and rsi <= rsi_long_max) or
                (bias == "SHORT" and rsi >= rsi_short_min)
            )
        )
        checks["rsi"] = {"passed": rsi_ok, "value": rsi}
        if not rsi_ok:
            reasons.append("RSI")

        # Handle session checks for old format (optional for new format)
        session_start = strategy.get("session_start", dtime(0, 0))
        session_end = strategy.get("session_end", dtime(23, 59))
        sess_ok = in_session(now, session_start, session_end)
        checks["session"] = {"passed": sess_ok, "value": now.time().isoformat()}
        if not sess_ok:
            reasons.append("SESSION")

        accepted = len(reasons) == 0

        diagnostics.append({
            "run_id": run_id,
            "strategy_id": strategy_id,
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

    # Load strategies dynamically from JSON files
    strategies = load_strategies_from_dir(STRATEGIES_DIR)
    
    if not strategies:
        print("[WARN] No strategies loaded. Exiting.")
        return

    all_diagnostics = []

    for strat in strategies:
        diags = run_strategy(strat, context, swing, run_id)
        all_diagnostics.extend(diags)

    # Export diagnostics to Supabase if configured and enabled (non-blocking)
    post_diagnostics_api(all_diagnostics)

    print(f"[DAY][ARENA] run={{run_id}} strategies={{len(strategies)}} duration_ms={{int((time.time()-t0)*1000)}}")

if __name__ == "__main__":
    main()
