import json
import os
from datetime import datetime, timezone

REGISTRY_FILE = "strategies_registry.json"
EVAL_FILE = "strategy_evaluation.json"
ACTIONS_FILE = "autopilot_actions.json"
MUTATIONS_FILE = "autopilot_mutations.json"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def decide_from_score(score, gov):
    if score <= gov["kill_threshold"]:
        return "KILL"
    if score < gov["adjust_threshold"]:
        return "KILL"
    if score < gov["keep_threshold"]:
        return "ADJUST"
    return "KEEP"

# Mutations autorisées par concept (fermées)
MUTATIONS = {
    "DELAYED_ENTRY": [
        {"name": "confirm_tf_30m", "field": "confirm_timeframe", "value": "30m"},
        {"name": "tp_2_5R", "field": "tp_r", "value": 2.5},
    ],
    "BREAKOUT": [
        {"name": "confirm_tf_4h", "field": "confirm_timeframe", "value": "4H"},
        {"name": "tp_4R", "field": "tp_r", "value": 4.0},
    ],
    "UNKNOWN": [
        {"name": "tp_2_5R", "field": "tp_r", "value": 2.5},
    ]
}

def next_mutation(concept, last_mutation_name):
    pool = MUTATIONS.get(concept, MUTATIONS["UNKNOWN"])
    if not last_mutation_name:
        return pool[0]
    # rotation
    for i, m in enumerate(pool):
        if m["name"] == last_mutation_name:
            return pool[(i + 1) % len(pool)]
    return pool[0]

def main():
    registry = load_json(REGISTRY_FILE, {})
    evaluation = load_json(EVAL_FILE, {})

    gov = registry.get("governance", {})
    if not gov:
        raise RuntimeError("Registry governance missing")

    actions = {
        "generated_at": utc_now(),
        "summary": {},
        "actions": []
    }

    mutations = {
        "generated_at": utc_now(),
        "mutations": []
    }

    if not evaluation:
        actions["summary"] = {"status": "NO_EVALUATION", "message": "strategy_evaluation.json is empty"}
        save_json(ACTIONS_FILE, actions)
        save_json(MUTATIONS_FILE, mutations)
        print("ℹ️ Autopilot V2: no evaluation data yet")
        return

    # 1) Décisions (KEEP / ADJUST / KILL / FREEZE)
    for sid, stats in evaluation.items():
        signals = stats.get("signals", 0)
        score = stats.get("score", 0.0)
        decision = decide_from_score(score, gov)

        if signals < gov["min_signals_for_eval"]:
            decision = "FREEZE"

        actions["actions"].append({
            "strategy_id": sid,
            "signals": signals,
            "score": score,
            "decision": decision,
            "reason": "autopilot_v2_governance"
        })

        strat = registry.get("strategies", {}).get(sid)
        if strat is None:
            registry.setdefault("strategies", {})[sid] = {
                "concept": "UNKNOWN",
                "status": "TEST",
                "direction": "BOTH",
                "version": None,
                "parent": None,
                "notes": "Discovered by autopilot",
                "last_mutation": None
            }
            strat = registry["strategies"][sid]

        # Apply status updates (no LIVE promotion)
        if decision == "KILL":
            strat["status"] = "ARCHIVED"
        elif decision == "ADJUST":
            strat["status"] = "TEST"
        elif decision == "KEEP":
            strat["status"] = "TEST"
        elif decision == "FREEZE":
            strat["status"] = "FREEZE"

    # 2) Mutation contrôlée: choisir 1 stratégie ADJUST max
    mutation_target = None
    for a in actions["actions"]:
        if a["decision"] == "ADJUST":
            mutation_target = a["strategy_id"]
            break

    if mutation_target:
        strat = registry["strategies"].get(mutation_target, {})
        concept = strat.get("concept", "UNKNOWN")
        last_mut = strat.get("last_mutation")
        m = next_mutation(concept, last_mut)

        # New ID versioning (simple)
        new_id = f"{mutation_target}__{m['name']}"

        mutations["mutations"].append({
            "base_strategy_id": mutation_target,
            "new_strategy_id": new_id,
            "concept": concept,
            "mutation": m,
            "status": "DRAFT",
            "note": "Proposed by autopilot_v2"
        })

        strat["last_mutation"] = m["name"]
        strat["status"] = "TEST"

        # Register the new strategy (DRAFT)
        registry["strategies"][new_id] = {
            "concept": concept,
            "status": "DRAFT",
            "direction": strat.get("direction", "BOTH"),
            "version": None,
            "parent": mutation_target,
            "notes": f"Auto-mutation: {m['name']}",
            "last_mutation": None
        }

    registry["last_updated"] = utc_now()

    # Summary
    counts = {}
    for a in actions["actions"]:
        counts[a["decision"]] = counts.get(a["decision"], 0) + 1

    actions["summary"] = {
        "status": "OK",
        "counts": counts,
        "note": "No LIVE promotion; max 1 mutation proposal per run"
    }

    save_json(REGISTRY_FILE, registry)
    save_json(ACTIONS_FILE, actions)
    save_json(MUTATIONS_FILE, mutations)

    print("✅ Autopilot V2 ran")
    print(f"📁 Updated: {REGISTRY_FILE}")
    print(f"📁 Written: {ACTIONS_FILE}")
    print(f"📁 Written: {MUTATIONS_FILE}")

if __name__ == "__main__":
    main()
