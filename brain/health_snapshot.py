import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

# Normalize URL to avoid double slashes
SUPABASE_URL = SUPABASE_URL.rstrip('/')

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}


def get_health_snapshot() -> Dict[str, Any]:
    """
    Get a health snapshot of the brain system.
    
    Returns:
        dict: Health status including timestamp, status, and metrics
    """
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "checks": {},
        "errors": []
    }
    
    # Check signals endpoint
    try:
        url = f"{SUPABASE_URL}/functions/v1/brain-signals"
        params = {"limit": "1"}
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        snapshot["checks"]["signals_endpoint"] = "ok"
    except requests.exceptions.HTTPError as http_err:
        snapshot["status"] = "degraded"
        snapshot["checks"]["signals_endpoint"] = "error"
        snapshot["errors"].append(f"Signals endpoint HTTP error: {http_err}")
    except requests.exceptions.RequestException as req_err:
        snapshot["status"] = "degraded"
        snapshot["checks"]["signals_endpoint"] = "error"
        snapshot["errors"].append(f"Signals endpoint request error: {req_err}")
    
    # Check market data endpoint
    try:
        url = f"{SUPABASE_URL}/functions/v1/market-data/ohlc"
        params = {
            "symbol": "BTC",
            "timeframe": "1d",
            "limit": "1"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        snapshot["checks"]["market_data_endpoint"] = "ok"
    except requests.exceptions.HTTPError as http_err:
        snapshot["status"] = "degraded"
        snapshot["checks"]["market_data_endpoint"] = "error"
        snapshot["errors"].append(f"Market data endpoint HTTP error: {http_err}")
    except requests.exceptions.RequestException as req_err:
        snapshot["status"] = "degraded"
        snapshot["checks"]["market_data_endpoint"] = "error"
        snapshot["errors"].append(f"Market data endpoint request error: {req_err}")
    
    return snapshot


if __name__ == "__main__":
    snapshot = get_health_snapshot()
    print(f"[health_snapshot] Status: {snapshot['status']}")
    print(f"[health_snapshot] Timestamp: {snapshot['timestamp']}")
    print(f"[health_snapshot] Checks: {snapshot['checks']}")
    if snapshot['errors']:
        print(f"[health_snapshot] Errors:")
        for error in snapshot['errors']:
            print(f"  - {error}")
