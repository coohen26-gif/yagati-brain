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

### Running the Brain Loop

```bash
python3 brain/brain_loop.py
```

The brain will:
1. Load environment variables from `.env`
2. Initialize Telegram notifications
3. Send a startup confirmation message
4. Run the analysis loop every 15 minutes
