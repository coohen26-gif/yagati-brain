import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v1.json"

def main():
    now = datetime.utcnow().isoformat()

    core_strategy = {
        "strategy_id": "CORE_V1_TREND_ZONE",
        "status": "DRAFT",
        "created_at": now,
        "rules": {
            "trend_filter": "EMA200_ONLY",
            "zone_type": "LIQUIDITY_STRONG_ONLY",
            "entry": "INSIDE_ZONE",
            "stop_loss": "OPPOSITE_ZONE_EDGE",
            "take_profit": {
                "type": "FIXED_R",
                "r_multiple": 2.0
            },
            "rr_min": {
                "exploration": 1.0,
                "live": 2.5
            }
        },
        "notes": "Core simple pour apprentissage. Base saine, peu de règles."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_strategy, f, indent=2)

    print("✅ CORE V1 strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
