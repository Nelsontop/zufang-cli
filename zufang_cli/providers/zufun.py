from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..constants import DESKTOP_HEADERS, PROVIDER_NAMES
from ..exceptions import ParseError
from ..http import HttpClient
from ..models import Listing
from ..query import build_search_token_groups
from .base import BaseProvider
from .routing import add_path_page, clean_text, collect_route_options, select_best_route


def _parse_price(value: str) -> Optional[int]:
    matches = re.findall(r"(\d+)", value.replace(",", ""))
    return int(matches[-1]) if matches else None


def _parse_area(value: str) -> Optional[float]:
    match = re.search(r"([\d.]+)", value)
    return float(match.group(1)) if match else None


def _normalize_rent_type(value: str) -> tuple[str, str]:
    if "\u5408\u79df" in value:
        return "shared", "shared"
    if "\u6574\u79df" in value:
        return "whole", "whole"
    return "unknown", ""


class ZufunProvider(BaseProvider):
    name = "zufun"
    display_name = PROVIDER_NAMES["zufun"]

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    def build_list_url(self, city_slug: str, page: int) -> str:
        return add_path_page(f"https://{city_slug}.zufun.cn/zufang-list/", page)

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        base_url = self._resolve_list_url(city_slug, keyword)
        html = self.http.get_text(add_path_page(base_url, page), headers=DESKTOP_HEADERS)
        return self.parse_list(html, city_slug)

    def parse_list(self, html: str, city_slug: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[Listing] = []

        for building in soup.select(".building-item"):
            community_tag = building.select_one(".title-wrap a[href]")
            community = clean_text(community_tag.get_text(" ", strip=True)) if community_tag else ""
            property_labels = [clean_text(tag.get_text(" ", strip=True)) for tag in building.select(".label-wrap .label-name")]

            addr = building.select_one(".ppt-addr")
            district = ""
            bizcircle = ""
            subway = ""
            address = ""
            if addr:
                links = addr.select("a")
                if links:
                    district = clean_text(links[0].get_text(" ", strip=True))
                if len(links) > 1:
                    bizcircle = clean_text(links[1].get_text(" ", strip=True))
                if len(links) > 2:
                    subway = clean_text(links[2].get_text(" ", strip=True))
                address = clean_text(addr.get_text(" ", strip=True))

            for apt in building.select("a.apt-item[href]"):
                href = urljoin(f"https://{city_slug}.zufun.cn", apt.get("href", "").strip())
                id_match = re.search(r"/apt/(\d+)", href)
                if not id_match:
                    continue

                columns = [clean_text(node.get_text(" ", strip=True)) for node in apt.select("li")]
                if len(columns) < 4:
                    continue

                title = ""
                image_tag = apt.select_one("img")
                if image_tag:
                    title = clean_text(image_tag.get("alt", ""))
                if not title:
                    title = clean_text(f"{community} {columns[0]}")

                image_url = ""
                if image_tag:
                    image_url = image_tag.get("data-original") or image_tag.get("src") or ""
                    image_url = clean_text(image_url)

                rent_type, rent_type_text = _normalize_rent_type(columns[0])

                listing = Listing(
                    provider=self.name,
                    provider_name=self.display_name,
                    id=id_match.group(1),
                    title=title,
                    url=href,
                    city_slug=city_slug,
                    district=district,
                    bizcircle=bizcircle,
                    community=community,
                    address=address,
                    price=_parse_price(columns[3]),
                    price_text=columns[3],
                    area_sqm=_parse_area(columns[1]),
                    layout=columns[0],
                    floor=columns[2],
                    rent_type=rent_type,
                    rent_type_text=rent_type_text,
                    tags=list(property_labels),
                    source_brand=" / ".join(property_labels),
                    image_url=image_url,
                    subway=subway,
                    detail_available=False,
                )
                if subway:
                    listing.tags.append(subway)
                items.append(listing)

        if not items:
            raise ParseError("Zufun parser found no rental listings on the page.")
        return items

    def _resolve_list_url(self, city_slug: str, keyword: str) -> str:
        current_url = self.build_list_url(city_slug, 1)
        for token_group in build_search_token_groups(keyword):
            html = self.http.get_text(current_url, headers=DESKTOP_HEADERS)
            next_url = select_best_route(
                collect_route_options(
                    html,
                    current_url,
                    href_predicate=lambda href: "/zufang-list" in href or "/zufang-sub" in href,
                ),
                token_group,
                current_url=current_url,
            )
            if next_url:
                current_url = next_url
        return current_url
