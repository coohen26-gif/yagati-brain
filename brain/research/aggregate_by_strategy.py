import json
from collections import defaultdict

INPUT_FILE = "brain_analysis_step1.json"
OUTPUT_FILE = "brain_strategy_decisions.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        decisions = json.load(f)

    stats = defaultdict(lambda: {
        "count": 0,
        "rr_sum": 0.0
    })

    for d in decisions:
        rr = d.get("rr")
        decision = d.get("decision")
        strategy_id = d.get("strategy_id")

        if decision == "IGNORE" or rr is None:
            continue

        stats[strategy_id]["count"] += 1
        stats[strategy_id]["rr_sum"] += rr

    strategy_decisions = []

    for strategy_id, s in stats.items():
        count = s["count"]
        if count == 0:
            continue

        avg_rr = s["rr_sum"] / count

        if avg_rr >= 3:
            action = "KEEP"
        elif avg_rr >= 1.5:
            action = "ADJUST"
        else:
            action = "FREEZE"

        strategy_decisions.append({
            "strategy_id": strategy_id,
            "signals": count,
            "avg_rr": round(avg_rr, 2),
            "action": action
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(strategy_decisions, f, indent=2)

    print("✅ Strategy governance updated")
    print(f"📁 {OUTPUT_FILE} written")


if __name__ == "__main__":
    main()
