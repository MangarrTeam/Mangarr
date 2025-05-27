from server.settings import connectors as C
from .connectors import kavita

kavita_connector = kavita.KavitaConnector(C.KAVITA_USERNAME, C.KAVITA_PASSWORD, C.KAVITA_TOKEN, C.KAVITA_ADDRESS, C.KAVITA_PORT)

def run_kavita():
    kavita_connector.notify(C.KAVITA_LIBRARY_ID)


def notify_connectors():
    run_kavita()