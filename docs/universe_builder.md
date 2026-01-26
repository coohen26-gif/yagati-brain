# Universe Builder - Deterministic Tradable Universe Generator

**Version**: 1.0.0  
**Module**: `brain_v2/universe/`

## Overview

The Universe Builder is a deterministic tool that generates a canonical list of tradable cryptocurrency symbols for Brain v2. It replaces the broken Supabase market-data dependency with a reliable, reproducible approach using public APIs.

### What It Does

1. **Fetches** top 100 cryptocurrencies by market cap from CoinGecko
2. **Excludes** stablecoins and stable-like assets
3. **Intersects** with Bitget USDT Perpetual Futures markets (active only)
4. **Produces** a canonical list of ≤50 symbols in Bitget format (e.g., `BTCUSDT`, `ETHUSDT`)
5. **Writes** output to a local JSON file

### Key Features

- ✅ **Deterministic**: Same inputs → same outputs (always)
- ✅ **Public APIs only**: No API keys required
- ✅ **Additive only**: No modifications to existing Brain logic
- ✅ **No Airtable writes**: Pure data generation
- ✅ **Comprehensive logging**: Clear step-by-step output

---

## Quick Start

### Installation

The universe builder uses the same dependencies as Brain v2:

```bash
pip install -r brain_v2/requirements.txt
```

Required packages:
- `requests>=2.31.0` - HTTP client for API calls
- `python-dotenv>=1.0.0` - Environment variable management

### Basic Usage

Run the universe builder:

```bash
python3 -m brain_v2.universe.build_universe
```

**Expected output:**

```
============================================================
Brain YAGATI v2 - Universe Builder
============================================================

[INFO] Fetching top 100 cryptocurrencies from CoinGecko...
[INFO] CoinGecko fetched: 100 coins
[INFO] Applying stablecoin filter...
[INFO] After stable exclusion: 85 coins
[INFO] Excluded 15 stablecoins
[INFO] Fetching Bitget USDT Perpetual Futures markets...
[INFO] Bitget USDT Perp markets found: 200
[INFO] Computing intersection...
[INFO] Intersection count: 72
[INFO] Selecting top 50 by market cap...
[INFO] Final universe size: 50
[INFO] Writing to /opt/yagati/data/universe_usdt_perp.json
[INFO] Written 2048 bytes to /opt/yagati/data/universe_usdt_perp.json

============================================================
[SUCCESS] Universe generation complete!
============================================================

Generated 50 symbols
Output: /opt/yagati/data/universe_usdt_perp.json
```

---

## Configuration

### Environment Variables

Configure the universe builder using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `UNIVERSE_OUTPUT_PATH` | Output JSON file path | `/opt/yagati/data/universe_usdt_perp.json` |
| `COINGECKO_VS_CURRENCY` | CoinGecko quote currency | `usd` |
| `COINGECKO_TOP_N` | Number of top coins to fetch | `100` |
| `BITGET_API_BASE_URL` | Bitget API base URL | `https://api.bitget.com` |

### Example Configuration

```bash
# Custom output path
export UNIVERSE_OUTPUT_PATH=/custom/path/universe.json

# Fetch top 200 coins instead of 100
export COINGECKO_TOP_N=200

# Run the builder
python3 -m brain_v2.universe.build_universe
```

---

## Output Format

The universe builder produces a JSON file with the following structure:

```json
{
  "generated_at": "2026-01-26T19:00:00+00:00",
  "market": "bitget_usdt_perp",
  "source": {
    "coingecko_top_n": 100,
    "target_size": 50
  },
  "symbols": [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "..."
  ],
  "metadata": {
    "coingecko_fetched": 100,
    "after_stable_exclusion": 85,
    "bitget_perp_markets": 200,
    "intersection_count": 50,
    "final_count": 50
  }
}
```

### Field Descriptions

