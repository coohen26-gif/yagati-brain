import json
from collections import defaultdict

INPUT_FILE = "brain_analysis_step1.json"
OUTPUT_FILE = "strategy_evaluation.json"


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(x, hi))


def main():
    # Charger les décisions par signal
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        decisions = json.load(f)

    # Stats par stratégie
    stats = defaultdict(lambda: {
        "signals": 0,      # total signaux observés
        "keeps": 0,        # nombre de KEEP
        "rr_sum": 0.0,     # somme des RR valides
        "rr_valid": 0      # nombre de RR non-null
    })

    # Agrégation
    for d in decisions:
        rr = d.get("rr")
        decision = d.get("decision")
        sid = d.get("strategy_id")

        # On compte le signal quoi qu'il arrive
        stats[sid]["signals"] += 1

        # RR invalide ou signal ignoré → pas exploitable
        if rr is None or decision == "IGNORE":
            continue

        # RR valide
        stats[sid]["rr_valid"] += 1
        stats[sid]["rr_sum"] += rr

        if decision == "KEEP":
            stats[sid]["keeps"] += 1

    evaluation = {}

    # Évaluation finale par stratégie
    for sid, s in stats.items():
        signals = s["signals"]
        if signals == 0:
            continue

        rr_valid_rate = s["rr_valid"] / signals

        # Si aucune donnée exploitable, on skip
        if s["rr_valid"] == 0:
            continue

        keep_rate = s["keeps"] / s["rr_valid"]
        avg_rr = s["rr_sum"] / s["rr_valid"]

        # Expectancy proxy (en R)
        expectancy_r = keep_rate * (avg_rr - 1) - (1 - keep_rate)

        # Score brut
        raw_score = clamp(
            0.6 * keep_rate +
            0.4 * min(avg_rr / 4.0, 1.0)
        )

        # Pénalité qualité (RR null trop fréquent)
        quality_penalty = max(0.0, 0.5 - rr_valid_rate)

        # Score final
        score = clamp(
            raw_score - (0.3 * quality_penalty)
        )

        # Décision d'évolution
        if score >= 0.7:
            decision = "KEEP"
        elif score >= 0.4:
            decision = "ADJUST"
        else:
            decision = "KILL"

        evaluation[sid] = {
            "signals": signals,
            "rr_valid_rate": round(rr_valid_rate, 2),
            "keep_rate": round(keep_rate, 2),
            "avg_rr": round(avg_rr, 2),
            "expectancy_r": round(expectancy_r, 2),
            "score": round(score, 2),
            "decision": decision
        }

    # Sauvegarde
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)

    print("✅ Strategy evaluation completed")
    print(f"📁 {OUTPUT_FILE} written")


if __name__ == "__main__":
    main()

