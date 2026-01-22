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

# Import telegram notifier
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from telegram_notifier import send_telegram_message

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

while True:
    print("\n==============================")
    print("🕒", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    run_step("brain/analyze_signals.py")
    run_step("brain/send_brain_decisions_v2.py")

    print(f"\n⏸️ Pause {LOOP_MINUTES} minutes...\n")
    time.sleep(LOOP_MINUTES * 60)