- **`generated_at`**: ISO 8601 timestamp of generation
- **`market`**: Always `"bitget_usdt_perp"`
- **`source.coingecko_top_n`**: Number of coins fetched from CoinGecko
- **`source.target_size`**: Target number of symbols (always 50)
- **`symbols`**: Array of symbol strings in Bitget format
- **`metadata.coingecko_fetched`**: Total coins fetched from CoinGecko
- **`metadata.after_stable_exclusion`**: Coins after stablecoin filtering
- **`metadata.bitget_perp_markets`**: Total active Bitget USDT perpetual markets
- **`metadata.intersection_count`**: Number of symbols in intersection
- **`metadata.final_count`**: Final number of symbols (≤50)

---

## How It Works

### 1. CoinGecko - Top Market Cap

Fetches top cryptocurrencies from CoinGecko's public `/coins/markets` endpoint:

- **Endpoint**: `https://api.coingecko.com/api/v3/coins/markets`
- **Parameters**:
  - `vs_currency=usd`
  - `order=market_cap_desc`
  - `per_page=100`
  - `page=1`
- **Fields used**: `symbol`, `id`, `market_cap_rank`

**Note**: CoinGecko free tier has rate limits (~10-50 calls/min). The client includes retry logic with exponential backoff.

### 2. Stablecoin Filtering

Applies a curated denylist to exclude stable assets:

**Major stablecoins excluded**:
- USDT, USDC, DAI, TUSD, FDUSD, USDE, FRAX, LUSD, PYUSD
- BUSD, GUSD, USDP, SUSD, EURS, EURT, USDN, USDJ, USDX
- Wrapped variants (WUSDC, WUSDT)

The filter checks both symbol and CoinGecko ID (case-insensitive).

### 3. Bitget - USDT Perpetual Futures

Fetches active USDT-margined perpetual futures from Bitget:

- **Endpoint**: `https://api.bitget.com/api/mix/v1/market/contracts`
- **Parameters**: `productType=umcbl` (USDT futures)
- **Filters**: Only active markets (with `supportMarginCoins`)
- **Normalization**: `BTCUSDT_UMCBL` → `BTCUSDT`

### 4. Intersection Logic

1. Get CoinGecko top 100 → **List A**
2. Remove stablecoins from A → **List A'**
3. Get Bitget USDT Perp symbols → **List B**
4. **Intersection**: Keep only coins where base symbol exists in both A' and B
5. Sort by CoinGecko market cap rank
6. Take **top 50** (or all if <50 available)

### 5. Edge Cases

- **Less than 50 symbols**: Outputs all available and logs warning
- **Symbol mismatches**: Currently none known; extendable via mapping dict
- **API failures**: Retry logic with exponential backoff (3 attempts)

---

## Module Architecture

```
brain_v2/universe/
├── __init__.py              # Module initialization
├── build_universe.py        # Main CLI entry point
├── coingecko_client.py      # CoinGecko API client
├── bitget_client.py         # Bitget API client
└── filters.py               # Stablecoin denylist + intersection logic
```

### Key Classes

**`CoinGeckoClient`**
- Fetches top N coins by market cap
- Handles pagination and rate limiting
- Retry logic with exponential backoff

**`BitgetClient`**
- Fetches USDT perpetual futures markets
- Filters active contracts only
- Normalizes symbol format

**Filters Module**
- `is_stablecoin()`: Check if coin is a stablecoin
- `filter_stablecoins()`: Remove stablecoins from list
- `compute_intersection()`: Compute CoinGecko ∩ Bitget

---

## Testing

### Running Tests

Run all universe builder tests:

```bash
# All tests
python3 -m unittest discover -s tests/universe -p 'test_*.py' -v

# Specific test module
python3 -m unittest tests.universe.test_filters -v
```

### Test Coverage

The test suite includes:

1. **Stablecoin filtering** (`test_filters.py`)
   - Major stablecoin identification
   - Filter removal logic
   - Edge cases

2. **Symbol normalization** (`test_filters.py`)
   - Bitget format normalization: `BTCUSDT_UMCBL` → `BTCUSDT`
   - Case handling

3. **Intersection logic** (`test_filters.py`)
   - Basic intersection
   - Market cap ordering
   - Target size limits
   - Less than target handling

4. **CoinGecko client** (`test_coingecko_client.py`)
   - API mocking
   - Pagination
   - Retry logic
   - Error handling

