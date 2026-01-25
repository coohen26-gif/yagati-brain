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

### Airtable Brain Logs (YAGATI-BRAIN-001, YAGATI-BRAIN-002)

The brain writes heartbeat, scan, and observation events to Airtable. This provides a canonical trace of brain activity and cognitive processes.

#### Airtable Setup

1. Create a new table named `brain_logs` in your Airtable base
2. Add the following fields:
   - `timestamp` (Date with time)
   - `cycle_type` (Single line text or Single select)
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

#### Event Types

The brain logs three types of events:

##### 1. Heartbeat (YAGATI-BRAIN-001)
Canonical trace confirming brain execution.
- `cycle_type`: "heartbeat"
- `context`: "GLOBAL"
- `status`: "ok"
- `note`: "initial brain heartbeat"

##### 2. Scan (YAGATI-BRAIN-002)
Logged when the brain scans or reads market/symbol data.
- `cycle_type`: "scan"
- `context`: Market symbol (e.g., "BTC", "BTCUSDT", "GLOBAL")
- `status`: "ok"
- `note`: Short factual text (e.g., "scanning market regime", "fetching signals from API")

##### 3. Observation (YAGATI-BRAIN-002)
Logged when weak or preliminary patterns are detected.
- `cycle_type`: "observation"
- `context`: Market symbol
- `status`: "weak" or "neutral"
- `note`: Short descriptive label (e.g., "regime: TREND (UP)", "regime: RANGE")

**Note**: The brain operates in observation-only mode. It does NOT log decision, signal, trade, order, buy/sell, execution, or entry/exit events.
