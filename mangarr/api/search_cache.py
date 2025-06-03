import threading
import time

_search_results = {}
_lock = threading.Lock()

def mark_processing(task_id):
    with _lock:
        _search_results[str(task_id)] = {
            "status": "processing",
            "timestamp": time.time(),
        }

def store_result(task_id, data):
    with _lock:
        _search_results[str(task_id)] = {
            "status": "done",
            "data": data,
            "timestamp": time.time(),
        }
    # Schedule cleanup after 60 seconds
    timer = threading.Timer(60, lambda: remove_result(task_id))
    timer.start()

def remove_result(task_id):
    with _lock:
        _search_results.pop(str(task_id), None)

def get_result(task_id):
    with _lock:
        return _search_results.get(str(task_id))