5. **Bitget client** (`test_bitget_client.py`)
   - API mocking
   - Active market filtering
   - Symbol normalization
   - Retry logic

6. **End-to-end** (`test_build_universe.py`)
   - Full universe generation
   - JSON output validation
   - Environment variable configuration

**All tests use mocked API responses** — no real network calls.

---

## Troubleshooting

### Problem: "Failed to fetch CoinGecko data"

**Cause**: Network error or CoinGecko rate limit exceeded

**Solutions**:
1. Check internet connection
2. Wait a few minutes (rate limit cooldown)
3. Reduce `COINGECKO_TOP_N` if rate limiting persists

### Problem: "Failed to fetch Bitget data"

**Cause**: Network error or Bitget API unavailable

**Solutions**:
1. Check internet connection
2. Verify Bitget API status
3. Check `BITGET_API_BASE_URL` is correct

### Problem: "Intersection yielded only X symbols (target: 50)"

**Cause**: Not enough overlap between CoinGecko and Bitget markets

**This is expected behavior** when:
- Many top coins don't have Bitget perpetual futures
- Many top coins are stablecoins

**Solutions**:
1. Accept fewer symbols (this is normal)
2. Increase `COINGECKO_TOP_N` to fetch more coins (e.g., 200)

### Problem: Output directory doesn't exist

**Cause**: Parent directory of `UNIVERSE_OUTPUT_PATH` doesn't exist

**Solutions**:
1. Create directory manually: `mkdir -p /opt/yagati/data`
2. Or use a different path: `export UNIVERSE_OUTPUT_PATH=/tmp/universe.json`

---

## Integration with Brain v2

The universe builder is **independent** and does not modify Brain v2 logic. To use the generated universe:

1. **Run the builder**:
   ```bash
   python3 -m brain_v2.universe.build_universe
   ```

2. **Load the JSON** in your application:
   ```python
   import json
   
   with open("/opt/yagati/data/universe_usdt_perp.json", "r") as f:
       universe = json.load(f)
   
   symbols = universe["symbols"]
   print(f"Trading universe: {len(symbols)} symbols")
   ```

3. **Use symbols** in Brain v2 configuration:
   ```python
   # Example: Update brain_v2/config/symbols.py
   SYMBOL_UNIVERSE = universe["symbols"]
   ```

---

## Motivation

### Why Replace Supabase?

The previous Supabase market-data dependency had several issues:
- ❌ Unreliable availability
- ❌ External dependency on third-party service
- ❌ Not deterministic (data could change unexpectedly)
- ❌ Required authentication and setup

### Benefits of Universe Builder

- ✅ **Deterministic**: Same inputs always produce same outputs
- ✅ **Public APIs**: No authentication required
- ✅ **Reliable**: CoinGecko and Bitget are stable, well-maintained APIs
- ✅ **Transparent**: Clear logging shows exactly what's being included/excluded
- ✅ **Auditable**: All filtering logic is explicit and testable
- ✅ **Maintainable**: Simple, focused codebase

---

## Future Enhancements

Potential improvements (out of scope for MVP):

- 📊 Historical tracking of universe changes over time
- 🔄 Automatic periodic regeneration (cron job)
- 📈 Additional filtering criteria (volume, liquidity)
- 🌍 Multi-exchange support (not just Bitget)
- 📝 Symbol mapping for known mismatches
- 🎯 Custom universe sizes (not just 50)

---

## API References

### CoinGecko API

- **Documentation**: https://www.coingecko.com/en/api/documentation
- **Endpoint**: `/coins/markets`
- **Rate Limits**: ~10-50 calls/min (free tier)
- **No API key required** for basic usage

### Bitget API

- **Documentation**: https://bitgetlimited.github.io/apidoc/en/mix/
- **Endpoint**: `/api/mix/v1/market/contracts`
- **No API key required** for public market data

---

## Support

For issues or questions:
- Check this documentation first
- Review test cases in `tests/universe/`
- Check main README: [/README.md](/README.md)
- Review Brain v2 docs: [/brain_v2/README.md](/brain_v2/README.md)

---

**Universe Builder** - Deterministic. Reliable. Transparent.
