import threading

stop_event = threading.Event()
threads = []

def register_thread(thread: threading.Thread):
    threads.append(thread)

def stop_all_threads(grace_period:int=5):
    stop_event.set()
    for t in threads:
        t.join(timeout=grace_period)