import json
from datetime import datetime

OUTPUT_FILE = "core_strategy_v5_breakout.json"

def main():
    now = datetime.utcnow().isoformat()

    core_v5 = {
        "strategy_id": "CORE_V5_BREAKOUT",
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
                "r_multiple": 3.0
            },
            "rr_min": {
                "exploration": 1.5,
                "live": 3.0
            }
        },
        "notes": "CORE V5 : changement de régime. Test breakout/structure plutôt que zone rejection."
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(core_v5, f, indent=2)

    print("✅ CORE V5 BREAKOUT strategy created")
    print(f"📁 {OUTPUT_FILE} written")

if __name__ == "__main__":
    main()
