from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup

from ..constants import CITY_HOST_ALIASES, DESKTOP_HEADERS, PROVIDER_NAMES
from ..exceptions import ParseError, ProviderBlockedError
from ..http import HttpClient
from ..models import Listing
from ..query import build_search_token_groups, normalize_query_text
from .base import BaseProvider
from .routing import add_query_page, clean_text, collect_route_options, select_best_route


def _parse_price(value: str) -> Optional[int]:
    match = re.search(r"(\d+)", value.replace(",", ""))
    return int(match.group(1)) if match else None


def _parse_area(value: str) -> Optional[float]:
    match = re.search(r"([\d.]+)", value)
    return float(match.group(1)) if match else None


def _normalize_rent_type(value: str) -> tuple[str, str]:
    if "\u5408\u79df" in value:
        return "shared", "shared"
    if "\u6574\u79df" in value:
        return "whole", "whole"
    return "unknown", ""


def _canonicalize_url(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class QfangProvider(BaseProvider):
    name = "qfang"
    display_name = PROVIDER_NAMES["qfang"]
    ROUTE_HINTS = {
        "sz": {
            normalize_query_text("南山"): "/rent/nanshan",
            normalize_query_text("福田"): "/rent/futian",
            normalize_query_text("罗湖"): "/rent/luohu",
            normalize_query_text("宝安"): "/rent/baoan",
            normalize_query_text("宝安区"): "/rent/baoan",
            normalize_query_text("龙岗"): "/rent/longgang",
            normalize_query_text("龙华"): "/rent/longhuaa",
            normalize_query_text("光明区"): "/rent/guangmingqu",
            normalize_query_text("盐田"): "/rent/yantiana",
            normalize_query_text("坪山"): "/rent/pingshanab",
            normalize_query_text("大鹏新区"): "/rent/dapengxinqu",
            normalize_query_text("宝安中心区"): "/rent/baoan-baoanzhongxinqu",
            normalize_query_text("碧海"): "/rent/baoan-bihai",
            normalize_query_text("福永"): "/rent/baoan-fuyong",
            normalize_query_text("翻身"): "/rent/baoan-fanshen",
            normalize_query_text("松岗"): "/rent/baoan-songgang",
            normalize_query_text("石岩"): "/rent/baoan-shiyan",
            normalize_query_text("沙井"): "/rent/baoan-shajing",
            normalize_query_text("桃源居"): "/rent/baoan-taoyuanju",
            normalize_query_text("西乡"): "/rent/baoan-xixiang",
            normalize_query_text("宝安西乡"): "/rent/baoan-xixiang",
            normalize_query_text("宝安区西乡"): "/rent/baoan-xixiang",
            normalize_query_text("新安"): "/rent/baoan-xinan",
            normalize_query_text("宝安新安"): "/rent/baoan-xinan",
            normalize_query_text("曦城"): "/rent/baoan-xicheng",
        }
    }

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    def _city_host(self, city_slug: str) -> str:
        host = CITY_HOST_ALIASES.get(city_slug)
        if not host:
            raise ProviderBlockedError(f"Qfang does not have a configured host for city `{city_slug}`.")
        return host

    def build_list_url(self, city_slug: str, page: int) -> str:
        host = self._city_host(city_slug)
        return add_query_page(f"https://{host}.qfang.com/rent", page)

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        base_url = self._resolve_list_url(city_slug, keyword)
        html = self.http.get_text(add_query_page(base_url, page), headers=DESKTOP_HEADERS)
        return self.parse_list(html, city_slug)

    def parse_list(self, html: str, city_slug: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        title = clean_text(soup.title.get_text()) if soup.title else ""
        body_text = soup.get_text(" ", strip=True)
        if "\u9a8c\u8bc1\u7801" in title or "\u8bbf\u95ee\u53d7\u9650" in body_text:
            raise ProviderBlockedError("Qfang list page is asking for verification.")

        host = self._city_host(city_slug)
        items: list[Listing] = []
        for card in soup.select("li.items"):
            link_tag = card.select_one("a.house-title[href]") or card.select_one(".photo-wrap a[href]")
            if not link_tag:
                continue

            href = link_tag.get("href", "").strip()
            if href.startswith("/"):
                href = f"https://{host}.qfang.com{href}"
            href = _canonicalize_url(href)
            id_match = re.search(r"/rent/(\d+)", href)
            if not id_match:
                continue

            meta_items = [clean_text(node.get_text(" ", strip=True)) for node in card.select(".house-metas .meta-items")]
            location_block = card.select_one(".house-location .text")
            community_tag = card.select_one(".house-location a.link[href]")
            community = clean_text(community_tag.get_text(" ", strip=True)) if community_tag else ""
            location_text = clean_text(location_block.get_text(" ", strip=True)) if location_block else ""
            if community:
                location_text = location_text.replace(community, "", 1).strip()
            location_parts = [clean_text(part) for part in re.split(r"[-/]", location_text) if clean_text(part)]
            district = location_parts[0] if location_parts else ""
            bizcircle = location_parts[1] if len(location_parts) > 1 else ""
            address = " - ".join(location_parts)

            tags = [clean_text(tag.get_text(" ", strip=True)) for tag in card.select(".house-tags p")]
            rent_type_text = meta_items[4] if len(meta_items) > 4 else ""
            rent_type, normalized_rent_type = _normalize_rent_type(rent_type_text)
            price_node = card.select_one(".list-price .bigger")
            price_text = clean_text(price_node.get_text(" ", strip=True)) if price_node else ""

            image_tag = card.select_one(".photo-wrap img")
            image_url = ""
            if image_tag:
                image_url = image_tag.get("data-original") or image_tag.get("src") or ""
                image_url = clean_text(image_url)
                if image_url.startswith("//"):
                    image_url = f"https:{image_url}"

            subway_node = card.select_one(".distance")
            subway = clean_text(subway_node.get_text(" ", strip=True)) if subway_node else ""

            listing = Listing(
                provider=self.name,
                provider_name=self.display_name,
                id=id_match.group(1),
                title=clean_text(link_tag.get_text(" ", strip=True)),
                url=href,
                city_slug=city_slug,
                district=district,
                bizcircle=bizcircle,
                community=community,
                address=address,
                price=_parse_price(price_text),
                price_text=price_text,
                area_sqm=_parse_area(meta_items[1]) if len(meta_items) > 1 else None,
                layout=meta_items[0] if meta_items else "",
                floor=meta_items[3] if len(meta_items) > 3 else "",
                orientation=meta_items[5] if len(meta_items) > 5 else "",
                rent_type=rent_type,
                rent_type_text=normalized_rent_type,
                tags=tags,
                source_brand="Qfang",
                image_url=image_url,
                subway=subway,
                detail_available=False,
            )
            if len(meta_items) > 2 and meta_items[2]:
                listing.tags.append(meta_items[2])
            if len(meta_items) > 6 and meta_items[6]:
                listing.tags.append(meta_items[6])
            items.append(listing)

        if not items:
            raise ParseError("Qfang parser found no rental listings on the page.")
        return items

    def _resolve_list_url(self, city_slug: str, keyword: str) -> str:
        hinted = self._resolve_hint_url(city_slug, keyword)
        if hinted:
            return hinted

        current_url = self.build_list_url(city_slug, 1)
        for token_group in build_search_token_groups(keyword):
            html = self.http.get_text(current_url, headers=DESKTOP_HEADERS)
            next_url = select_best_route(
                collect_route_options(
                    html,
                    current_url,
                    href_predicate=lambda href: "/rent/" in href and not re.search(r"/rent/\d+", href),
                ),
                token_group,
                current_url=current_url,
            )
            if next_url:
                current_url = next_url
        return current_url

    def _resolve_hint_url(self, city_slug: str, keyword: str) -> str:
        route_map = self.ROUTE_HINTS.get(city_slug, {})
        if not route_map:
            return ""

        normalized_keyword = normalize_query_text(keyword)
        hint_path = route_map.get(normalized_keyword)
        if hint_path:
            return f"https://{self._city_host(city_slug)}.qfang.com{hint_path}"

        for token_group in build_search_token_groups(keyword):
            for token in token_group:
                hint_path = route_map.get(normalize_query_text(token))
                if hint_path:
                    return f"https://{self._city_host(city_slug)}.qfang.com{hint_path}"
        return ""
