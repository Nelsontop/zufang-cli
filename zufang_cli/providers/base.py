from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Listing


class BaseProvider(ABC):
    name: str
    display_name: str

    @abstractmethod
    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        raise NotImplementedError
