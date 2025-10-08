from .base import BaseConnector, skip_if_errored, connectors
import requests
import logging
logger = logging.getLogger(__name__)

class KavitaConnector(BaseConnector):
    def __init__(self, username, password, token, *args, **kwargs):
        self.username = username
        self.password = password
        self.token = token
        super().__init__(*args, **kwargs)

    @skip_if_errored
    def notify(self, library:int, *args, **kwargs):
        ip = self.ip
        if ip is None:
            raise Exception("IP was None")
        logger.debug(f"Authentificating Kavita on: {ip}")
        res_login = requests.post(f"{ip}/api/Account/login",
                    json={
                        "username": self.username,
                        "password": self.password,
                        "apiKey": self.token,
                    })
        
        res_login.raise_for_status()

        data = res_login.json()

        jwt_token = data.get("token")
        if jwt_token is not None:
            logger.debug(f"Notifying library {library} on address: {ip}")
            res_scan = requests.post(f"{ip}/api/Library/scan",
                    params={
                        "libraryId": library,
                        "force": False
                    },
                    headers={
                        "Authorization": f"Bearer {jwt_token}"
                    })
            res_scan.raise_for_status()

        logger.debug(f"Notification succesfull")


connector = KavitaConnector(
                connectors.KAVITA_USERNAME,
                connectors.KAVITA_PASSWORD,
                connectors.KAVITA_TOKEN,
                connectors.KAVITA_ADDRESS,
                connectors.KAVITA_PORT,
            )
