import os
import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# =====================================================
# BRAIN DAY — V1.2 (CONTEXT ONLY)
# - DAY-only
# - Source: Bitget (ohlc_cache_intraday as cache)
# - EMA200 computed on RUNTIME fetch (truth)
# - Maturity based on runtime length, NOT DB count
# - 5m: operational
# - 15m: observation only
# - NO signals, NO trades
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY env vars.")

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}

BASE_DIR = os.path.dirname(__file__)
LAST_RUN_FILE = os.path.join(BASE_DIR, "last_run.txt")
CONTEXT_FILE = os.path.join(BASE_DIR, "intraday_context.json")

# =====================================================
# DAY UNIVERSE
# =====================================================

DAY_ASSETS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "PAXG": "pax-gold",
    "XAUT": "tether-gold",
}

TIMEFRAMES = ("5m", "15m")

EMA_PERIOD = 200
FETCH_LIMIT = 300          # runtime truth
RUNTIME_MIN_FOR_EMA = 200  # maturity based on runtime

# =====================================================
# UTILS
# =====================================================

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_last_run() -> Optional[datetime]:
    if not os.path.exists(LAST_RUN_FILE):
        return None
    with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        return datetime.fromisoformat(raw) if raw else None

def save_last_run(dt: datetime) -> None:
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        f.write(dt.isoformat())

def safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None

def ema(series: List[float], period: int) -> List[float]:
    if len(series) < period:
        return []
    k = 2 / (period + 1)
    seed = sum(series[:period]) / period
    values: List[float] = [seed] * period
    prev = seed
    for price in series[period:]:
        prev = (price * k) + (prev * (1 - k))
        values.append(prev)
    return values

def slope_label(ema_values: List[float], lookback: int) -> str:
    if len(ema_values) <= lookback:
        return "unknown"
    if ema_values[-1] > ema_values[-1 - lookback]:
        return "up"
    if ema_values[-1] < ema_values[-1 - lookback]:
        return "down"
    return "flat"

def fetch_intraday_closes(
    coingecko_id: str,
    timeframe: str,
    limit: int,
) -> Tuple[List[str], List[float]]:
    url = (
        f"{SUPABASE_URL}/rest/v1/ohlc_cache_intraday"
        f"?select=timestamp,close"
        f"&coingecko_id=eq.{coingecko_id}"
        f"&timeframe=eq.{timeframe}"
        f"&order=timestamp.asc"
        f"&limit={limit}"
    )
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    rows = r.json() if isinstance(r.json(), list) else []
    ts, closes = [], []
    for row in rows:
        c = safe_float(row.get("close"))
        if row.get("timestamp") and c is not None:
            ts.append(row["timestamp"])
            closes.append(c)
    return ts, closes

def write_context(ctx: Dict[str, Any]) -> None:
    with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2)

# =====================================================
# CORE — CONTEXT BUILDER
# =====================================================

def build_intraday_context() -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "mode": "DAY",
        "kind": "INTRADAY_CONTEXT_V1_2",
        "generated_at": utc_now_iso(),
        "ema_period": EMA_PERIOD,
        "runtime_fetch": FETCH_LIMIT,
        "assets": {},
        "health": {"ok": True, "notes": []},
    }

    for symbol, coingecko_id in DAY_ASSETS.items():
        asset_block = {"symbol": symbol, "timeframes": {}}

        for tf in TIMEFRAMES:
            tf_block = {
                "bars_runtime": 0,
                "ema200": None,
                "price_vs_ema200": "unknown",
                "ema200_slope": "unknown",
                "status": "observation" if tf == "15m" else "ok",
            }

            ts, closes = fetch_intraday_closes(coingecko_id, tf, FETCH_LIMIT)
            tf_block["bars_runtime"] = len(closes)

            # Maturity based on RUNTIME only
            if len(closes) < RUNTIME_MIN_FOR_EMA:
                tf_block["status"] = "insufficient_runtime"
                context["health"]["ok"] = False
                context["health"]["notes"].append(
                    f"{symbol} {tf}: insufficient runtime bars ({len(closes)}/{RUNTIME_MIN_FOR_EMA})"
                )
            else:
                ema_values = ema(closes, EMA_PERIOD)
                if not ema_values:
                    tf_block["status"] = "error"
                    context["health"]["ok"] = False
                    context["health"]["notes"].append(
                        f"{symbol} {tf}: EMA computation failed"
                    )
                else:
                    last_ema = ema_values[-1]
                    last_close = closes[-1]
                    tf_block["ema200"] = last_ema
                    tf_block["price_vs_ema200"] = (
                        "above" if last_close > last_ema else "below"
                    )
                    tf_block["ema200_slope"] = slope_label(
                        ema_values, lookback=6 if tf == "5m" else 3
                    )
                    # 15m remains observation even if EMA exists
                    tf_block["status"] = "ok" if tf == "5m" else "observation"

            asset_block["timeframes"][tf] = tf_block

        context["assets"][symbol] = asset_block

    return context

# =====================================================
# MAIN
# =====================================================

def main() -> None:
    now = datetime.now(timezone.utc)
    ctx = build_intraday_context()
    write_context(ctx)
    save_last_run(now)

    ok = ctx["health"]["ok"]
    print(f"[DAY][CONTEXT] generated_at={ctx['generated_at']} ok={ok}")
    for n in ctx["health"]["notes"]:
        print(f" - {n}")

if __name__ == "__main__":
    main()
