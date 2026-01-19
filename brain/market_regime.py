import os
import requests
from math import fabs

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}

def fetch_ohlc(symbol: str, timeframe: str, limit: int = 260):
    url = f"{SUPABASE_URL}/functions/v1/market-data/ohlc"
    params = {
        "symbol": symbol,
        "timeframe": timeframe,
        "limit": str(limit),
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def ema(values, period: int):
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e

def slope(values, lookback: int = 20):
    if len(values) < lookback:
        return None
    first = values[-lookback]
    last = values[-1]
    if first == 0:
        return None
    return (last - first) / first

def detect_regime(symbol: str):
    candles = fetch_ohlc(symbol, "1d", limit=260)
    closes = [float(c["close"]) for c in candles if c.get("close") is not None]

    if len(closes) < 210:
        return {"regime": "TRANSITION", "bias": None}

    last = closes[-1]
    ema200 = ema(closes[-210:], 200)
    if ema200 is None:
        return {"regime": "TRANSITION", "bias": None}

    dist_pct = fabs(last - ema200) / ema200 * 100.0
    slp = slope(closes, lookback=20)
    if slp is None:
        return {"regime": "TRANSITION", "bias": None}

    slope_pct = slp * 100.0

    if dist_pct <= 1.0 and abs(slope_pct) <= 0.15:
        return {
            "regime": "RANGE",
            "bias": None,
        }

    if dist_pct >= 2.0 and abs(slope_pct) >= 0.35:
        bias = "UP" if last > ema200 else "DOWN"
        return {
            "regime": "TREND",
            "bias": bias,
        }

    return {
        "regime": "TRANSITION",
        "bias": None,
    }


def detect_market_phase_from_regime(symbol: str):
    """
    Derive a coarse market phase from existing regime logic.
    Returns: 'IMPULSE' | 'PULLBACK' | 'EXHAUSTION'
    """
    regime_data = detect_regime(symbol)
    regime = regime_data.get("regime")
    bias = regime_data.get("bias")

    # Fetch data again (no refactor, explicit call)
    candles = fetch_ohlc(symbol, "1d", limit=60)
    closes = [float(c["close"]) for c in candles if c.get("close") is not None]

    if len(closes) < 30:
        return "EXHAUSTION"

    # Simple range expansion / contraction proxy
    recent = closes[-10:]
    previous = closes[-20:-10]

    recent_range = max(recent) - min(recent)
    previous_range = max(previous) - min(previous)

    if regime == "TREND" and recent_range > previous_range:
        return "IMPULSE"

    if regime == "TREND" and recent_range <= previous_range:
        return "PULLBACK"

    if regime == "RANGE":
        return "EXHAUSTION"

    return "EXHAUSTION"
