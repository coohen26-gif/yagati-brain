"""
RUN SCORE SNAPSHOT — YAGATI (ENGINE ONLY)

Charge les diagnostics DAY existants depuis des fichiers locaux,
calcule les scores par stratégie et écrit des snapshots JSON.

Aucune automatisation.
Aucune dépendance externe.
"""

import json
import os
from collections import defaultdict
from typing import Dict, Any, List

from engine.scoring.canonical_scoring import score_strategy_day


# =====================================================
# CONFIG
# =====================================================

BASE_DIR = os.path.dirname(__file__)

# Adapter si besoin à l’emplacement réel des diagnostics
DAY_DIAGNOSTICS_FILE = os.path.join(
    BASE_DIR, "..", "..", "brain_day", "diagnostics.json"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "..", "..", "engine_outputs")
OUTPUT_DAY_FILE = os.path.join(OUTPUT_DIR, "strategy_scores_day.json")


# =====================================================
# UTILS
# =====================================================

def load_json(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        print(f"[WARN] File not found: {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return []


# =====================================================
# MAIN
# =====================================================

def main() -> None:
    diagnostics = load_json(DAY_DIAGNOSTICS_FILE)

    by_strategy: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in diagnostics:
        sid = row.get("strategy_id")
        if sid:
            by_strategy[sid].append(row)

    scores = []
    for sid, rows in by_strategy.items():
        score = score_strategy_day(rows)
        scores.append(score.to_dict())

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(OUTPUT_DAY_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    print(f"[OK] Wrote {len(scores)} strategy scores to {OUTPUT_DAY_FILE}")


if __name__ == "__main__":
    main()
