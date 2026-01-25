# yagati-brain
YAGATI - Brain-first trading system 

## Setup

### Environment Variables

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anonymous key
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (for notifications)
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID (for notifications)
- `AIRTABLE_API_KEY` - Your Airtable API key (for brain heartbeat logging)
- `AIRTABLE_BASE_ID` - Your Airtable base ID (for brain heartbeat logging)

### Running the Brain Loop

```bash
python3 brain/brain_loop.py
```

The brain will:
1. Load environment variables from `.env`
2. Initialize Telegram notifications
3. Send a startup confirmation message
4. Run the analysis loop every 15 minutes
5. Log a heartbeat trace to Airtable on each cycle (YAGATI-BRAIN-001)
6. Scan markets for setups forming (V1.1.3-01)

### Airtable Brain Logs (YAGATI-BRAIN-001, YAGATI-BRAIN-002)

The brain writes events to Airtable on each execution cycle. This provides a canonical trace of brain activity.

#### Event Types (cycle_type)

The brain logs three types of events:

1. **heartbeat** - Confirms brain execution (every cycle)
   - `context`: "GLOBAL"
   - `status`: "ok"
   - `note`: "initial brain heartbeat"

2. **scan** - Market symbol scanning events (YAGATI-BRAIN-002)
   - `context`: Market symbol (e.g. "BTCUSDT", "ETHUSDT", "SOLUSDT")
   - `status`: "ok"
   - `note`: "market scanned" (or custom note)

3. **observation** - Pattern detection events (YAGATI-BRAIN-002)
   - `context`: Market symbol
   - `status`: "weak" or "neutral"
   - `note`: Pattern description (e.g. "regime transition detected", "significant upward momentum")

#### Airtable Setup

1. Create a new table named `brain_logs` in your Airtable base
2. Add the following fields:
   - `timestamp` (Date with time)
   - `cycle_type` (Single line text or Single select with values: heartbeat, scan, observation)
   - `context` (Single line text)
   - `status` (Single line text)
   - `note` (Long text, optional)

3. Get your API credentials:
   - API Key: Go to https://airtable.com/account and generate a personal access token
   - Base ID: Found in your base's API documentation (starts with "app...")

4. Add to your `.env` file:
   ```
   AIRTABLE_API_KEY=your_api_key_here
   AIRTABLE_BASE_ID=your_base_id_here
   ```

#### Example Brain Logs Output

Each brain cycle will create records like:

```
timestamp: 2026-01-25T10:00:00Z
cycle_type: heartbeat
context: GLOBAL
status: ok
note: initial brain heartbeat

timestamp: 2026-01-25T10:00:01Z
cycle_type: scan
context: BTCUSDT
status: ok
note: market scanned

timestamp: 2026-01-25T10:00:02Z
cycle_type: scan
context: ETHUSDT
status: ok
note: market scanned

timestamp: 2026-01-25T10:00:03Z
cycle_type: observation
context: BTCUSDT
status: neutral
note: trend regime detected (UP)
```

### Market Setups Table (V1.1.3-01)

The brain now actively scans markets and logs detected setups to a separate table: `setups_forming`.

**Key Features:**
- **Deduplication:** One setup per (symbol, timeframe, setup_type) - updates existing records
- **Smart Writes:** Only writes on state changes (new setup or confidence change)
- **Market Context:** Adds global market context (NORMAL, VOLATILE, PANIC)

#### Airtable Setup for Setups

1. Create a new table named `setups_forming` in your Airtable base
2. Add the following fields:
   - `symbol` (Single line text) - Market symbol (e.g., "BTCUSDT")
   - `timeframe` (Single line text) - Timeframe (e.g., "1h", "4h", "1d")
   - `setup_type` (Single line text) - Type of setup detected
   - `status` (Single line text) - Setup status (always "FORMING" for now)
   - `confidence` (Single line text) - Confidence level (LOW, MEDIUM, HIGH)
   - `detected_at` (Date with time) - When the setup was detected
   - `context` (Long text) - Additional context about the setup
   - `market_context` (Single line text) - Global market context (NORMAL, VOLATILE, PANIC)

#### Setup Types

The scanner detects four types of setups:
- `volatility_expansion` - Volatility spike detected (current > 2x average)
- `range_break_attempt` - Price near recent high/low with expanding volatility
- `trend_acceleration` - Price extended abnormally from moving averages
- `compression_expansion` - Low volatility followed by sudden expansion (squeeze release)

#### Market Scanner Details

- **Universe:** Top 10 crypto assets (BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOGE, DOT, MATIC)
  - Expandable to top 25/50 in configuration
- **Timeframes:** 1H, 4H, 1D
- **Metrics:** Volatility (ATR proxy), price change, MA distance, proximity to extremes
- **Frequency:** Every 15 minutes (same as heartbeat)
- **Important:** This is NOT signal execution. The scanner only detects and logs patterns.

For more details, see [brain/MARKET_SCANNER.md](brain/MARKET_SCANNER.md).

