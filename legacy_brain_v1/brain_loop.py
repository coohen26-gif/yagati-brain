import time
import subprocess
from datetime import datetime
import os
from pathlib import Path

# Load .env file explicitly at startup
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not installed, attempting to load environment variables from system")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

# Import telegram notifier and airtable logger
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from telegram_notifier import send_telegram_message
from airtable_logger import log_brain_heartbeat
from brain_cognitive_events import log_cognitive_events
from market_scanner import scan_all_markets
from setup_logger import log_setups_to_airtable

# QUARANTINE GUARD - Brain v1 is obsolete
print("=" * 80)
print("⚠️  CRITICAL WARNING: Brain v1 is QUARANTINED and OBSOLETE")
print("=" * 80)
print()
print("This Brain v1 implementation has been quarantined and should NOT be used.")
print()
print("Reasons for quarantine:")
print("  - Contained hardcoded credentials (security violation)")
print("  - Non-deterministic architecture")
print("  - Superseded by Brain v2 (brain_v2/)")
print()
print("✅ Use brain_v2/ instead:")
print("   python brain_v2/run.py")
print()
print("=" * 80)

# Uncomment the line below to enforce quarantine:
# raise RuntimeError("Brain v1 is quarantined. Use brain_v2 instead.")

# For now, we allow execution with a 10-second warning
print("\n⚠️  Execution will continue in 10 seconds...")
print("Press Ctrl+C to abort.\n")
try:
    time.sleep(10)
except KeyboardInterrupt:
    print("\n✅ Execution aborted. Please use brain_v2 instead.")
    sys.exit(0)

print("⚠️  Proceeding with Brain v1 (legacy mode)...\n")

LOOP_MINUTES = 15  # fréquence du cerveau

def run_step(cmd):
    print(f"\n▶️ Lancement : {cmd}")
    result = subprocess.run(
        ["python3", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(result.stdout)
    if result.stderr:
        print("⚠️ Erreur :", result.stderr)

print("🧠 Brain Loop démarré")
print("⏱️ Fréquence :", LOOP_MINUTES, "minutes")

# Initialize and test Telegram
telegram_ready = False
if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
    print("✅ Telegram ready")
    telegram_ready = True
    
    # Send startup test message
    startup_message = "🧠 <b>YAGATI Brain Started</b>\n\n✅ Brain loop initialized\n⏱️ Running every {} minutes".format(LOOP_MINUTES)
    if send_telegram_message(startup_message):
        print("✅ Startup notification sent to Telegram")
    else:
        print("⚠️ Failed to send startup notification")
else:
    print("⚠️ Telegram not configured (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID required)")

# Log canonical brain heartbeat to Airtable once at startup (YAGATI-BRAIN-001)
print("\n🔍 Logging initial brain heartbeat to Airtable...")
log_brain_heartbeat()

while True:
    print("\n==============================")
    print("🕒", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Log cognitive events (YAGATI-BRAIN-002: scan & observation events)
    try:
        log_cognitive_events()
    except Exception as e:
        print(f"⚠️ Cognitive events failed (non-blocking): {e}")

    # V1.1.3-01: Market scan for setups forming
    try:
        setups = scan_all_markets()
        if setups:
            log_setups_to_airtable(setups)
        else:
            print("ℹ️ No setups detected (market quiet)")
    except Exception as e:
        print(f"⚠️ Market scan failed (non-blocking): {e}")

    run_step("legacy_brain_v1/analyze_signals.py")
    run_step("legacy_brain_v1/send_brain_decisions_v2.py")

    print(f"\n⏸️ Pause {LOOP_MINUTES} minutes...\n")
    time.sleep(LOOP_MINUTES * 60)