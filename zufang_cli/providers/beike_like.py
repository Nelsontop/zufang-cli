from __future__ import annotations

import json
import re
from html import unescape
from typing import Optional, Union
from urllib.parse import urlsplit, urlunsplit

from ..exceptions import ParseError, ProviderBlockedError
from ..http import HttpClient
from ..models import Listing
from .base import BaseProvider


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_float(value: Optional[Union[str, int, float]]) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Optional[Union[str, int, float]]) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalize_rent_type(value: str) -> tuple[str, str]:
    if "合租" in value:
        return "shared", "shared"
    if "整租" in value:
        return "whole", "whole"
    return "unknown", ""


def _canonicalize_url(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class BeikeLikeProvider(BaseProvider):
    host: str

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    def build_list_url(self, city_slug: str, page: int) -> str:
        if page <= 1:
            return f"https://{self.host}/chuzu/{city_slug}/"
        return f"https://{self.host}/chuzu/{city_slug}/pg{page}/"

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        from ..constants import MOBILE_HEADERS

        html = self.http.get_text(self.build_list_url(city_slug, page), headers=MOBILE_HEADERS)
        return self.parse_list(html, city_slug)

    def parse_list(self, html: str, city_slug: str) -> list[Listing]:
        if "当前系统繁忙" in html or "系统繁忙" in html:
            raise ProviderBlockedError(f"{self.display_name} returned a temporary busy page.")
        payload = self._extract_house_list(html)
        items: list[Listing] = []
        for entry in payload:
            house_url = entry.get("house_url") or entry.get("scheme", {}).get("m_scheme") or ""
            house_url = unescape(house_url)
            if house_url.startswith("/"):
                house_url = f"https://{self.host}{house_url}"
            house_url = _canonicalize_url(house_url)

            tags = [tag.get("val", "").strip() for tag in entry.get("house_tags", []) if tag.get("val")]
            rent_type, rent_type_text = _normalize_rent_type(str(entry.get("rent_type_name", "")))
            price = _parse_int(entry.get("discount_price") or entry.get("rent_price_listing"))
            price_text = f"{price} yuan/month" if price is not None else ""

            subway_parts = [
                str(entry.get("nearest_line_name", "")).strip(),
                str(entry.get("nearest_subway_station_name", "")).strip(),
            ]
            subway = " ".join(part for part in subway_parts if part)

            listing = Listing(
                provider=self.name,
                provider_name=self.display_name,
                id=str(entry.get("house_code", "")),
                title=_clean(str(entry.get("house_title", ""))),
                url=house_url,
                city_slug=city_slug,
                district=_clean(str(entry.get("hdic_district_name", ""))),
                bizcircle=_clean(str(entry.get("hdic_bizcircle_name", ""))),
                community=_clean(str(entry.get("hdic_resblock_name", ""))),
                address=_clean(str(entry.get("address", ""))),
                price=price,
                price_text=price_text,
                area_sqm=_parse_float(entry.get("rent_area")),
                layout=_clean(str(entry.get("house_layout", ""))),
                floor=_clean(str(entry.get("floor_level", ""))),
                orientation=_clean(str(entry.get("frame_orientation", ""))),
                rent_type=rent_type,
                rent_type_text=rent_type_text,
                tags=tags,
                source_brand=_clean(str(entry.get("app_source_brand_name", ""))),
                image_url=str(entry.get("list_picture", "")),
                subway=subway,
                detail_available=False,
            )
            if listing.id and listing.title:
                items.append(listing)

        if not items:
            raise ParseError(f"{self.display_name} parser found no rental listings in the page payload.")
        return items

    def _extract_house_list(self, html: str) -> list[dict]:
        marker = "JSON.parse(JSON.stringify("
        start = html.find(marker)
        while start != -1:
            bracket_start = html.find("[", start)
            if bracket_start == -1:
                break
            json_blob = self._extract_balanced_json_array(html, bracket_start)
            if '"house_code"' in json_blob and '"house_title"' in json_blob:
                data = json.loads(json_blob)
                if isinstance(data, list):
                    return data
            start = html.find(marker, start + len(marker))
        raise ParseError(f"Could not find {self.display_name} listing payload in the page source.")

    def _extract_balanced_json_array(self, text: str, start_index: int) -> str:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start_index, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == "[":
                depth += 1
                continue
            if char == "]":
                depth -= 1
                if depth == 0:
                    return text[start_index:index + 1]
        raise ParseError(f"Unbalanced {self.display_name} listing payload.")
