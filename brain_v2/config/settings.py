"""
Brain YAGATI v2 Configuration

All configuration parameters are explicitly defined here.
Uses environment variables for credentials.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Market Data Configuration (Supabase)
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL environment variable is required for brain_v2")
if not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_ANON_KEY environment variable is required for brain_v2")

# Normalize URL
SUPABASE_URL = SUPABASE_URL.rstrip('/')

# ============================================================================
# Airtable Configuration
# ============================================================================
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

if not AIRTABLE_API_KEY:
    raise RuntimeError("AIRTABLE_API_KEY environment variable is required for brain_v2")
if not AIRTABLE_BASE_ID:
    raise RuntimeError("AIRTABLE_BASE_ID environment variable is required for brain_v2")

# Table names
TABLE_BRAIN_LOGS = "brain_logs"
TABLE_SETUPS_FORMING = "setups_forming"

# ============================================================================
# Market Analysis Configuration
# ============================================================================

# Timeframes to analyze (aligned with CoinGecko /ohlc supported intervals)
TIMEFRAMES = ["4h", "1d"]

# OHLC data limit (number of candles to fetch)
OHLC_LIMIT = 260

# ============================================================================
# Feature Computation Parameters (Deterministic)
# ============================================================================

# Volatility calculation
VOLATILITY_PERIOD = 20  # Number of candles for volatility calculation

# Moving average periods
MA_FAST = 20
MA_SLOW = 50
MA_TREND = 200

# Risk/Reward parameters
MIN_RISK_REWARD_RATIO = 2.0  # Minimum acceptable R:R ratio

# ============================================================================
# Setup Detection Rules (Deterministic)
# ============================================================================

# Trend conditions
TREND_STRENGTH_THRESHOLD = 0.02  # 2% price distance from MA for trend confirmation

# Volatility expansion threshold
VOL_EXPANSION_MULTIPLIER = 2.0  # Current vol must be > 2x average

# Price extension threshold (for exhaustion detection)
PRICE_EXTENSION_THRESHOLD = 0.05  # 5% from MA

# ============================================================================
# Decision Scoring Parameters (Deterministic)
# ============================================================================

# Base scores for different conditions
SCORE_TREND_ALIGNMENT = 30
SCORE_VOLATILITY_EXPANSION = 25
SCORE_RR_FAVORABLE = 25
SCORE_STRUCTURE_CLEAR = 20

# Confidence thresholds
CONFIDENCE_HIGH_THRESHOLD = 75
CONFIDENCE_MEDIUM_THRESHOLD = 50

# Minimum score to classify as "forming"
MIN_FORMING_SCORE = 50

# ============================================================================
# Governance Configuration
# ============================================================================

# Log all decisions (both forming and reject)
LOG_ALL_DECISIONS = True

# Explicit error logging
LOG_ERRORS_EXPLICITLY = True

# ============================================================================
# Paper Trading Configuration
# ============================================================================

# Enable/disable paper trading engine (default: disabled for safety)
PAPER_TRADING_ENABLED = os.getenv("PAPER_TRADING_ENABLED", "false").lower() == "true"
