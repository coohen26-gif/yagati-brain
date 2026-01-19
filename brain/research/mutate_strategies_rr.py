import json
import copy
from datetime import datetime

# Entrées / sorties
EVALUATION_FILE = "strategy_evaluation.json"
OUTPUT_FILE = "strategies_mutations.json"

# Mutation contrôlée
BASE_RR = 3.0
MUTATED_RR = 2.5
SUFFIX = "_RR25"


def main():
    # Charger l'évaluation
    with open(EVALUATION_FILE, "r", encoding="utf-8") as f:
        evaluation = json.load(f)

    mutations = []
    now = datetime.utcnow().isoformat()

    # Si aucune stratégie évaluée, on prépare quand même la structure
    if not evaluation:
        print("ℹ️ Aucune stratégie à muter (évaluation vide)")
    else:
        for sid, data in evaluation.items():
            decision = data.get("decision")

            # On mute uniquement les stratégies non KEEP
            if decision not in ("ADJUST", "KILL"):
                continue

            mutated_id = f"{sid}{SUFFIX}"

            mutation = {
                "base_strategy_id": sid,
                "mutated_strategy_id": mutated_id,
                "mutation": {
                    "parameter": "rr_min",
                    "from": BASE_RR,
                    "to": MUTATED_RR
                },
                "status": "DRAFT",
                "created_at": now
            }

            mutations.append(mutation)

    # Sauvegarde
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mutations, f, indent=2)

    print("🧬 Mutation RR completed")
    print(f"📁 {OUTPUT_FILE} written ({len(mutations)} mutations)")


if __name__ == "__main__":
    main()
