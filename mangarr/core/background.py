from plugins.tasks import load_downloaded_plugins, background_update
from processes.tasks import monitoring
from core.thread_manager import register_thread
import threading

def _run_plugins():
    load_downloaded_plugins()
    background_update()

def _run_processes():
    monitoring()

def start_background_tasks():
    # Plugins
    plugins_thread = threading.Thread(target=_run_plugins, daemon=True)
    register_thread(plugins_thread)
    plugins_thread.start()

    # Downloader
    processes_thread = threading.Thread(target=_run_processes, daemon=True)
    register_thread(processes_thread)
    processes_thread.start()