# V1.1.3-01: Market Scanner Implementation

## Overview

The brain now actively scans crypto markets to detect early trading setups and logs them to Airtable.

**Key Features:**
- **Deduplication:** One setup per (symbol, timeframe, setup_type) - updates existing records
- **Smart Writes:** Only writes on state changes (new setup or confidence change)
- **Market Context:** Adds global market context (NORMAL, VOLATILE, PANIC)
- **Important:** This is NOT signal execution. The scanner only detects and logs patterns.

## What Was Added

### 1. Market Scanner (`market_scanner.py`)

Scans crypto markets using simple, explainable metrics (NO ML/AI).

**Universe:**
- **Top 10** (active): BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOGE, DOT, MATIC
- **Expandable:** Pre-configured for top 25 and top 50 (change `MARKET_UNIVERSE` variable)

**Timeframes:**
- 1H, 4H, 1D

**Metrics Calculated:**
- **Volatility (ATR proxy):** Average true range as percentage of price
- **Price change:** Percentage change over N candles
- **MA distance:** Distance from MA20 and MA50
- **Proximity to extremes:** Distance to recent high/low

**Setup Detection Rules:**

1. **Volatility Expansion**
   - Current volatility > 2x recent average
   - Confidence: HIGH if >3x, MEDIUM if >2x
   - Context: Shows actual volatility values

2. **Range Break Attempt**
   - Price within 2% of recent high/low
   - Volatility expanding (>1.5x recent average)
   - Confidence: MEDIUM
   - Context: Direction (upside/downside)

3. **Trend Acceleration**
   - Price extended >5% from MA20 or >8% from MA50
   - Confidence: HIGH if extended from MA50, MEDIUM if from MA20
   - Context: Direction and actual distances

4. **Compression → Expansion**
   - Low volatility period followed by sudden expansion
   - Compression: vol drops <70% of previous
   - Expansion: vol rises >150% of compressed level
   - Confidence: HIGH if >2x expansion, MEDIUM if >1.5x
   - Context: Volatility progression

**Market Context Detection:**

Global market context based on average volatility across BTC, ETH, SOL:
- **PANIC:** Average volatility > 6% (extreme market movement)
- **VOLATILE:** Average volatility > 3% (significant movement)
- **NORMAL:** Average volatility ≤ 3% (typical market conditions)

### 2. Setup Logger (`setup_logger.py`)

Logs detected setups to Airtable table: `setups_forming`

**Features:**
- **Deduplication:** Loads existing setups into memory cache on startup
- **State Tracking:** Compares current setups with cached state
- **Smart Writes:**
  - **CREATE:** New setup (not in cache)
  - **UPDATE:** Existing setup with confidence change
  - **SKIP:** Existing setup with no changes
- **Batch Processing:** Efficient handling of multiple setups

### 3. Integration (`brain_loop.py`)

Added market scan to the main brain loop:
- Runs every 15 minutes (same as heartbeat)
- Does NOT break existing heartbeat
- Fails gracefully if scan fails
- Only writes to Airtable on state changes

## Airtable Setup

### New Table: `setups_forming`

Create this table in your Airtable base with the following fields:

| Field Name      | Field Type        | Description                                    |
|-----------------|-------------------|------------------------------------------------|
| symbol          | Single line text  | Market symbol (e.g., "BTCUSDT")                |
| timeframe       | Single line text  | Timeframe (e.g., "1h", "4h", "1d")             |
| setup_type      | Single line text  | Type of setup detected                         |
| status          | Single line text  | Always "FORMING" for now                       |
| confidence      | Single line text  | Confidence level (LOW, MEDIUM, HIGH)           |
| detected_at     | Date with time    | When the setup was detected (ISO 8601)         |
| context         | Long text         | Additional context about the setup             |
| market_context  | Single line text  | Global market context (NORMAL, VOLATILE, PANIC)|

**Setup Types:**
- `volatility_expansion` - Volatility spike detected
- `range_break_attempt` - Price near extreme with expansion
- `trend_acceleration` - Price extended from moving averages
- `compression_expansion` - Squeeze release pattern

### Existing Table: `brain_logs`

No changes to existing table. Heartbeat continues to work as before.

## Testing

Run the test script:

```bash
python3 brain/test_market_scanner.py
```

This will:
1. Check environment variables
2. Test single symbol scan
3. Test full market scan across all symbols/timeframes
4. Test Airtable logging

