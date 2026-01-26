"""
Setup Detection Module

Detects "forming" setups based on deterministic rules.

Setup types:
- volatility_expansion: Volatility spike detected
- trend_with_structure: Clear trend with favorable structure
- breakout_preparation: Price near key level with expanding volatility
"""

from typing import Dict, Optional
from brain_v2.config.settings import (
    VOL_EXPANSION_MULTIPLIER,
    TREND_STRENGTH_THRESHOLD,
    MIN_RISK_REWARD_RATIO,
    PRICE_EXTENSION_THRESHOLD,
)


def detect_volatility_expansion(features: Dict) -> Optional[Dict]:
    """
    Detect volatility expansion setup.
    
    Conditions:
    - Current volatility > expansion multiplier * average
    
    Args:
        features: Computed technical features
        
    Returns:
        Setup dict or None if not detected
    """
    vol_ratio = features.get("volatility_ratio")
    if vol_ratio is None:
        return None
    
    if vol_ratio >= VOL_EXPANSION_MULTIPLIER:
        return {
            "type": "volatility_expansion",
            "details": f"Volatility expanded {vol_ratio:.2f}x average",
            "metrics": {
                "volatility_ratio": vol_ratio,
            }
        }
    
    return None


def detect_trend_with_structure(features: Dict) -> Optional[Dict]:
    """
    Detect trend with clear structure.
    
    Conditions:
    - Trend strength > threshold
    - MA distance confirms trend
    - Risk/reward ratio favorable
    
    Args:
        features: Computed technical features
        
    Returns:
        Setup dict or None if not detected
    """
    trend_strength = features.get("trend_strength")
    ma_distance_trend = features.get("ma_distance_trend")
    rr_data = features.get("risk_reward")
    
    if trend_strength is None or ma_distance_trend is None or rr_data is None:
        return None
    
    # Check trend strength
    if trend_strength < 50:  # At least partial alignment
        return None
    
    # Check trend confirmation (price sufficiently away from MA)
    # We want meaningful distance, not too close to MA
    if abs(ma_distance_trend) < TREND_STRENGTH_THRESHOLD * 100:  # Convert to percentage
        return None
    
    # Check risk/reward
    rr_ratio = rr_data.get("ratio", 0)
    if rr_ratio < MIN_RISK_REWARD_RATIO:
        return None
    
    return {
        "type": "trend_with_structure",
        "details": f"Trend strength {trend_strength:.0f}/100, R:R {rr_ratio:.2f}",
        "metrics": {
            "trend_strength": trend_strength,
            "ma_distance": ma_distance_trend,
            "risk_reward": rr_ratio,
        }
    }


def detect_breakout_preparation(features: Dict) -> Optional[Dict]:
    """
    Detect breakout preparation setup.
    
    Conditions:
    - Price near recent high/low (within threshold)
    - Volatility expanding
    
    Args:
        features: Computed technical features
        
    Returns:
        Setup dict or None if not detected
    """
    rr_data = features.get("risk_reward")
    vol_ratio = features.get("volatility_ratio")
    
    if rr_data is None or vol_ratio is None:
        return None
    
    current = rr_data.get("current")
    resistance = rr_data.get("resistance")
    support = rr_data.get("support")
    
    if current is None or resistance is None or support is None:
        return None
    
    # Check if near resistance or support
    distance_to_resistance = abs(current - resistance) / current
    distance_to_support = abs(current - support) / current
    
    near_level = (distance_to_resistance < PRICE_EXTENSION_THRESHOLD or 
                  distance_to_support < PRICE_EXTENSION_THRESHOLD)
    
    if not near_level:
        return None
    
    # Check volatility expansion
    if vol_ratio < 1.5:  # At least 1.5x average
        return None
    
    level_type = "resistance" if distance_to_resistance < distance_to_support else "support"
    
    return {
        "type": "breakout_preparation",
        "details": f"Price near {level_type}, volatility {vol_ratio:.2f}x",
        "metrics": {
            "level_type": level_type,
            "volatility_ratio": vol_ratio,
            "distance_to_level": min(distance_to_resistance, distance_to_support) * 100,
        }
    }


def detect_setups(features: Dict, symbol: str, timeframe: str) -> list:
    """
    Run all setup detection rules.
    
    Args:
        features: Computed technical features
        symbol: Market symbol
        timeframe: Timeframe
        
    Returns:
        List of detected setups
    """
    setups = []
    
    # Detect volatility expansion
    vol_setup = detect_volatility_expansion(features)
    if vol_setup:
        setups.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "setup_type": vol_setup["type"],
            "details": vol_setup["details"],
            "metrics": vol_setup["metrics"],
        })
    
    # Detect trend with structure
    trend_setup = detect_trend_with_structure(features)
    if trend_setup:
        setups.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "setup_type": trend_setup["type"],
            "details": trend_setup["details"],
            "metrics": trend_setup["metrics"],
        })
    
    # Detect breakout preparation
    breakout_setup = detect_breakout_preparation(features)
    if breakout_setup:
        setups.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "setup_type": breakout_setup["type"],
            "details": breakout_setup["details"],
            "metrics": breakout_setup["metrics"],
        })
    
    return setups
