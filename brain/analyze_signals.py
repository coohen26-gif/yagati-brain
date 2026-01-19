import os
import json
import requests
from datetime import datetime, timezone

from market_regime import detect_regime
from brain_core.trade_model import TradeModel
from brain_core.trade_state_types import TradeDirection, TradeState
from brain_core.position_manager import PositionManager
from brain_core.trade_repository import TradeRepository

# =====================================================
# CONFIG
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}

BASE_DIR = os.path.dirname(__file__)
LAST_RUN_FILE = os.path.join(BASE_DIR, "last_run.txt")
STEP1_FILE = os.path.join(BASE_DIR, "brain_analysis_step1.json")

MAX_OPEN_POSITIONS_TOTAL = 3
MAX_OPEN_POSITIONS_PER_SYMBOL = 1

STRATEGY_ID = "EMA200_CONTINUATION_AGGRESSIVE_V1"

# =====================================================
# CORE
# =====================================================

positions = PositionManager()
repo = TradeRepository()

# =====================================================
# UTILS
# =====================================================

def normalize_direction(d):
    if not d:
        return None
    d = d.lower()
    if d == "long":
        return TradeDirection.LONG
    if d == "short":
        return TradeDirection.SHORT
    return None

def load_last_run():
    if not os.path.exists(LAST_RUN_FILE):
        return None
    with open(LAST_RUN_FILE, "r", encoding="utf-8") as f:
        raw = f.read().strip()
        return datetime.fromisoformat(raw) if raw else None

def save_last_run(dt):
    with open(LAST_RUN_FILE, "w", encoding="utf-8") as f:
        f.write(dt.isoformat())

def fetch_signals():
    r = requests.get(
        f"{SUPABASE_URL}/functions/v1/brain-signals?limit=5",
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("signals", [])

def can_open(symbol):
    if positions.count_open() >= MAX_OPEN_POSITIONS_TOTAL:
        return False
    by_symbol = positions.get_open_by_symbol() or {}
    return by_symbol.get(symbol, 0) < MAX_OPEN_POSITIONS_PER_SYMBOL

def write_step1(items):
    with open(STEP1_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def compute_rr(entry, stop, tp):
    try:
        if entry is None or stop is None or tp is None:
            return None
        entry = float(entry)
        stop = float(stop)
        tp = float(tp)
        if entry == stop:
            return None
        # rr for LONG: (tp - entry) / (entry - stop) ; for SHORT symmetric with signs removed
        return round(abs((tp - entry) / (entry - stop)), 2)
    except Exception:
        return None

# =====================================================
# MAIN
# =====================================================

def main():
    print("🧠 Brain — V0 HARD PROOF (canonical TradeModel)")

    last_run = load_last_run()
    now = datetime.now(timezone.utc)

    # Le régime BTC est observé mais NON bloquant pour la preuve
    detect_regime("BTC")

    opened = []

    for s in fetch_signals():
        created_at = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
        if last_run and created_at <= last_run:
            continue

        direction = normalize_direction(s.get("direction"))
        if direction is None:
            continue

        symbol = s.get("symbol")
        if not symbol or not can_open(symbol):
            continue

        trade = TradeModel(
            trade_id=f"proof_{s['id']}",
            symbol=symbol,
            direction=direction,
            entry_price=s.get("entry_price"),
            stop_loss=s.get("stop_loss"),
            tp1=s.get("tp1"),
            tp2=s.get("tp2"),
            state=TradeState.POSITION_OPEN,
        )

        positions.open_position(trade)
        repo.save_open(trade)

        rr = compute_rr(s.get("entry_price"), s.get("stop_loss"), s.get("tp1"))

        # SWING-compatible output (minimal required fields)
        opened.append({
            "strategy_id": STRATEGY_ID,
            "decision": "KEEP",  # trade was opened -> KEEP
            "symbol": symbol,
            "direction": direction.value,
            "rr": rr,
            "created_at": created_at.isoformat(),
        })

    save_last_run(now)
    write_step1(opened)

    print(f"✅ DONE — {len(opened)} trades opened")
    if opened:
        print("📌 Opened trades:", opened)

if __name__ == "__main__":
    main()
