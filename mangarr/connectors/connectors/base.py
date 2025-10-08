from abc import ABC, abstractmethod
from core.settings import connectors
import socket
import logging
logger = logging.getLogger(__name__)

def skip_if_errored(func):
    def wrapper(self, *args, **kwargs):
        if self._errored:
            logger.debug(f"Notification already errored, restart to try again.")
            return
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error - {e}")
            self._errored = True
            return False

    return wrapper

class BaseConnector(ABC):
    def __init__(self, address:str, port:int, ssl:bool=False) -> None:
        self.address = address
        self.port = port
        self.ssl = ssl
        self._errored = False

    @property
    def ip(self) -> str:
        try:
            ip = socket.gethostbyname(self.address)
            return f"http{"s" if self.ssl else ""}://{ip}:{self.port}"
        except socket.gaierror as e:
            logger.error(f"Failed to resolve {self.address}: {e}")
            return None

    def __repr__(self):
        return f"<{self.__class__.__name__} ip={self.ip} port={self.port}>"

    @abstractmethod
    def notify(self, *args, **kwargs) -> bool:
        pass