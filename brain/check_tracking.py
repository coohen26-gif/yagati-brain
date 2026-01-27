import requests
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not ANON_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

HEADERS = {
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

r = requests.get(
    f"{SUPABASE_URL}/functions/v1/brain-signals?limit=50",
    headers=HEADERS
)

r.raise_for_status()
signals = r.json()["signals"]

print(f"Signals récupérés : {len(signals)}\n")

for s in signals[:10]:
    print(
        s["symbol"],
        "| status:", s["signal_status"],
        "| outcome:", s["outcome"],
        "| TP1:", s["hit_tp1"],
        "| TP2:", s["hit_tp2"],
        "| SL:", s["hit_stop_loss"]
    )
