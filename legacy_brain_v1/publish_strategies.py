import json
import os
import requests

# =============================
# CONFIG
# =============================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}

REGISTRY_FILE = "strategies_registry.json"

# =============================
# HELPERS
# =============================

def map_direction(direction):
    if direction == "BOTH":
        return "all"
    if direction == "LONG":
        return "long_only"
    if direction == "SHORT":
        return "short_only"
    return "all"

def map_profile_level(concept):
    """
    Mapping concept -> profile_level attendu par l'UI
    """
    if concept == "SAFE":
        return 5.0
    if concept == "INTER":
        return 4.0
    if concept == "DYNAMIC":
        return 3.0
    if concept == "JOKER":
        return None

    # Concepts techniques
    if concept in ["RANGE_FADE", "TREND_PULLBACK", "TREND_BREAKDOWN", "BREAKOUT", "DELAYED_ENTRY"]:
        return 4.0  # INTER par défaut

    return None  # fallback JOKER

def load_and_transform_registry():
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    strategies_array = []

    for key, data in raw["strategies"].items():
        entry = {
            "key": key,
            "name": data["name"],
            "concept": data.get("concept"),
            "status": data.get("status"),
            "version": data.get("version"),
            "notes": data.get("notes"),
            "trading_horizon": "SWING",
            "direction": map_direction(data.get("direction", "BOTH")),
            "profile_level": map_profile_level(data.get("concept"))
        }
        strategies_array.append(entry)

    return {
        "version": raw.get("version"),
        "last_updated": raw.get("last_updated"),
        "strategies": strategies_array
    }

# =============================
# MAIN
# =============================

def main():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY missing")

    registry = load_and_transform_registry()

    payload = {
        "action": "sync",
        "registry": registry
    }

    url = f"{SUPABASE_URL}/functions/v1/brain-publish-strategies"

    print("📡 Publishing Brain strategies to Supabase...")
    r = requests.post(url, headers=HEADERS, json=payload, timeout=20)

    if r.status_code != 200:
        print("❌ Sync failed")
        print(r.status_code, r.text)
        return

    print("✅ Sync successful")
    print(json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    main()
