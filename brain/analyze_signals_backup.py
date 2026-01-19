import requests
import json
from math import fabs
from datetime import datetime, timezone
import os

# =========================
# CONFIG
# =========================
SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpodGZ1cXBuZ2dtYmxzZGZ0bHJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5NDQxNzQsImV4cCI6MjA4MzUyMDE3NH0.hhdYOKXQJ4A9oADhuljNICDgABdu8jW54jfkXzidWdY"

LAST_RUN_FILE = "last_run.txt"

HEADERS = {
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

# =========================
# LOAD LAST RUN TIME
# =========================
def load_last_run():
    if not os.path.exists(LAST_RUN_FILE):
        return None
    with open(LAST_RUN_FILE, "r") as f:
        return datetime.fromisoformat(f.read().strip())

def save_last_run(dt):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(dt.isoformat())

# =========================
# FETCH SIGNALS
# =========================
def fetch_signals():
    url = f"{SUPABASE_URL}/functions/v1/brain-signals?limit=500"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()["signals"]

# =========================
# RR CALCULATION
# =========================
def compute_rr(signal):
    entry = signal["entry_price"]
    sl = signal["stop_loss"]
    tp2 = signal["tp2"]

    if not entry or not sl or not tp2:
        return None

    risk = fabs(entry - sl)
    reward = fabs(tp2 - entry)

    if risk == 0:
        return None

    return round(reward / risk, 2)

# =========================
# DECISION LOGIC (V1)
# =========================
def decide(rr):
    if rr is None:
        return "KILL"
    if rr >= 3:
        return "KEEP"
    if rr >= 1.5:
        return "ADJUST"
    return "KILL"

# =========================
# MAIN
# =========================
def main():
    print("🧠 Analyse des NOUVEAUX signaux uniquement")

    last_run = load_last_run()
    now = datetime.now(timezone.utc)

    signals = fetch_signals()

    new_signals = []
    for s in signals:
        created_at = datetime.fromisoformat(
            s["created_at"].replace("Z", "+00:00")
        )
        if last_run is None or created_at > last_run:
            new_signals.append(s)

    print(f"➡️ Signaux reçus : {len(signals)}")
    print(f"🆕 Nouveaux signaux analysés : {len(new_signals)}")

    decisions = []

    for s in new_signals:
        rr = compute_rr(s)
        decision = decide(rr)

        decisions.append({
            "signal_id": s["id"],
            "strategy_id": s.get("strategy_id"),
            "symbol": s["symbol"],
            "direction": s["direction"],
            "rr": rr,
            "decision": decision,
            "created_at": s["created_at"]
        })

        print(
            f"{s['symbol']} | {s['direction'].upper()} | "
            f"RR={rr} → {decision}"
        )

    with open("brain_analysis_step1.json", "w", encoding="utf-8") as f:
        json.dump(decisions, f, indent=2)

    save_last_run(now)

    print("\n✅ Analyse terminée")
    print("📁 brain_analysis_step1.json mis à jour")
    print("🕒 Dernière exécution enregistrée")

if __name__ == "__main__":
    main()
