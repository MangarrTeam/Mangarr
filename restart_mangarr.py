import subprocess
import sys

PROGRAM_NAMES = ["hypercorn", "redis"]

def restart_programs():
    try:
        print(f"[INFO] Restarting programs: {', '.join(PROGRAM_NAMES)}")
        result = subprocess.run(
            ["supervisorctl", "restart"] + PROGRAM_NAMES,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[INFO] Programs restarted successfully:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to restart programs:\n{e.stderr}", file=sys.stderr)

if __name__ == "__main__":
    restart_programs()