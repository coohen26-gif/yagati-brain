import time
import subprocess
from datetime import datetime

LOOP_MINUTES = 15  # fréquence du cerveau
def run_step(cmd):
    print(f"\n▶️ Lancement : {cmd}")
    result = subprocess.run([
        "python3", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    print(result.stdout)
    if result.stderr:
        print("⚠️ Erreur :", result.stderr)

print("🧠 Brain Loop démarré")
print("⏱️ Fréquence :", LOOP_MINUTES, "minutes")

while True:
    print("\n==============================")
    print("🕒", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    run_step("brain/analyze_signals.py")
    run_step("brain/send_brain_decisions_v2.py")

    print(f"\n⏸️ Pause {LOOP_MINUTES} minutes...\n")
    time.sleep(LOOP_MINUTES * 60)