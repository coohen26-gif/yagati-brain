import json
import re
import requests
from collections import defaultdict
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================
SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

HEADERS = {
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

ANALYSIS_FILE = "brain_analysis_step1.json"
REGISTRY_FILE = "strategies_registry.json"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)

SWING_STRATEGY_ID = "EMA200_CONTINUATION_AGGRESSIVE_V1"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def classify_strategy_id(sid: str) -> str:
    if not sid:
        return "UNKNOWN"
    s = sid.strip()
    if s.startswith("CORE_"):
        return "BRAIN_KEY"
    if UUID_RE.match(s):
        return "UUID"
    return "UNKNOWN"

def load_registry():
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            reg = json.load(f)
        return reg if isinstance(reg, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def get_registry_info(registry: dict, brain_key: str):
    """
    Retourne (brain_version, brain_status, concept, direction, parent) si disponible.
    """
    strategies = registry.get("strategies", {}) if isinstance(registry, dict) else {}
    s = strategies.get(brain_key)
    if not isinstance(s, dict):
        return None

    return {
        "brain_strategy_key": brain_key,
        "brain_version": s.get("version"),
        "brain_status": s.get("status"),
        "concept": s.get("concept"),
        "direction": s.get("direction"),
        "parent": s.get("parent"),
    }

# =========================
# LOAD ANALYSIS
# =========================
trades = []
try:
    with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        trades = data if data is not None else []
except FileNotFoundError:
    trades = []
except Exception as e:
    print("Failed to read analysis file:", e)
    trades = []

# Ensure trades is a list
if not isinstance(trades, list):
    trades = [trades]

# =========================
# GROUP BY STRATEGY
# =========================
by_strategy = defaultdict(list)
for t in trades:
    sid = t.get("strategy_id")
    if sid:
        by_strategy[sid].append(t)

print(f"Brain detected {len(by_strategy)} strategy_id groups")
if not trades:
    print("🧠 Brain run OK — no new signals to analyze")

# =========================
# DECISION LOGIC
# =========================
def decide_strategy(trades_):
    kills = sum(1 for t in trades_ if t.get("decision") == "KILL")
    keeps = sum(1 for t in trades_ if t.get("decision") == "KEEP")
    adjusts = sum(1 for t in trades_ if t.get("decision") == "ADJUST")
    total = len(trades_) if trades_ else 1

    if kills / total > 0.6:
        return "ADJUST_REJECTED", f"{kills}/{total} trades négatifs"
    if keeps / total > 0.6:
        return "KEEP", f"{keeps}/{total} trades positifs"
    return "ADJUST", f"Résultats mixtes ({keeps} KEEP / {kills} KILL / {adjusts} ADJUST)"

# =========================
# LOAD REGISTRY (optional)
# =========================
registry = load_registry()

# =========================
# SEND TO SUPABASE
# =========================
success = 0
errors = 0
skipped = 0

# Normal flow: send aggregated decisions per strategy
for strategy_id_raw, trades_ in by_strategy.items():
    action, reason = decide_strategy(trades_)

    sid_type = classify_strategy_id(strategy_id_raw)

    # Canonical info if it's already a Brain key
    registry_info = None
    if sid_type == "BRAIN_KEY":
        registry_info = get_registry_info(registry, strategy_id_raw)

    # We keep `strategy_id` as-is for backward compatibility.
    payload = {
        "strategy_id": strategy_id_raw,
        "action": action,
        "reason": reason,
        "metadata": {
            "ts": utc_now(),
            "trades_analyzed": len(trades_),
            "details": reason,
            "strategy_id_raw": strategy_id_raw,
            "strategy_id_type": sid_type,
            "brain_canonical": registry_info  # may be None; that's fine
        }
    }

    # Defensive: if strategy_id is empty (should not happen), skip
    if not strategy_id_raw:
        print("SKIP empty strategy_id")
        skipped += 1
        continue

    try:
        r = requests.post(
            f"{SUPABASE_URL}/functions/v1/brain-log",
            headers=HEADERS,
            json=payload
        )

        if r.status_code == 200:
            print(f"OK {strategy_id_raw} ({sid_type}) -> {action}")
            success += 1
        else:
            print(f"ERROR {strategy_id_raw} ({sid_type}) -> {r.status_code} {r.text}")
            errors += 1
    except Exception as e:
        print(f"ERROR {strategy_id_raw} request failed:", e)
        errors += 1

print("\nSUMMARY")
print(f"Success: {success}")
print(f"Errors: {errors}")
print(f"Skipped: {skipped}")
