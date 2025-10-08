from database.manga.models import Library
import logging
logger = logging.getLogger(__name__)

def notify_connectors(library:Library):
    connectors = library.connectors.all()
    for connector in connectors:
        if not connector.notify():
            logger.warning(f"Connector {connector.name} failed to run notify")