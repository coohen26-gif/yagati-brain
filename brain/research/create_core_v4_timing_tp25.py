import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v4_timing_tp25.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v4 = {
        "strategy_id": "CORE_V4_TIMING_TP25",
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
                "r_multiple": 2.5
            },
            "rr_min": {
                "exploration": 1.0,
                "live": 2.5
            }
        },
        "notes": "CORE V4 : même timing que V3, TP étendu à 2.5R pour augmenter le RR."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v4, f, indent=2)

    print("✅ CORE V4 TIMING TP25 strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
