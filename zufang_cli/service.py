from __future__ import annotations

from typing import Iterable, Optional

from .cache import get_by_index, get_by_key, save_index
from .constants import COMMON_CITIES, PROVIDER_NAMES
from .exceptions import ProviderBlockedError
from .http import HttpClient
from .models import Listing, SearchOptions, SearchResult
from .providers import AnjukeProvider, KeProvider, LianjiaProvider, LeyoujiaProvider, QfangProvider, ZufunProvider
from .query import (
    build_search_token_groups,
    build_search_tokens,
    infer_city_and_keyword,
    normalize_city_slug,
    normalize_query_text,
)


def list_supported_cities() -> list[tuple[str, str]]:
    return list(COMMON_CITIES)


class ZufangService:
    def __init__(self, http_client: Optional[HttpClient] = None) -> None:
        self.http = http_client or HttpClient()
        self.providers = {
            "anjuke": AnjukeProvider(self.http),
            "ke": KeProvider(self.http),
            "lianjia": LianjiaProvider(self.http),
            "qfang": QfangProvider(self.http),
            "zufun": ZufunProvider(self.http),
            "leyoujia": LeyoujiaProvider(self.http),
        }

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> ZufangService:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def search(self, options: SearchOptions) -> SearchResult:
        effective_city, effective_keyword = infer_city_and_keyword(options.keyword, options.city_slug)
        city_slug, city_name = normalize_city_slug(effective_city)
        warnings: list[str] = []
        items: list[Listing] = []
        errors: list[Exception] = []

        for provider_name in options.providers:
            provider = self.providers[provider_name]
            for page in range(options.page, options.page + options.pages):
                try:
                    page_items = provider.search_page(city_slug, page, effective_keyword)
                    for item in page_items:
                        item.city_name = city_name
                    items.extend(page_items)
                except ProviderBlockedError as exc:
                    warnings.append(f"{provider.display_name}: {exc}")
                    break
                except Exception as exc:  # pragma: no cover
                    errors.append(exc)
                    break

        filtered = self._filter_items(items, effective_keyword, options.min_price, options.max_price, options.rent_type)
        sorted_items = self._sort_items(filtered, options.sort)
        limited = sorted_items[: options.limit]
        save_index(limited, source=f"search:{options.keyword}:{city_slug}")

        if not limited and errors and not warnings:
            raise errors[0]

        return SearchResult(
            items=limited,
            warnings=warnings,
            city_slug=city_slug,
            city_name=city_name,
            keyword=options.keyword,
            providers=[PROVIDER_NAMES[name] for name in options.providers],
            page=options.page,
            pages=options.pages,
            sort=options.sort,
        )

    def show(self, index: int) -> Listing:
        return get_by_index(index)

    def get_cached_listing(self, reference: str) -> Listing:
        if reference.isdigit():
            return get_by_index(int(reference))
        return get_by_key(reference)

    def provider_names(self) -> list[tuple[str, str]]:
        return [(name, provider.display_name) for name, provider in self.providers.items()]

    def _filter_items(
        self,
        items: Iterable[Listing],
        keyword: str,
        min_price: Optional[int],
        max_price: Optional[int],
        rent_type: str,
    ) -> list[Listing]:
        token_groups = build_search_token_groups(keyword)
        result: list[Listing] = []
        for item in items:
            if token_groups:
                haystack = normalize_query_text(
                    " ".join(
                        [
                            item.title,
                            item.community,
                            item.district,
                            item.bizcircle,
                            item.address,
                            item.source_brand,
                            item.city_name,
                            item.city_slug,
                            item.subway,
                            item.floor,
                            item.orientation,
                            " ".join(item.tags),
                        ]
                    )
                )
                if any(all(candidate not in haystack for candidate in group) for group in token_groups):
                    continue
            if min_price is not None and (item.price is None or item.price < min_price):
                continue
            if max_price is not None and (item.price is None or item.price > max_price):
                continue
            if rent_type != "all" and item.rent_type != rent_type:
                continue
            result.append(item)
        return result

    def _sort_items(self, items: list[Listing], mode: str) -> list[Listing]:
        if mode == "price_asc":
            return sorted(items, key=lambda item: (item.price is None, item.price or 0, item.provider, item.id))
        if mode == "price_desc":
            return sorted(items, key=lambda item: (item.price is None, -(item.price or 0), item.provider, item.id))
        return items


def get_service() -> ZufangService:
    return ZufangService()
