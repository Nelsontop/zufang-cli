from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Listing:
    provider: str
    provider_name: str
    id: str
    title: str
    url: str
    city_slug: str
    city_name: str = ""
    district: str = ""
    bizcircle: str = ""
    community: str = ""
    address: str = ""
    price: Optional[int] = None
    price_text: str = ""
    area_sqm: Optional[float] = None
    layout: str = ""
    floor: str = ""
    orientation: str = ""
    rent_type: str = "unknown"
    rent_type_text: str = ""
    tags: list[str] = field(default_factory=list)
    agent_name: str = ""
    source_brand: str = ""
    image_url: str = ""
    subway: str = ""
    detail_available: bool = False
    description: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.id}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["key"] = self.key
        return data


@dataclass
class SearchOptions:
    keyword: str
    city_slug: str
    providers: tuple[str, ...]
    page: int = 1
    pages: int = 1
    limit: int = 30
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    rent_type: str = "all"
    sort: str = "default"


@dataclass
class SearchProgress:
    completed: int
    total: int
    provider: str
    provider_name: str
    page: int


@dataclass
class SearchResult:
    items: list[Listing]
    warnings: list[str]
    city_slug: str
    city_name: str
    keyword: str
    providers: list[str]
    page: int
    pages: int
    sort: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [item.to_dict() for item in self.items],
            "count": len(self.items),
            "warnings": list(self.warnings),
            "city_slug": self.city_slug,
            "city_name": self.city_name,
            "keyword": self.keyword,
            "providers": list(self.providers),
            "page": self.page,
            "pages": self.pages,
            "sort": self.sort,
        }
