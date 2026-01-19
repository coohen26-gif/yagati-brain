import os
import sys
import json
import re
import requests
from collections import defaultdict
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not ANON_KEY:
    print("SUPABASE_URL or SUPABASE_ANON_KEY not set — skipping Supabase send.")
    sys.exit(0)

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
    except Exception:
        return {}

trades = []
try:
    with open(ANALYSIS_FILE, "r", encoding="utf-8") as f:
        trades = json.load(f) or []
except Exception:
    trades = []

if not isinstance(trades, list):
    trades = [trades]

by_strategy = defaultdict(list)
for t in trades:
    sid = t.get("strategy_id")
    if sid:
        by_strategy[sid].append(t)

print(f"Brain detected {len(by_strategy)} strategy_id groups")
if not by_strategy:
    print("No strategies detected — nothing to send. Exiting.")
    sys.exit(0)

def decide_strategy(trades_):
    kills = sum(1 for t in trades_ if t.get("decision") == "KILL")
    keeps = sum(1 for t in trades_ if t.get("decision") == "KEEP")
    adjusts = sum(1 for t in trades_ if t.get("decision") == "ADJUST")
    total = len(trades_) if trades_ else 1

    if kills / total > 0.6:
        return "ADJUST_REJECTED", "too many kills"
    if keeps / total > 0.6:
        return "KEEP", "mostly keeps"
    return "ADJUST", "mixed results"

for strategy_id, items in by_strategy.items():
    action, reason = decide_strategy(items)
    payload = {
        "strategy_id": strategy_id,
        "action": action,
        "reason": reason,
        "metadata": {
            "ts": utc_now(),
            "trades_analyzed": len(items)
        }
    }
    r = requests.post(
        f"{SUPABASE_URL}/functions/v1/brain-log",
        headers=HEADERS,
        json=payload
    )
    print(strategy_id, r.status_code)
