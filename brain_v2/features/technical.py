"""
Technical Features Module

Deterministic computations for market analysis:
- Volatility (ATR proxy)
- Moving averages
- Risk/Reward approximations
- Trend strength

All calculations are deterministic and reproducible.
"""

from typing import List, Optional, Dict
from brain_v2.config.settings import (
    VOLATILITY_PERIOD,
    MA_FAST,
    MA_SLOW,
    MA_TREND,
)


def extract_closes(candles: List[Dict]) -> List[float]:
    """Extract close prices from OHLC candles"""
    return [float(c["close"]) for c in candles if c.get("close") is not None]


def extract_highs(candles: List[Dict]) -> List[float]:
    """Extract high prices from OHLC candles"""
    return [float(c["high"]) for c in candles if c.get("high") is not None]


def extract_lows(candles: List[Dict]) -> List[float]:
    """Extract low prices from OHLC candles"""
    return [float(c["low"]) for c in candles if c.get("low") is not None]


def simple_moving_average(values: List[float], period: int) -> Optional[float]:
    """
    Calculate simple moving average.
    
    Args:
        values: List of values
        period: Period for MA
        
    Returns:
        MA value or None if insufficient data
    """
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def exponential_moving_average(values: List[float], period: int) -> Optional[float]:
    """
    Calculate exponential moving average.
    
    Args:
        values: List of values
        period: Period for EMA
        
    Returns:
        EMA value or None if insufficient data
    """
    if len(values) < period:
        return None
    
    k = 2 / (period + 1)
    ema = values[0]
    for v in values[1:]:
        ema = v * k + ema * (1 - k)
    return ema


def calculate_volatility(candles: List[Dict], period: int = VOLATILITY_PERIOD) -> Optional[float]:
    """
    Calculate volatility (ATR proxy using high-low ranges).
    
    Args:
        candles: OHLC candles
        period: Period for volatility calculation
        
    Returns:
        Volatility as percentage or None if insufficient data
    """
    if len(candles) < period:
        return None
    
    highs = extract_highs(candles[-period:])
    lows = extract_lows(candles[-period:])
    closes = extract_closes(candles[-period:])
    
    if not highs or not lows or not closes:
        return None
    
    # Calculate average true range (simplified)
    ranges = []
    for i in range(len(highs)):
        true_range = highs[i] - lows[i]
        ranges.append(true_range)
    
    avg_range = sum(ranges) / len(ranges)
    last_close = closes[-1]
    
    if last_close == 0:
        return None
    
    # Return as percentage
    return (avg_range / last_close) * 100.0


def calculate_volatility_ratio(candles: List[Dict]) -> Optional[float]:
    """
    Calculate current volatility vs average volatility ratio.
    
    Args:
        candles: OHLC candles
        
    Returns:
        Ratio (current_vol / avg_vol) or None if insufficient data
    """
    if len(candles) < VOLATILITY_PERIOD * 2:
        return None
    
    # Current volatility (last N candles)
    current_vol = calculate_volatility(candles[-VOLATILITY_PERIOD:], VOLATILITY_PERIOD)
    
    # Average volatility (all available data)
    avg_vol = calculate_volatility(candles, len(candles))
    
    if current_vol is None or avg_vol is None or avg_vol == 0:
        return None
    
    return current_vol / avg_vol


def calculate_ma_distance(candles: List[Dict], ma_period: int) -> Optional[float]:
    """
    Calculate distance from price to moving average.
    
    Args:
        candles: OHLC candles
        ma_period: MA period
        
    Returns:
        Distance as percentage or None if insufficient data
    """
    closes = extract_closes(candles)
    if len(closes) < ma_period:
        return None
    
    ma = simple_moving_average(closes, ma_period)
    if ma is None or ma == 0:
        return None
    
    last_close = closes[-1]
    distance_pct = ((last_close - ma) / ma) * 100.0
    
    return distance_pct


def calculate_trend_strength(candles: List[Dict]) -> Optional[float]:
    """
    Calculate trend strength based on MA alignment and distance.
    
    Args:
        candles: OHLC candles
        
    Returns:
        Trend strength score (0-100) or None if insufficient data
    """
    closes = extract_closes(candles)
    if len(closes) < MA_TREND:
        return None
    
    # Calculate MAs
    ma_fast = simple_moving_average(closes, MA_FAST)
    ma_slow = simple_moving_average(closes, MA_SLOW)
    ma_trend = simple_moving_average(closes, MA_TREND)
    
    if ma_fast is None or ma_slow is None or ma_trend is None:
        return None
    
    last_close = closes[-1]
    
    # Check alignment (all MAs trending same direction)
    alignment_score = 0
    
    # Uptrend: price > fast > slow > trend
    if last_close > ma_fast > ma_slow > ma_trend:
        alignment_score = 100
    # Downtrend: price < fast < slow < trend
    elif last_close < ma_fast < ma_slow < ma_trend:
        alignment_score = 100
    # Partial alignment
    elif (last_close > ma_trend and ma_fast > ma_slow) or \
         (last_close < ma_trend and ma_fast < ma_slow):
        alignment_score = 50
    else:
        alignment_score = 0
    
    return alignment_score


def calculate_risk_reward_proxy(candles: List[Dict]) -> Optional[Dict]:
    """
    Calculate approximate risk/reward based on recent structure.
    
    Args:
        candles: OHLC candles
        
    Returns:
        Dict with {ratio, support, resistance} or None
    """
    if len(candles) < 20:
        return None
    
    closes = extract_closes(candles)
    highs = extract_highs(candles)
    lows = extract_lows(candles)
    
    last_close = closes[-1]
    
    # Find recent support and resistance (simple approach)
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])
    
    # Calculate potential reward and risk
    potential_reward = recent_high - last_close
    potential_risk = last_close - recent_low
    
    if potential_risk <= 0:
        return None
    
    rr_ratio = potential_reward / potential_risk
    
    return {
        "ratio": rr_ratio,
        "support": recent_low,
        "resistance": recent_high,
        "current": last_close
    }


def compute_features(candles: List[Dict]) -> Dict:
    """
    Compute all technical features for a set of candles.
    
    Args:
        candles: OHLC candles
        
    Returns:
        Dictionary of computed features
    """
    if not candles:
        return {}
    
    closes = extract_closes(candles)
    
    features = {
        "candle_count": len(candles),
        "last_close": closes[-1] if closes else None,
        "volatility": calculate_volatility(candles),
        "volatility_ratio": calculate_volatility_ratio(candles),
        "ma_distance_fast": calculate_ma_distance(candles, MA_FAST),
        "ma_distance_slow": calculate_ma_distance(candles, MA_SLOW),
        "ma_distance_trend": calculate_ma_distance(candles, MA_TREND),
        "trend_strength": calculate_trend_strength(candles),
        "risk_reward": calculate_risk_reward_proxy(candles),
    }
    
    return features
