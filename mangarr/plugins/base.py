from abc import ABC, abstractmethod
from io import BytesIO
from enum import Enum, unique
import requests
import logging
logger = logging.getLogger(__name__)

NO_THUMBNAIL_URL = "/uploads/static/no_thumbnail.png"

def enforce_structure(required_keys):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            def apply_defaults(d):
                return {**required_keys, **d}
            if isinstance(result, dict):
                return apply_defaults(result)
            elif isinstance(result, list):
                return [apply_defaults(item) if isinstance(item, list) else item for item in result]
            else:
                raise TypeError("Return must be dicct or list of dicts")
        wrapper._enforced_structure = required_keys
        return wrapper
    return decorator

def final(method):
    method.__is_final__ = True
    return method

class EnforceStructureMeta(type(ABC)):
    def __init__(cls, name, bases, namespace):
        for base in bases:
            for attr_name, attr_value in base.__dict__.items():
                if getattr(attr_value, '__is_final__', False):
                    if attr_name in namespace and namespace[attr_name] != attr_value:
                        raise TypeError(f"Cannot override final method '{attr_name}' in class '{namespace.get("__module__")}'")
        super().__init__(name, bases, namespace)

    def __new__(mcs, name, bases, namespace):
        for attr_name, attr in namespace.items():
            for base in bases:
                base_method = getattr(base, attr_name, None)
                if (base_method and
                    hasattr(base_method, '_enforced_structure') and
                    callable(attr) and
                    not hasattr(attr, '_enforces_structure')):

                    namespace[attr_name] = enforce_structure(base_method._enforced_structure)(attr)
        return super().__new__(mcs, name, bases, namespace)
    
@unique
class BaseEnum(int, Enum):
    @staticmethod
    def get_members(enum:Enum) -> list:
        return list(map(lambda x: (x.value, x.name), enum._member_map_.values()))

class Formats(BaseEnum):
    NORMAL:int = 1
    SPECIAL:int = 2
    REFERENCE:int = 3
    DIRECTORS_CUT:int = 4
    BOX_SET:int = 5
    BOX__SET:int = 6
    ANNUAL:int = 7
    ANTHOLOGY:int = 8
    EPILOGUE:int = 9
    ONE_SHOT:int = 10
    ONE__SHOT:int = 11
    PROLOGUE:int = 12
    TPB:int = 13
    TRADE_PAPER_BACK:int = 14
    OMNIBUS:int = 15
    COMPENDIUM:int = 16
    ABSOLUTE:int = 17
    GRAPHIC_NOVEL:int = 18
    GN:int = 19
    FCBD:int = 20

class AgeRating(BaseEnum):
    UNKNOWN:int = 1
    RATING_PENDING:int = 2
    EARLY_CHILDHOOD:int = 3
    EVERYONE:int = 4
    G:int = 5
    EVERYONE_10_PLUS:int = 6
    PG:int = 7
    KIDS_TO_ADULTS:int = 8
    TEEN:int = 9
    MA_15_PLUS:int = 10
    MATURE_17_PLUS:int = 11
    M:int = 12
    R18_PLUS:int = 13
    ADULTS_ONLY_18_PLUS:int = 14
    X_18_PLUS:int = 15

class Status(BaseEnum):
    UNKNOWN = 1
    ONGOING = 2
    COMPLETED = 3
    HIATUS = 4
    CANCELLED = 5

class MangaPluginBase(ABC, metaclass=EnforceStructureMeta):
    languages = []

    def __init__(self, nsfw_allowed = False, *args, **kwargs):
        self.nsfw_allowed = nsfw_allowed
        super().__init__(*args, **kwargs)

    @final
    @classmethod
    def get_languages(self) -> list[str]:
        return self.languages
    
    @final
    @staticmethod
    def search_manga_dict() -> dict:
        """
        Gets predefined manga dictionary (for search)

        Returns:
            dict: Predefined manga dictionary
        """
        return {
            "name": "",
            "complete": False,
            "cover": None,
            "url": None,
        }
    
    @enforce_structure(search_manga_dict())
    @abstractmethod
    def search_manga(self, query:str, language:str) -> list[dict]:
        """
        Gets list of mangas parsed from query

        Args:
            query (str): Query string

        Returns:
            list[dict]: List of found mangas
        """
        pass
        	
    @final
    @staticmethod
    def get_manga_dict() -> dict:
        """
        Gets predefined manga dictionary

        Returns:
            dict: Predefined manga dictionary
        """
        return {
            "name": "",
            "alt_names": [],
            "description": "",
            "original_language": "",
            "genres": [],
            "tags": [],
            "complete": False,
            "url": None,
        }

    @enforce_structure(get_manga_dict())
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

    @final
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
            "chapter_number": 1.0,
            "volume_number": 1.0,
            "arguments": {},
            "url": None,
            "source_url": None,
        }

    @enforce_structure(get_chapter_dict())
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

    @final
    @staticmethod
    def get_page_dict() -> dict:
        """
        Gets predefined pages dictionary (for list of pages)

        Returns:
            dict: Predefined pages dictionary
        """
        return {
            "url": None,
            "arguments": {}
        }

    @enforce_structure(get_page_dict())
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

    @final
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