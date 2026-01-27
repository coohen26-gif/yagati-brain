# yagati-brain
YAGATI - Brain-first trading system 

---

## 🚀 Bootstrap d'un nouveau chat (Context Pack)

Pour démarrer une nouvelle conversation avec le contexte complet du projet YAGATI, suivez ces étapes :

### Étape 1 : Copier le Context Pack
Copiez le contenu du fichier **[docs/YAGATI_CONTEXT_PACK.md](docs/YAGATI_CONTEXT_PACK.md)** dans votre nouveau chat.

Ce fichier contient :
- Les règles absolues du projet
- Le pipeline de trading
- Les modules actifs et leur statut
- Les interdictions et contraintes
- L'état actuel du projet

### Étape 2 : Références pour approfondir (optionnel)

Si vous avez besoin de plus de détails, consultez ces documents :

- **[docs/YAGATI_KERNEL.md](docs/YAGATI_KERNEL.md)** — Source de vérité stable (principes, architecture, gouvernance)
- **[docs/YAGATI_STATE.md](docs/YAGATI_STATE.md)** — Snapshot de l'état actuel du projet
- **[docs/YAGATI_DECISIONS.md](docs/YAGATI_DECISIONS.md)** — Journal des décisions majeures
- **[docs/OPS.md](docs/OPS.md)** — Workflow opérationnel de l'équipe

### Étape 3 : Commencer votre travail

Vous êtes prêt ! Le context pack contient tout ce qu'il faut pour :
- Comprendre les contraintes du projet (GitHub source unique, Copilot→PR, pas de hotfix)
- Connaître le pipeline (Signaux → Signal Center → /day → Paper Trading → Bitget)
- Respecter les interdictions (Binance, fake data, WebSockets)
- Suivre les priorités trading (EV, drawdown, risk-of-ruin)

---

## Brain Modules

This repository contains two brain modules:

### ✅ Brain YAGATI v2 (PRODUCTION - `brain_v2/`)
**Status**: ACTIVE - Use this implementation

Deterministic decision module (MVP) - fully independent, clean architecture.

**Run**: `python brain_v2/run.py`

📖 **Full documentation**: [brain_v2/README.md](brain_v2/README.md)

Key features:
- ✅ Deterministic, auditable decisions
- ✅ Real market data (Supabase API)
- ✅ **Universe Builder** - Deterministic tradable symbol generation
- ✅ Setup detection (forming only)
- ✅ Complete governance & logging
- ✅ Airtable integration (`brain_logs` + `setups_forming`)
- ✅ No hardcoded credentials (environment variables only)

### ⚠️ Brain v1 (QUARANTINED - `legacy_brain_v1/`)
**Status**: OBSOLETE - DO NOT USE

The original event-driven trading brain has been quarantined due to:
- Security violations (hardcoded credentials)
- Non-deterministic architecture
- Superseded by Brain v2

**This directory is kept for audit purposes only and will be removed after Brain v2 validation.**

❌ Do not use in production  
❌ Do not modify  
✅ Use `brain_v2/` instead

---

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

### Running Brain v2

```bash
python brain_v2/run.py
```

For Brain v2 documentation, see [brain_v2/README.md](brain_v2/README.md).

### ⚠️ Legacy Brain v1 (Quarantined)

**Status**: OBSOLETE - Kept for audit purposes only

Brain v1 has been quarantined and is **non-executable**. Any attempt to run it will immediately fail with an error.

- ❌ **DO NOT** attempt to execute
- ❌ **DO NOT** modify
- ✅ **Use `brain_v2/` instead** for all production needs

For historical context, see [legacy_brain_v1/README.md](legacy_brain_v1/README.md).

#### Legacy Brain v1 Features (Historical Reference Only)

The legacy Brain v1 previously would:
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

For more details, see [legacy_brain_v1/MARKET_SCANNER.md](legacy_brain_v1/MARKET_SCANNER.md) (Legacy documentation).

---

## Universe Builder (Brain v2 - NEW)

The **Universe Builder** is a deterministic tool for generating a canonical list of tradable cryptocurrency symbols. It replaces the broken Supabase market-data dependency with a reliable approach using public APIs.

### Quick Start

Generate the tradable universe:

```bash
python3 -m brain_v2.universe.build_universe
```

This will:
1. Fetch top 100 cryptocurrencies by market cap from CoinGecko
2. Exclude stablecoins (USDT, USDC, DAI, etc.)
3. Intersect with Bitget USDT Perpetual Futures markets
4. Output ≤50 symbols to `/opt/yagati/data/universe_usdt_perp.json`

### Features

- ✅ **Deterministic**: Same inputs → same outputs
- ✅ **Public APIs only**: No API keys required
- ✅ **Comprehensive logging**: Clear step-by-step output
- ✅ **No Airtable writes**: Pure data generation
- ✅ **Fully tested**: 31 unit and integration tests

### Configuration

Configure via environment variables:

```bash
export UNIVERSE_OUTPUT_PATH=/custom/path/universe.json
export COINGECKO_TOP_N=200
python3 -m brain_v2.universe.build_universe
```

**Full Documentation**: [docs/universe_builder.md](docs/universe_builder.md)

