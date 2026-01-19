import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v3_timing_confirmation.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v3 = {
        "strategy_id": "CORE_V3_TIMING_CONFIRM",
        "status": "DRAFT",
        "created_at": now,
        "rules": {
            "trend_filter": "EMA200_ONLY",
            "zone_type": "LIQUIDITY_STRONG_ONLY",
            "entry": {
                "type": "ZONE_REJECTION_CONFIRM",
                "timeframe": ["5m", "15m"],
                "require_close_reject": True,
                "require_wick_reject": True
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
        "notes": "CORE V3 : ajout d'une confirmation timing (rejection) pour filtrer le bruit."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v3, f, indent=2)

    print("✅ CORE V3 TIMING strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
