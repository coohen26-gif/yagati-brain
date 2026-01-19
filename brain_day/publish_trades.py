import os
import json
import requests
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant")

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}

DATA_DIR = "/root/brain/data"
OPEN_TRADES_FILE = os.path.join(DATA_DIR, "open_trades.json")
CLOSED_TRADES_FILE = os.path.join(DATA_DIR, "closed_trades.json")


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def upsert(table, rows):
    if not rows:
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(
        url,
        headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
        json=rows,
        timeout=20,
    )
    r.raise_for_status()


def publish_open_trades():
    data = load_json(OPEN_TRADES_FILE)
    rows = []

    for trade_id, t in data.items():
        rows.append({
            "trade_id": trade_id,
            "symbol": t.get("symbol"),
            "direction": t.get("direction"),
            "entry_price": t.get("entry_price"),
            "stop_loss": t.get("stop_loss"),
            "tp1": t.get("tp1"),
            "tp2": t.get("tp2"),
            "state": t.get("state"),
            "opened_at": t.get("opened_at"),
            "updated_at": datetime.utcnow().isoformat(),
        })

    upsert("open_trades", rows)


def publish_closed_trades():
    data = load_json(CLOSED_TRADES_FILE)
    rows = []

    for trade_id, t in data.items():
        rows.append({
            "trade_id": trade_id,
            "symbol": t.get("symbol"),
            "direction": t.get("direction"),
            "entry_price": t.get("entry_price"),
            "exit_price": t.get("exit_price"),
            "stop_loss": t.get("stop_loss"),
            "tp1": t.get("tp1"),
            "tp2": t.get("tp2"),
            "realized_r": t.get("realized_r"),
            "state": t.get("state"),
            "opened_at": t.get("opened_at"),
            "closed_at": t.get("closed_at"),
            "updated_at": datetime.utcnow().isoformat(),
        })

    upsert("closed_trades", rows)


def main():
    publish_open_trades()
    publish_closed_trades()
    print("✅ Trades published to Supabase")


if __name__ == "__main__":
    main()
