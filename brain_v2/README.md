# Brain YAGATI v2 - Deterministic Decision Module

**Version**: 2.0.0  
**Status**: MVP (Minimum Viable Product)

## Overview

Brain YAGATI v2 is a fully independent, deterministic decision module that analyzes real market data, detects forming setups, and makes auditable trading decisions. All decisions are logged to Airtable for complete traceability.

### Key Features

- ✅ **Real Market Data**: Uses existing Supabase API (no fake data)
- ✅ **Deterministic Decisions**: All logic is reproducible and auditable
- ✅ **Setup Detection**: Detects forming setups based on explicit rules
- ✅ **Governance & Logging**: Every action is logged; no silent errors
- ✅ **Airtable Integration**: Writes to `brain_logs` and `setups_forming` tables
- ❌ **No Trading**: No execution, paper trading, or WebSockets
- ❌ **No AI**: No ChatGPT, Grok, or probabilistic models

## Architecture

```
brain_v2/
├── run.py                    # Main entry point
├── config/                   # Configuration
│   ├── settings.py          # All parameters (deterministic)
│   └── symbols.py           # Symbol universe
├── ingest/                   # Market data fetching
│   └── market_data.py       # Supabase API integration
├── features/                 # Feature computation
│   └── technical.py         # Volatility, MA, R:R calculations
├── detect/                   # Setup detection
│   └── setup_detector.py    # Forming setup rules
├── decide/                   # Decision engine
│   └── decision_engine.py   # Scoring + justification
├── publish/                  # Airtable writes
│   └── airtable_writer.py   # brain_logs + setups_forming
└── governance/               # Logging & traceability
    └── logger.py            # Explicit error logging
```

## Setup

### 1. Environment Variables

Ensure your `.env` file contains:

```bash
# Supabase (Market Data)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Airtable (Logging)
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_airtable_base_id
```

### 2. Airtable Tables

Create two tables in your Airtable base:

#### Table: `brain_logs`

| Field       | Type           | Description                     |
|-------------|----------------|---------------------------------|
| timestamp   | Date/Time      | When the log was created        |
| cycle_type  | Single Line    | heartbeat, scan, decision, error|
| context     | Single Line    | GLOBAL, symbol_timeframe, etc.  |
| status      | Single Line    | ok, forming, reject, error      |
| note        | Long Text      | Additional details              |

#### Table: `setups_forming`

| Field          | Type           | Description                   |
|----------------|----------------|-------------------------------|
| symbol         | Single Line    | Market symbol (e.g., BTCUSDT) |
| timeframe      | Single Line    | Timeframe (e.g., 1h, 4h, 1d)  |
| setup_type     | Single Line    | Type of setup detected        |
| status         | Single Line    | Always "FORMING"              |
| confidence     | Single Line    | LOW, MEDIUM, HIGH             |
| detected_at    | Date/Time      | When setup was detected       |
| context        | Long Text      | Justification/details         |
| market_context | Single Line    | NORMAL, VOLATILE, PANIC       |

### 3. Install Dependencies

```bash
pip install requests python-dotenv
```

## Usage

Run the brain:

```bash
python brain_v2/run.py
```

### Expected Output

1. **Startup Log**: One record in `brain_logs` with `cycle_type="heartbeat"`
2. **Analysis Cycle**: Analyzes all symbols/timeframes
3. **Cycle Log**: One record in `brain_logs` with cycle statistics
4. **Decision Logs**: One record per decision in `brain_logs`
5. **Forming Setups**: Records in `setups_forming` only if conditions met

## Decision Flow

```
Market Data → Features → Setup Detection → Decision → Airtable
     ↓            ↓             ↓              ↓           ↓
  OHLC       Volatility    Forming Rules   Score      brain_logs
  candles    MA distance   R:R check       Status     setups_forming
             Trend         Structure       Justif.
```

## Setup Types

The brain detects three types of forming setups:

