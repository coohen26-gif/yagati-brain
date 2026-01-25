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

### Airtable Brain Logs (YAGATI-BRAIN-001)

The brain writes a heartbeat record to Airtable on each execution cycle. This provides a canonical trace of brain activity.

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

Each brain cycle will create a record with:
- `timestamp`: Current UTC time
- `cycle_type`: "heartbeat"
- `context`: "GLOBAL"
- `status`: "ok"
- `note`: "initial brain heartbeat"
