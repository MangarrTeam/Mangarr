from abc import ABC, abstractmethod
from io import BytesIO
from enum import Enum
import requests
import logging
logger = logging.getLogger(__name__)

NO_THUMBNAIL_URL = "/uploads/static/no_thumbnail.png"

class Formats(Enum):
    NORMAL = 1
    SPECIAL = 2
    REFERENCE = 3
    DIRECTORS_CUT = 4
    BOX_SET = 5
    BOX__SET = 6
    ANNUAL = 7
    ANTHOLOGY = 8
    EPILOGUE = 9
    ONE_SHOT = 10
    ONE__SHOT = 11
    PROLOGUE = 12
    TPB = 13
    TRADE_PAPER_BACK = 14
    OMNIBUS = 15
    COMPENDIUM = 16
    ABSOLUTE = 17
    GRAPHIC_NOVEL = 18
    GN = 19
    FCBD = 20

class AgeRating(Enum):
    UNKNOWN = 1
    RATING_PENDING = 2
    EARLY_CHILDHOOD = 3
    EVERYONE = 4
    G = 5
    EVERYONE_10_PLUS = 6
    PG = 7
    KIDS_TO_ADULTS = 8
    TEEN = 9
    MA_15_PLUS = 10
    MATURE_17_PLUS = 11
    M = 12
    R18_PLUS = 13
    ADULTS_ONLY_18_PLUS = 14
    X_18_PLUS = 15

class MangaPluginBase(ABC):
    languages = []

    @classmethod
    def get_languages(self) -> list[str]:
        return self.languages
    
    @staticmethod
    def search_manga_dict() -> dict:
        """
        Gets predefined manga dictionary (for search)

        Returns:
            dict: Predefined manga dictionary
        """
        return {
            "name": "",
            "description": "",
            "genres": [],
            "tags": [],
            "complete": False,
            "cover": None,
            "url": None,
        }
    
    @abstractmethod
    def search_manga(self, query:str, nsfw:bool, language:str) -> list[dict]:
        """
        Gets list of mangas parsed from query

        Args:
            query (str): Query string

        Returns:
            list[dict]: List of found mangas
        """
        pass

    @staticmethod
    def get_manga_dict() -> dict:
        """
        Gets predefined manga dictionary

        Returns:
            dict: Predefined manga dictionary
        """
        return {
            "name": "",
            "description": "",
            "genres": [],
            "tags": [],
            "complete": False,
            "url": None,
        }

    @abstractmethod
    def get_manga(self, arguments:dict) -> dict:
        """
        Gets manga metadata

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            dict: Dictionary of manga metadata like name, description etc.
        """
        pass

    @staticmethod
    def get_volumes_dict() -> dict:
        """
        Gets predefined volumes dictionary (for list of volumes)

        Returns:
            dict: Predefined volumes dictionary
        """
        return {
            "url": None,
            "arguments": {}
        }

    @abstractmethod
    def get_volumes(self, arguments:dict) -> list[dict]:
        """
        Gets list of volumes urls and other neccessary parameters

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            list[dict]: List of volumes urls and other neccessary parameters
        """
        pass
    
    @staticmethod
    def get_volume_dict() -> dict:
        """
        Gets predefined volume dictionary

        Returns:
            dict: Predefined volume dictionary
        """
        return {
            "name": "",
            "description": "",
            "number": 1.0,
            "url": None,
        }

    @abstractmethod
    def get_volume(self, arguments:dict) -> dict:
        """
        Gets volume metadata

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            dict: Dictionary of volume metadata like name, description etc.
        """
        pass

    @staticmethod
    def get_chapters_dict() -> dict:
        """
        Gets predefined chapters dictionary (for list of chapters)

        Returns:
            dict: Predefined chapters dictionary
        """
        return {
            "url": None,
            "arguments": {}
        }

    @abstractmethod
    def get_chapters(self, arguments:dict) -> list[dict]:
        """
        Gets list of chapters urls and other neccessary parameters

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            list[dict]: List of chapters urls and other neccessary parameters
        """
        pass
    
    @staticmethod
    def get_chapter_dict() -> dict:
        """
        Gets predefined manga dictionary

        Returns:
            dict: Predefined manga dictionary
        """
        return {
            "name": "",
            "description": "",
            "localization": "",
            "publisher": "",
            "imprint": "",
            "release_date": None,
            "writer": "",
            "penciller": "",
            "inker": "",
            "colorist": "",
            "letterer": "",
            "cover_artist": "",
            "editor": "",
            "translator": "",
            "page_count": 1,
            "format": Formats.NORMAL,
            "age_rating": AgeRating.UNKNOWN,
            "isbn": "",
            "number": 1.0,
            "url": None,
        }

    @abstractmethod
    def get_chapter(self, arguments:dict) -> dict:
        """
        Gets chapter metadata

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            dict: Dictionary of chapter metadata like name, description etc.
        """
        pass

    @staticmethod
    def get_pages_dict(self) -> dict:
        """
        Gets predefined pages dictionary (for list of pages)

        Returns:
            dict: Predefined pages dictionary
        """
        return {
            "url": None,
            "arguments": {}
        }

    @abstractmethod
    def get_pages(self, arguments:dict) -> list[dict]:
        """
        Gets list of pages urls

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            list[dict]: List of pages urls and other neccessary parameters
        """
        pass

    @staticmethod
    def download_page(url:str, arguments:dict) -> BytesIO:
        """
        Downloads an image from a given URL and returns it as an in-memory binary stream.

        Args:
            arguments (dict): Dictionary of arguments

        Returns:
            BytesIO: A BytesIO object containing the image data.

        Raises:
            requests.exceptions.RequestException: If the download fails.
        """
        try:
            response = requests.get(url, headers=arguments.get("headers"), cookies=arguments.get("cookies"), timeout=arguments.get("timeout", 10))
            response.raise_for_status()
            return BytesIO(response.content)
        except Exception as e:
            logger.error(f"Error occured while trying to download page - {e}")
            return None