1. **volatility_expansion**: Volatility spike (current > 2x average)
2. **trend_with_structure**: Clear trend + favorable R:R
3. **breakout_preparation**: Price near key level + expanding volatility

## Decision Scoring (Deterministic)

Each decision receives a score (0-100) based on:

- **Volatility Expansion** (25 points): Current vol > 2x average
- **Trend Alignment** (30 points): MA alignment strength
- **Risk/Reward** (25 points): R:R ratio ≥ 2.0
- **Structure Clarity** (20 points): Setup type specific

### Status Assignment

- **forming**: Score ≥ 50
- **reject**: Score < 50

### Confidence Levels

- **HIGH**: Score ≥ 75
- **MEDIUM**: Score ≥ 50
- **LOW**: Score < 50

## Configuration

All parameters are explicitly defined in `brain_v2/config/settings.py`:

```python
# Timeframes
TIMEFRAMES = ["1h", "4h", "1d"]

# Volatility
VOLATILITY_PERIOD = 20
VOLATILITY_THRESHOLD = 2.0

# Moving Averages
MA_FAST = 20
MA_SLOW = 50
MA_TREND = 200

# Risk/Reward
MIN_RISK_REWARD_RATIO = 2.0

# Scoring
SCORE_TREND_ALIGNMENT = 30
SCORE_VOLATILITY_EXPANSION = 25
SCORE_RR_FAVORABLE = 25
SCORE_STRUCTURE_CLEAR = 20

# Decision Thresholds
MIN_FORMING_SCORE = 50
CONFIDENCE_HIGH_THRESHOLD = 75
CONFIDENCE_MEDIUM_THRESHOLD = 50
```

## Symbol Universe

Default: 5 crypto symbols (configurable in `brain_v2/config/symbols.py`)

```python
SYMBOL_UNIVERSE = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
]
```

Can be expanded to 10, 25, or 50 symbols.

## Governance

### Explicit Error Logging

- **Market data unavailable**: Logged to `brain_logs` as error
- **Airtable write failure**: Logged explicitly (never silent)
- **Decision errors**: Logged with full context

### Deterministic & Reproducible

- No randomness in any calculations
- Same input → same output (always)
- All decisions fully traceable and explainable

## Testing

Manual test checklist:

1. ✅ Run: `python brain_v2/run.py`
2. ✅ Verify startup log in Airtable `brain_logs`
3. ✅ Verify cycle log with statistics
4. ✅ Verify decision logs (forming or reject)
5. ✅ Verify `setups_forming` records (if conditions met)
6. ✅ Check for explicit error logs (if any failures)

## Comparison with Existing Brain

| Feature               | Existing Brain (brain/) | Brain v2 (brain_v2/)     |
|-----------------------|-------------------------|--------------------------|
| Decision Logic        | Event-driven            | Deterministic rules      |
| Setup Detection       | Scanner v1.1.3          | Explicit forming rules   |
| Execution             | Trading enabled         | No execution (MVP)       |
| Logging               | Partial                 | Complete governance      |
| Reproducibility       | Partial                 | Fully deterministic      |
| Independence          | N/A                     | Fully independent        |

## Explicitly Out of Scope

- ❌ Trading / paper trading / execution
- ❌ WebSockets / real-time streaming
- ❌ Fake or simulated data
- ❌ AI-based decisions (ChatGPT, Grok, etc.)
- ❌ Mass historical storage in Airtable
- ❌ VPS modifications
- ❌ Any changes to existing brain code

## Future Enhancements (Post-MVP)

- Extended symbol universe (10, 25, 50 symbols)
- Additional setup types
- Market context detection (NORMAL/VOLATILE/PANIC)
- Multi-timeframe correlation analysis
- Advanced risk/reward calculations
- Continuous loop mode (vs. single run)

## Support

For issues or questions, check:
- Repository README: `/README.md`
- Existing brain docs: `/brain/MARKET_SCANNER.md`
- Airtable setup guide in main README

---

**Brain YAGATI v2** - Deterministic. Auditable. Independent.
