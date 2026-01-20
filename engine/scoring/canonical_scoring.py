"""
CANONICAL STRATEGY SCORING — YAGATI (ENGINE ONLY)

Objectif
--------
Fournir un score unique, normalisé (0..100), comparable entre stratégies,
utilisable par :
- DAY arena (diagnostics ACCEPTED / REJECTED)
- SWING_ALPHA arena (realized_r si disponible)

Aucune dépendance externe.
Aucun lien UI / Supabase.
SWING_PROD strictement hors périmètre.

Principes
---------
- Score conservateur (protection faible échantillon)
- Stable (pas de volatilité excessive)
- Entièrement auditable (breakdown complet)

Formules
--------
DAY:
- Taux d'ACCEPTED
- Borne inférieure de Wilson (z=1.0)
- Score = wilson_lb * 100

SWING:
- Moyenne des realized_r
- Shrinkage vers 0 : n / (n + k), k=20
- Mapping borné via tanh
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math


# =====================================================
# DATA STRUCTURE
# =====================================================

@dataclass
class StrategyScoreBreakdown:
    strategy_id: str
    n_samples: int

    quality_score: Optional[float]
    quality_details: Dict[str, Any]

    performance_score: Optional[float]
    performance_details: Dict[str, Any]

    final_score: float
    weights: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =====================================================
# STATS
# =====================================================

def wilson_lower_bound(successes: int, n: int, z: float = 1.0) -> float:
    if n <= 0:
        return 0.0

    phat = successes / n
    denom = 1.0 + (z * z) / n
    centre = phat + (z * z) / (2 * n)
    margin = z * math.sqrt(
        (phat * (1 - phat) + (z * z) / (4 * n)) / n
    )

    return max(0.0, (centre - margin) / denom)


# =====================================================
# DAY SCORING
# =====================================================

def score_strategy_day(
    diagnostics_rows: List[Dict[str, Any]]
) -> StrategyScoreBreakdown:
    if not diagnostics_rows:
        return StrategyScoreBreakdown(
            strategy_id="UNKNOWN",
            n_samples=0,
            quality_score=0.0,
            quality_details={"reason": "no diagnostics"},
            performance_score=None,
            performance_details={},
            final_score=0.0,
            weights={"quality": 1.0, "performance": 0.0},
        )

    strategy_id = diagnostics_rows[0].get("strategy_id", "UNKNOWN")

    total = 0
    accepted = 0

    for row in diagnostics_rows:
        decision = row.get("final_decision")
        if decision not in ("ACCEPTED", "REJECTED"):
            continue
        total += 1
        if decision == "ACCEPTED":
            accepted += 1

    wilson_lb = wilson_lower_bound(accepted, total)
    score = round(wilson_lb * 100.0, 2)

    return StrategyScoreBreakdown(
        strategy_id=strategy_id,
        n_samples=total,
        quality_score=score,
        quality_details={
            "accepted": accepted,
            "total": total,
            "wilson_lower_bound": wilson_lb,
            "z": 1.0,
        },
        performance_score=None,
        performance_details={},
        final_score=score,
        weights={"quality": 1.0, "performance": 0.0},
    )


# =====================================================
# SWING SCORING
# =====================================================

def score_strategy_swing(
    trade_rows: List[Dict[str, Any]],
    strategy_id: str,
    k: float = 20.0,
) -> StrategyScoreBreakdown:
    realized_rs = [
        r.get("realized_r")
        for r in trade_rows
        if isinstance(r.get("realized_r"), (int, float))
    ]

    n = len(realized_rs)

    if n == 0:
        return StrategyScoreBreakdown(
            strategy_id=strategy_id,
            n_samples=0,
            quality_score=50.0,
            quality_details={"note": "no realized trades"},
            performance_score=None,
            performance_details={},
            final_score=50.0,
            weights={"quality": 1.0, "performance": 0.0},
        )

    mean_r = sum(realized_rs) / n
    shrink = n / (n + k)
    shrunk_r = mean_r * shrink

    perf_score = 50.0 + 50.0 * math.tanh(shrunk_r)
    perf_score = round(perf_score, 2)

    return StrategyScoreBreakdown(
        strategy_id=strategy_id,
        n_samples=n,
        quality_score=None,
        quality_details={},
        performance_score=perf_score,
        performance_details={
            "mean_r": mean_r,
            "shrunk_r": shrunk_r,
            "n": n,
            "k": k,
        },
        final_score=perf_score,
        weights={"quality": 0.0, "performance": 1.0},
    )
