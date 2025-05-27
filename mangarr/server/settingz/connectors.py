from .config import CONFIG

KAVITA_ADDRESS = CONFIG.get("Kavita", "address", "", description="IP/domain of Kavita connector")
KAVITA_PORT = CONFIG.getint("Kavita", "port", 80, description="Port of Kavita connector")
KAVITA_SSL = CONFIG.getboolean("Kavita", "ssl", False, description="SSL use of Kavita connector")
KAVITA_USERNAME = CONFIG.get("Kavita", "username", "", description="Username of Kavita connector")
KAVITA_PASSWORD = CONFIG.get("Kavita", "password", "", description="Password of Kavita connector")
KAVITA_TOKEN = CONFIG.get("Kavita", "token", "", description="Token of Kavita connector")
KAVITA_LIBRARY_ID = CONFIG.getint("Kavita", "library_id", -1, description="Library ID of Kavita connector")