## Environment Variables

No new environment variables required. Uses existing:
- `SUPABASE_URL` - For market data
- `SUPABASE_ANON_KEY` - For market data
- `AIRTABLE_API_KEY` - For logging
- `AIRTABLE_BASE_ID` - For logging

## How It Works

### Scan Loop

```
Every 15 minutes:
1. Log heartbeat (existing)
2. Log cognitive events (existing)
3. NEW: Scan all markets
   - For each symbol in universe
   - For each timeframe (1h, 4h, 1d)
   - Fetch OHLC data
   - Calculate metrics
   - Run detection rules
   - Collect detected setups
4. NEW: Log setups to Airtable
5. Continue with existing logic
```

### Detection Process

For each symbol/timeframe combination:

1. **Fetch Data:** Get 100 most recent candles from Supabase
2. **Calculate Metrics:**
   - ATR proxy (volatility)
   - Price change
   - MA20, MA50 distances
   - Recent high/low proximity
3. **Run Detectors:** Apply each detection rule
4. **Collect Results:** Add detected setups to list

### Logging

- Only logs when setups are actually detected
- No spam if markets are quiet
- Each setup gets its own Airtable record
- Includes full context for analysis

## What to Expect

### When Markets Are Quiet
- Few or no setups detected
- This is normal and expected
- Brain continues heartbeat as usual

### When Markets Are Active
- Multiple setups may be detected
- Different setup types from different timeframes
- Higher confidence when patterns are strong

### Example Output

```
🔍 Starting market scan...
  ✓ BTCUSDT 1d: 1 setup(s) detected
  ✓ ETHUSDT 4h: 2 setup(s) detected
✅ Market scan complete: 3 total setup(s) detected

✅ Setup logged: BTCUSDT 1d - volatility_expansion
✅ Setup logged: ETHUSDT 4h - range_break_attempt
✅ Setup logged: ETHUSDT 4h - compression_expansion
✅ Logged 3/3 setups to Airtable
```

## Files Changed

### New Files
- `brain/market_scanner.py` - Core scanning logic
- `brain/setup_logger.py` - Airtable logger for setups
- `brain/test_market_scanner.py` - Test suite
- `brain/MARKET_SCANNER.md` - This documentation

### Modified Files
- `brain/brain_loop.py` - Added market scan integration

## Technical Details

### Performance
- Scans 5 symbols × 3 timeframes = 15 combinations per cycle
- Each scan fetches 100 candles (~lightweight)
- Total scan time: ~5-10 seconds per cycle
- Non-blocking: Fails gracefully on errors

### Error Handling
- All scans wrapped in try/except
- Individual symbol failures don't stop scan
- Airtable failures don't crash brain
- Detailed error messages for debugging

### Constraints Honored
- ✅ NO ML, AI, or deep learning
- ✅ NO trading execution
- ✅ NO fake data
- ✅ NO Binance
- ✅ NO WebSockets
- ✅ Simple, explainable metrics only
- ✅ Heartbeat continues to work
- ✅ No breaking changes to existing tables

## Maintenance

### Adding New Symbols
Edit `MARKET_UNIVERSE` in `market_scanner.py`:
```python
MARKET_UNIVERSE = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
```

### Adding New Timeframes
Edit `TIMEFRAMES` in `market_scanner.py`:
```python
TIMEFRAMES = ["1h", "4h", "1d", "1w"]
```

### Adjusting Detection Rules
Each detector function is self-contained and can be tuned independently:
- `detect_volatility_expansion()` - Adjust thresholds (currently 2x, 3x)
- `detect_range_break_attempt()` - Adjust proximity (currently 2%)
- `detect_trend_acceleration()` - Adjust MA distances (currently 5%, 8%)
- `detect_compression_expansion()` - Adjust compression/expansion ratios

### Adding New Detectors
1. Create new function in `market_scanner.py`
2. Add to `detectors` list in `scan_symbol_timeframe()`
3. Test with `test_market_scanner.py`

## Next Steps (Future Work)

This implementation is V1.1.3-01. Future enhancements could include:
- Signal generation (separate from setup detection)
- Risk assessment for detected setups
- Historical setup analysis
- Alert filtering/prioritization

But for now: **Scan ✓, Detect ✓, Log ✓, Don't Execute ✓**
