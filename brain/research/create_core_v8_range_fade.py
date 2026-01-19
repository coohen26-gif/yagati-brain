import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v8_range_fade.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v8 = {
        "strategy_id": "CORE_V8_RANGE_FADE",
        "status": "DRAFT",
        "created_at": now,
        "rules": {
            "market_regime": "RANGE_MEAN_REVERSION",
            "trend_filter": "EMA200_OPTIONAL",
            "setup": {
                "type": "RANGE_EXTREME_REJECTION",
                "require_wick_reject": True,
                "require_close_inside_range": True
            },
            "entry": {
                "type": "FADE_EXTREME",
                "mode": "COUNTER_TREND"
            },
            "stop_loss": "BEYOND_RANGE_EXTREME",
            "take_profit": {
                "type": "RANGE_MEAN",
                "target": "MID_RANGE"
            },
            "rr_min": {
                "exploration": 1.0,
                "live": 2.0
            }
        },
        "notes": "CORE V8 : Mean reversion / range fade. Test régime non directionnel."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v8, f, indent=2)

    print("✅ CORE V8 RANGE FADE strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
