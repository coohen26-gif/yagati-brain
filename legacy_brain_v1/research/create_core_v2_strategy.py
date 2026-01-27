import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v2_tight_zone.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v2 = {
        "strategy_id": "CORE_V2_TIGHT_ZONE",
        "status": "DRAFT",
        "created_at": now,
        "rules": {
            "trend_filter": "EMA200_ONLY",
            "zone_type": "LIQUIDITY_STRONG_ONLY",
            "entry": {
                "type": "INSIDE_ZONE_TIGHT",
                "percent_of_zone": 0.30
            },
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
        "notes": "CORE V2 : entrée resserrée dans le dernier 30% de la zone pour améliorer RR."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v2, f, indent=2)

    print("✅ CORE V2 TIGHT ZONE strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
