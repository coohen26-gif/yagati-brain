import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v6_breakout_tp4.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v6 = {
        "strategy_id": "CORE_V6_BREAKOUT_TP4",
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
                "type": "BREAKOUT_PULLBACK_OR_CONTINUATION",
                "allow_pullback": True,
                "allow_continuation": True
            },
            "stop_loss": "BELOW_BROKEN_STRUCTURE",
            "take_profit": {
                "type": "FIXED_R",
                "r_multiple": 4.0
            },
            "rr_min": {
                "exploration": 1.5,
                "live": 3.0
            }
        },
        "notes": "CORE V6 : même breakout que V5, TP étendu à 4R pour augmenter le RR."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v6, f, indent=2)

    print("✅ CORE V6 BREAKOUT TP4 strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
