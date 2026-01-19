import requests

SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpodGZ1cXBuZ2dtYmxzZGZ0bHJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5NDQxNzQsImV4cCI6MjA4MzUyMDE3NH0.hhdYOKXQJ4A9oADhuljNICDgABdu8jW54jfkXzidWdY"

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
