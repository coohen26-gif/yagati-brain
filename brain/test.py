import json
import requests

# REMPLIS ICI (localement)
SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpodGZ1cXBuZ2dtYmxzZGZ0bHJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5NDQxNzQsImV4cCI6MjA4MzUyMDE3NH0.hhdYOKXQJ4A9oADhuljNICDgABdu8jW54jfkXzidWdY"

# Charger la décision validée
with open("brain_decisions_validated.json", "r", encoding="utf-8") as f:
    validated = json.load(f)

decision = validated[0]

payload = {
    "strategy_id": decision["strategy_id"],
    "action": decision["action"],
    "reason": decision["reason"],
    "metadata": decision["metrics"]
}

headers = {
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

resp = requests.post(
    f"{SUPABASE_URL}/functions/v1/brain-log",
    json=payload,
    headers=headers
)

print("Status code :", resp.status_code)
print("Response :", resp.text)
