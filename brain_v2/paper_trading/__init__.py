"""
Paper Trading Module

A completely isolated paper trading engine that operates independently
from the main trading flow. Reads signals from Airtable and manages
a virtual trading account.

Architecture:
- account.py: Manages paper account state (equity, stats)
- position.py: Calculates position sizes, SL, TP
- recorder.py: Handles all Airtable read/write operations
- engine.py: Main trading logic and lifecycle management

Key Features:
- 100,000 USDT initial capital
- 1% risk per trade
- 1:2 Risk/Reward ratio
- Max 1 trade open at a time
- Completely isolated from real trading
"""

from brain_v2.paper_trading.engine import PaperTradingEngine
from brain_v2.paper_trading.account import PaperAccount
from brain_v2.paper_trading.position import PositionCalculator
from brain_v2.paper_trading.recorder import AirtableRecorder

__all__ = [
    'PaperTradingEngine',
    'PaperAccount',
    'PositionCalculator',
    'AirtableRecorder',
]
