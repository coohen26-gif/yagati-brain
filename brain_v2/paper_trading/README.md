# Paper Trading Module

A completely isolated paper trading engine for Brain YAGATI v2. This module operates independently from the main trading flow and manages a virtual trading account.

## ⚠️ Activation

The paper trading engine is **disabled by default** for safety. To enable it:

```bash
# In your .env file
PAPER_TRADING_ENABLED=true
```

Or via environment variable:
```bash
export PAPER_TRADING_ENABLED=true
```

**Default behavior**: If not set or set to anything other than "true", paper trading remains **disabled**.

## Architecture

```
brain_v2/paper_trading/
├── __init__.py       # Module exports
├── engine.py         # Main trading engine
├── account.py        # Account management
├── position.py       # Position sizing & calculations
├── recorder.py       # Airtable I/O operations
└── README.md         # This file
```

## Features

- **Initial Capital**: 100,000 USDT virtual account
- **Risk Management**: 1% risk per trade
- **Risk/Reward**: 1:2 ratio (target 2x potential profit vs risk)
- **Trade Limit**: Maximum 1 open trade at a time
- **Complete Isolation**: No impact on real trading systems

## Airtable Tables

### Read From
- `setups_forming`: Source of trading signals from main analysis

### Write To
- `paper_account`: Virtual account state (equity, statistics)
- `paper_open_trades`: Currently open trades
- `paper_closed_trades`: Historical closed trades

## Usage

### Enabling Paper Trading

1. Set the environment variable:
   ```bash
   export PAPER_TRADING_ENABLED=true
   ```

2. Or add to your `.env` file:
   ```
   PAPER_TRADING_ENABLED=true
   ```

3. Run the brain normally:
   ```bash
   python brain_v2/run.py
   ```

### Integration in Main Flow

The paper trading engine is **optionally** called at the end of each analysis cycle in `run.py`:

```python
from brain_v2.config.settings import PAPER_TRADING_ENABLED

# At the end of analysis cycle
if PAPER_TRADING_ENABLED:
    try:
        from brain_v2.paper_trading.engine import PaperTradingEngine
        paper_engine = PaperTradingEngine()
        paper_engine.run_cycle()
    except Exception as e:
        # Paper trading errors NEVER block the main flow
        logger.error(f"Paper trading error (non-blocking): {e}")
        # Main flow continues normally
else:
    logger.info("Paper trading disabled")
```

**Important**: Paper trading is wrapped in try/except to ensure main flow **always continues** even if errors occur.

## Components

### 1. PaperTradingEngine (`engine.py`)

Main engine that orchestrates the trading cycle:
- Monitors open trades for SL/TP hits
- Checks for new signals when no trade is open
- Opens new trades based on setups
- Closes trades and updates account

### 2. PaperAccount (`account.py`)

Manages virtual account state:
- Initializes account with starting capital
- Tracks equity (current balance)
- Maintains trade statistics (total, wins, losses)
- Updates account after each trade

### 3. PositionCalculator (`position.py`)

Calculates position parameters:
- **Position Size**: Based on 1% account risk
- **Stop Loss**: Risk-based level
- **Take Profit**: 1:2 risk/reward ratio
- **P&L Calculation**: Profit/loss for closed trades

### 4. AirtableRecorder (`recorder.py`)

Handles all Airtable operations:
- Reads forming setups
- Reads/writes account state
- Manages open trades table
- Archives closed trades

## Trading Logic

### Cycle Flow

```
1. Check Open Trades
   ├─> If SL hit → Close trade (loss)
   ├─> If TP hit → Close trade (profit)
   └─> If no hit → Continue monitoring

2. Check New Signals (only if no open trade)
   ├─> Read setups_forming table
   ├─> Filter valid FORMING setups
   ├─> Calculate position size (1% risk)
   ├─> Calculate SL and TP (1:2 RR)
   └─> Open trade
```

### Position Sizing Example

```python
equity = 100,000 USDT
risk_percent = 0.01  # 1%
risk_amount = 100,000 * 0.01 = 1,000 USDT

entry_price = 50,000
stop_loss = 49,000
distance_to_sl = 1,000

position_size = risk_amount / distance_to_sl
              = 1,000 / 1,000
              = 1.0 units

take_profit = entry_price + (distance_to_sl * 2)
            = 50,000 + (1,000 * 2)
            = 52,000
```

### P&L Calculation

**Long Trade**:
```python
pnl = (exit_price - entry_price) * position_size
```

**Short Trade**:
```python
pnl = (entry_price - exit_price) * position_size
```

## Data Structures

### Account Record (paper_account)
```python
{
    "equity": 100000.0,           # Current equity
    "initial_capital": 100000.0,  # Starting capital
    "total_trades": 0,             # Total trades executed
    "winning_trades": 0,           # Number of wins
    "losing_trades": 0,            # Number of losses
    "updated_at": "2024-01-30T12:00:00Z"
}
```

### Open Trade Record (paper_open_trades)
```python
{
    "symbol": "BTCUSDT",
    "direction": "LONG",           # LONG or SHORT
    "entry_price": 50000.0,
    "position_size": 1.0,
    "stop_loss": 49000.0,
    "take_profit": 52000.0,
    "risk_amount": 1000.0,         # Amount at risk (1%)
    "equity_at_open": 100000.0,    # Equity when opened
    "opened_at": "2024-01-30T12:00:00Z",
    "setup_id": "rec123abc"        # Reference to setup
}
```

### Closed Trade Record (paper_closed_trades)
```python
{
    # All fields from open trade, plus:
    "exit_price": 52000.0,
    "closed_at": "2024-01-30T14:00:00Z",
    "pnl": 2000.0,                 # Profit/Loss in USDT
    "pnl_percent": 4.0,            # P&L as percentage
    "exit_reason": "TP_HIT"        # TP_HIT, SL_HIT, MANUAL
}
```

## Safety & Isolation

### No Impact on Main Flow
- Wrapped in try/except to never block main analysis
- Uses separate Airtable tables
- No shared state with real trading
- Independent execution cycle

### Error Handling
- All errors logged but not raised
- Failed operations don't crash the system
- Defensive validation of all data

### No Real Trading
- **NEVER** sends orders to exchanges
- **NEVER** accesses real trading accounts
- **PURELY** virtual/simulated trading
- All operations write only to paper trading tables

## Monitoring

The engine outputs detailed logs for each cycle:

```
============================================================
📊 Paper Trading Cycle
============================================================
Equity: 100000.00 USDT
Trades: 0 (0W/0L)
ℹ️  Paper Trading: No open trades
🔍 Paper Trading: Checking for new signals...
   Found 1 forming setup(s)
   📌 Selected setup: BTCUSDT - bullish_reversal
   ✅ Trade opened
   BTCUSDT LONG
   Entry: 50000.00
   Size: 1.0000
   SL: 49000.00 | TP: 52000.00
   Risk: 1000.00 USDT (1%)
============================================================
```

## Future Enhancements

- [ ] Integration with market data for real-time price monitoring
- [ ] Advanced position sizing strategies
- [ ] Multiple simultaneous trades
- [ ] Performance analytics and reporting
- [ ] Backtesting capabilities
- [ ] Risk management enhancements

## Testing

Run the integration test:
```bash
python brain_v2/test_paper_trading.py
```

## Notes

- The module currently has placeholders for price data integration
- Trade monitoring requires market data feed (to be implemented)
- All calculations are deterministic and testable
- Module is designed for easy enhancement and extension
