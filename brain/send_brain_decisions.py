import json
import requests

# ===== CONFIG =====
SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpodGZ1cXBuZ2dtYmxzZGZ0bHJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5NDQxNzQsImV4cCI6MjA4MzUyMDE3NH0.hhdYOKXQJ4A9oADhuljNICDgABdu8jW54jfkXzidWdY"

HEADERS = {
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

# ===== LOAD DECISIONS =====
with open("strategy_scores.json", "r", encoding="utf-8") as f:
    strategy_decisions = json.load(f)

print(f"🧠 Envoi de {len(strategy_decisions)} décisions (1 par stratégie)\n")

success = 0
errors = 0

for d in strategy_decisions:
    action = d["decision"]

    # Mapping compatible Supabase
    if action == "FREEZE":
        action = "ADJUST_REJECTED"
    elif action == "IGNORE":
        continue

    payload = {
        "strategy_id": d["strategy_id"],
        "action": action,
        "metadata": {
            "score": d["score"],
            "source": "Python Brain V1.3",
            "reason": "Score-based strategy decision"
        }
    }

    try:
        r = requests.post(
            f"{SUPABASE_URL}/functions/v1/brain-log",
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        if r.status_code == 200:
            print(f"✅ STRATEGY {d['strategy_id'][:8]} → {action}")
            success += 1
        else:
            print(f"❌ STRATEGY {d['strategy_id'][:8]} → ERREUR {r.status_code}")
            errors += 1

    except Exception as e:
        print(f"🔥 STRATEGY {d['strategy_id'][:8]} → EXCEPTION {e}")
        errors += 1

print("\n📊 RÉSUMÉ")
print(f"✔️ Succès : {success}")
print(f"❌ Erreurs : {errors}")
