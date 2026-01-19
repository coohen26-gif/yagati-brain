import json
import os
from datetime import datetime, timezone

REGISTRY_FILE = "strategies_registry.json"
EVAL_FILE = "strategy_evaluation.json"
PLAN_FILE = "autopilot_v3_plan.json"

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

def main():
    registry = load_json(REGISTRY_FILE, {})
    evaluation = load_json(EVAL_FILE, {})

    gov = registry.get("governance", {})
    if not gov:
        raise RuntimeError("Registry governance missing")

    plan = {
        "generated_at": utc_now(),
        "status": "OK",
        "decisions": [],
        "new_strategy_created": None,
        "note": "V3 creates a new concept when all evaluated strategies are KILL/FREEZE."
    }

    # If no evaluation, do nothing
    if not evaluation:
        plan["status"] = "NO_EVALUATION"
        plan["note"] = "strategy_evaluation.json empty"
        save_json(PLAN_FILE, plan)
        print("ℹ️ Autopilot V3: no evaluation")
        return

    # Check if we have any ADJUST/KEEP candidate
    has_candidate = False
    for sid, s in evaluation.items():
        decision = s.get("decision")
        if decision in ("ADJUST", "KEEP"):
            has_candidate = True
            break

    if has_candidate:
        plan["status"] = "NO_NEW_CONCEPT"
        plan["note"] = "At least one strategy is ADJUST/KEEP; V3 does not introduce a new concept."
        save_json(PLAN_FILE, plan)
        print("ℹ️ Autopilot V3: candidate exists; no new concept created")
        return

    # Otherwise, introduce a new concept: RANGE_FADE
    new_id = "CORE_V8_RANGE_FADE"

    registry.setdefault("strategies", {})
    if new_id not in registry["strategies"]:
        registry["strategies"][new_id] = {
            "concept": "RANGE_FADE",
            "status": "DRAFT",
            "direction": "BOTH",
            "version": 8,
            "parent": None,
            "notes": "Auto-introduced concept: mean reversion / range fade",
            "last_mutation": None
        }

    # Add concept to active_concepts if not present
    registry.setdefault("active_concepts", [])
    if "RANGE_FADE" not in registry["active_concepts"]:
        registry["active_concepts"].append("RANGE_FADE")

    registry["last_updated"] = utc_now()

    plan["new_strategy_created"] = {
        "strategy_id": new_id,
        "concept": "RANGE_FADE",
        "status": "DRAFT",
        "intent": "Test mean reversion regime when trend/breakout concepts fail."
    }

    plan["decisions"].append({
        "action": "CREATE_DRAFT_STRATEGY",
        "strategy_id": new_id,
        "reason": "All evaluated strategies are KILL/FREEZE; switching concept."
    })

    save_json(REGISTRY_FILE, registry)
    save_json(PLAN_FILE, plan)

    print("✅ Autopilot V3 ran")
    print(f"📁 Updated: {REGISTRY_FILE}")
    print(f"📁 Written: {PLAN_FILE}")

if __name__ == "__main__":
    main()
