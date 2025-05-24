import datetime
import shutil
from pathlib import Path
import time

def convert_datetime(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(item) for item in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    else:
        return obj
    
def wait_for_file(file_path: Path, timeout=5, interval=0.5):
    elapsed = 0
    while elapsed < timeout:
        if file_path.exists():
            return True
        time.sleep(interval)
        elapsed += interval
    return False
    
def move_file(src: Path, dst:Path):
    if not wait_for_file(src):
        raise FileNotFoundError(f"Source file does not exist: {src}")

    try:
        src.rename(dst)
    except OSError:
        temp_dst = dst.with_suffix(dst.suffix + ".partial")

        try:
            shutil.copy2(src, temp_dst)
            temp_dst.rename(dst)
            src.unlink()
        except Exception:
            if wait_for_file(temp_dst):
                temp_dst.unlink()
            raise