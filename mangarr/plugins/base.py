from abc import ABC, abstractmethod


class MangaPluginBase(ABC):
    @abstractmethod
    def get_manga(self) -> dict:
        pass

    @abstractmethod
    def get_volumes(self) -> list[dict]:
        pass