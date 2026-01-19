import requests
from collections import defaultdict

# =========================
# CONFIG
# =========================
SUPABASE_URL = "https://jhtfuqpnggmblsdftlry.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpodGZ1cXBuZ2dtYmxzZGZ0bHJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc5NDQxNzQsImV4cCI6MjA4MzUyMDE3NH0.hhdYOKXQJ4A9oADhuljNICDgABdu8jW54jfkXzidWdY"

HEADERS = {
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json"
}

# =========================
# FETCH SIGNALS
# =========================
def fetch_signals():
    print("Fetching signals from Supabase...")
    r = requests.get(
        f"{SUPABASE_URL}/functions/v1/brain-signals?limit=1000",
        headers=HEADERS
    )
    r.raise_for_status()
    return r.json()["signals"]

# =========================
# ANALYZE OUTCOMES
# =========================
def analyze(signals):
    by_strategy = defaultdict(list)

    for s in signals:
        if s["strategy_id"] and s["outcome"] not in (None, "pending"):
            by_strategy[s["strategy_id"]].append(s)

    print(f"\nStrategies analyzed: {len(by_strategy)}\n")

    for strategy_id, trades in by_strategy.items():
        wins = 0
        losses = 0
        expectancy = 0.0

        for t in trades:
            result = t.get("final_result_percent")
            if result is None:
                continue

            if result > 0:
                wins += 1
            else:
                losses += 1

            expectancy += result

        total = wins + losses
        if total == 0:
            continue

        expectancy /= total
        win_rate = (wins / total) * 100

        print(f"Strategy ID: {strategy_id}")
        print(f"  Trades: {total}")
        print(f"  Win rate: {win_rate:.1f}%")
        print(f"  Expectancy: {expectancy:.2f}%\n")

# =========================
# MAIN
# =========================
def main():
    signals = fetch_signals()
    analyze(signals)

if __name__ == "__main__":
    main()
