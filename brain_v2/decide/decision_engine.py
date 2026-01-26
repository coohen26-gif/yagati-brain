"""
Decision Engine Module

Makes deterministic, auditable decisions based on detected setups.

Output:
- status: "forming" or "reject"
- score: numeric confidence (0-100)
- confidence: "LOW", "MEDIUM", "HIGH"
- justification: human-readable explanation
"""

from typing import Dict, List
from brain_v2.config.settings import (
    SCORE_TREND_ALIGNMENT,
    SCORE_VOLATILITY_EXPANSION,
    SCORE_RR_FAVORABLE,
    SCORE_STRUCTURE_CLEAR,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    MIN_FORMING_SCORE,
    MIN_RISK_REWARD_RATIO,
)


def calculate_setup_score(setup: Dict, features: Dict) -> int:
    """
    Calculate deterministic score for a setup.
    
    Args:
        setup: Detected setup
        features: Technical features
        
    Returns:
        Score (0-100)
    """
    score = 0
    
    # Base score for setup type
    setup_type = setup.get("setup_type", "")
    
    # Volatility expansion adds points
    vol_ratio = features.get("volatility_ratio", 0)
    if vol_ratio and vol_ratio >= 2.0:
        score += SCORE_VOLATILITY_EXPANSION
    elif vol_ratio and vol_ratio >= 1.5:
        score += int(SCORE_VOLATILITY_EXPANSION * 0.6)
    
    # Trend alignment adds points
    trend_strength = features.get("trend_strength", 0)
    if trend_strength and trend_strength >= 100:
        score += SCORE_TREND_ALIGNMENT
    elif trend_strength and trend_strength >= 50:
        score += int(SCORE_TREND_ALIGNMENT * 0.5)
    
    # Risk/reward adds points
    rr_data = features.get("risk_reward")
    if rr_data:
        rr_ratio = rr_data.get("ratio", 0)
        if rr_ratio >= MIN_RISK_REWARD_RATIO:
            score += SCORE_RR_FAVORABLE
        elif rr_ratio >= MIN_RISK_REWARD_RATIO * 0.7:
            score += int(SCORE_RR_FAVORABLE * 0.5)
    
    # Structure clarity (setup type specific)
    if setup_type in ["trend_with_structure", "breakout_preparation"]:
        score += SCORE_STRUCTURE_CLEAR
    elif setup_type == "volatility_expansion":
        score += int(SCORE_STRUCTURE_CLEAR * 0.5)
    
    # Cap score at 100
    return min(score, 100)


def determine_confidence(score: int) -> str:
    """
    Determine confidence level from score.
    
    Args:
        score: Numeric score
        
    Returns:
        Confidence level: "HIGH", "MEDIUM", or "LOW"
    """
    if score >= CONFIDENCE_HIGH_THRESHOLD:
        return "HIGH"
    elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
        return "MEDIUM"
    else:
        return "LOW"


def generate_justification(
    setup: Dict, 
    features: Dict, 
    score: int, 
    status: str
) -> str:
    """
    Generate human-readable justification for decision.
    
    Args:
        setup: Detected setup
        features: Technical features
        score: Decision score
        status: Decision status
        
    Returns:
        Justification text
    """
    if status == "reject":
        return f"Setup rejected: score {score} below threshold {MIN_FORMING_SCORE}"
    
    # Build justification for forming setup
    parts = []
    
    # Setup type and details
    setup_type = setup.get("setup_type", "unknown")
    details = setup.get("details", "")
    parts.append(f"{setup_type}: {details}")
    
    # Volatility
    vol_ratio = features.get("volatility_ratio")
    if vol_ratio:
        parts.append(f"volatility {vol_ratio:.2f}x average")
    
    # Trend
    trend_strength = features.get("trend_strength")
    if trend_strength and trend_strength >= 50:
        parts.append(f"trend strength {trend_strength:.0f}/100")
    
    # Risk/reward
    rr_data = features.get("risk_reward")
    if rr_data:
        rr_ratio = rr_data.get("ratio", 0)
        if rr_ratio >= MIN_RISK_REWARD_RATIO:
            parts.append(f"R:R {rr_ratio:.2f}")
    
    # Final score
    parts.append(f"score {score}/100")
    
    return "; ".join(parts)


def make_decision(setup: Dict, features: Dict) -> Dict:
    """
    Make a deterministic decision for a setup.
    
    Args:
        setup: Detected setup
        features: Technical features
        
    Returns:
        Decision dict with:
        - status: "forming" or "reject"
        - score: numeric score
        - confidence: confidence level
        - justification: explanation
        - setup: original setup
        - features: features used
    """
    # Calculate score
    score = calculate_setup_score(setup, features)
    
    # Determine status
    status = "forming" if score >= MIN_FORMING_SCORE else "reject"
    
    # Determine confidence
    confidence = determine_confidence(score)
    
    # Generate justification
    justification = generate_justification(setup, features, score, status)
    
    return {
        "status": status,
        "score": score,
        "confidence": confidence,
        "justification": justification,
        "symbol": setup.get("symbol"),
        "timeframe": setup.get("timeframe"),
        "setup_type": setup.get("setup_type"),
        "setup": setup,
        "features": features,
    }


def make_decisions(setups: List[Dict], features: Dict) -> List[Dict]:
    """
    Make decisions for multiple setups.
    
    Args:
        setups: List of detected setups
        features: Technical features
        
    Returns:
        List of decisions
    """
    return [make_decision(setup, features) for setup in setups]
