import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v7_delayed_entry.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v7 = {
        "strategy_id": "CORE_V7_DELAYED_ENTRY",
        "status": "DRAFT",
        "created_at": now,
        "rules": {
            "trend_filter": "EMA200_ONLY",
            "setup": {
                "type": "BREAKOUT_STRUCTURE",
                "confirm_timeframe": "1H",
                "require_close_break": True
            },
            "entry": {
                "type": "DELAYED_CONFIRM_ENTRY",
                "mode": "PULLBACK_ONLY",
                "confirm_timeframe": "15m",
                "require_second_close": True,
                "require_pullback_touch": True
            },
            "stop_loss": "BELOW_BROKEN_STRUCTURE",
            "take_profit": {
                "type": "FIXED_R",
                "r_multiple": 3.0
            },
            "rr_min": {
                "exploration": 1.5,
                "live": 3.0
            }
        },
        "notes": "CORE V7 : entrée retardée + pullback confirmé (évite les entrées trop tôt)."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v7, f, indent=2)

    print("✅ CORE V7 DELAYED ENTRY strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
