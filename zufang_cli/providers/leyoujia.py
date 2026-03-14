from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from ..constants import CITY_HOST_ALIASES, DESKTOP_HEADERS, PROVIDER_NAMES
from ..exceptions import ParseError, ProviderBlockedError
from ..http import HttpClient
from ..models import Listing
from ..query import build_search_token_groups
from .base import BaseProvider
from .routing import add_query_page, clean_text, collect_route_options, select_best_route

SUPPORTED_CITY_HOSTS = {
    "sz": "shenzhen",
    "gz": "guangzhou",
    "dg": "dongguan",
    "fs": "foshan",
}


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


class LeyoujiaProvider(BaseProvider):
    name = "leyoujia"
    display_name = PROVIDER_NAMES["leyoujia"]

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    def _city_host(self, city_slug: str) -> str:
        host = SUPPORTED_CITY_HOSTS.get(city_slug)
        if host:
            return host
        mapped = CITY_HOST_ALIASES.get(city_slug)
        if mapped in SUPPORTED_CITY_HOSTS.values():
            return mapped
        raise ProviderBlockedError(f"Leyoujia does not have a configured host for city `{city_slug}`.")

    def build_list_url(self, city_slug: str, page: int) -> str:
        base = f"https://{self._city_host(city_slug)}.leyoujia.com/zf/"
        return add_query_page(base, page, name="n")

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        base_url = self._resolve_list_url(city_slug, keyword)
        filtered = urlsplit(base_url).path.rstrip("/") != "/zf"
        if filtered and page > 1:
            raise ProviderBlockedError("Leyoujia filtered pagination is unstable; only page 1 is enabled.")
        page_url = add_query_page(base_url, page, name="n")
        html = self.http.get_text(page_url, headers=DESKTOP_HEADERS)
        if filtered and self._looks_like_login(html):
            html = self.http.get_text(self.build_list_url(city_slug, page), headers=DESKTOP_HEADERS)
        return self.parse_list(html, city_slug)

    def parse_list(self, html: str, city_slug: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        title = clean_text(soup.title.get_text()) if soup.title else ""
        if self._looks_like_login(html, title=title):
            raise ProviderBlockedError("Leyoujia redirected this request to login.")

        host = self._city_host(city_slug)
        items: list[Listing] = []
        for card in soup.select(".list-box li.item"):
            link_tag = card.select_one(".tit a[href]") or card.select_one(".img a[href]")
            if not link_tag:
                continue

            href = link_tag.get("href", "").strip()
            if href.startswith("/"):
                href = f"https://{host}.leyoujia.com{href}"
            href = _canonicalize_url(href)

            house_id = link_tag.get("houseid", "").strip()
            if not house_id:
                id_match = re.search(r"/zf/detail/([^/.?]+)", href)
                if not id_match:
                    continue
                house_id = id_match.group(1)

            attr_rows = card.select("p.attr")
            first_row = [clean_text(node.get_text(" ", strip=True)) for node in attr_rows[0].select("span")] if len(attr_rows) > 0 else []
            second_row = [clean_text(node.get_text(" ", strip=True)) for node in attr_rows[1].select("span")] if len(attr_rows) > 1 else []
            third_row_links = attr_rows[2].select("a") if len(attr_rows) > 2 else []

            community = clean_text(third_row_links[0].get_text(" ", strip=True)) if third_row_links else ""
            district = clean_text(third_row_links[1].get_text(" ", strip=True)) if len(third_row_links) > 1 else ""
            bizcircle = clean_text(third_row_links[2].get_text(" ", strip=True)) if len(third_row_links) > 2 else ""
            address_parts = [part for part in [district, bizcircle] if part]
            address = " - ".join(address_parts)

            tags = [clean_text(tag.get_text(" ", strip=True)) for tag in card.select(".labs .lab")]
            subway = next((tag for tag in tags if "\u5730\u94c1" in tag or "\u53f7\u7ebf" in tag), "")

            price_block = card.select_one(".price .sup")
            price_text = clean_text(price_block.get_text(" ", strip=True)) if price_block else ""
            rent_summary_node = card.select_one(".price .sub")
            rent_summary = clean_text(rent_summary_node.get_text(" ", strip=True)) if rent_summary_node else ""
            rent_type, rent_type_text = _normalize_rent_type(rent_summary)

            image_tag = card.select_one(".img img")
            image_url = ""
            if image_tag:
                image_url = image_tag.get("data-original") or image_tag.get("src") or ""
                image_url = clean_text(image_url)

            listing = Listing(
                provider=self.name,
                provider_name=self.display_name,
                id=house_id,
                title=clean_text(link_tag.get_text(" ", strip=True)),
                url=href,
                city_slug=city_slug,
                district=district,
                bizcircle=bizcircle,
                community=community,
                address=address,
                price=_parse_price(price_text),
                price_text=price_text,
                area_sqm=_parse_area(first_row[2]) if len(first_row) > 2 else None,
                layout=first_row[0] if first_row else "",
                floor=second_row[1] if len(second_row) > 1 else "",
                orientation=first_row[1] if len(first_row) > 1 else "",
                rent_type=rent_type,
                rent_type_text=rent_type_text,
                tags=tags,
                image_url=image_url,
                subway=subway,
                detail_available=False,
            )
            if len(second_row) > 0 and second_row[0]:
                listing.tags.append(second_row[0])
            items.append(listing)

        if not items:
            raise ParseError("Leyoujia parser found no rental listings on the page.")
        return items

    def _resolve_list_url(self, city_slug: str, keyword: str) -> str:
        current_url = self.build_list_url(city_slug, 1)
        for token_group in build_search_token_groups(keyword):
            html = self.http.get_text(current_url, headers=DESKTOP_HEADERS)
            next_url = select_best_route(
                collect_route_options(
                    html,
                    current_url,
                    href_predicate=lambda href: href.startswith("/zf/a") and "/zf/detail/" not in href,
                ),
                token_group,
                current_url=current_url,
            )
            if next_url:
                current_url = next_url
        return current_url

    def _looks_like_login(self, html: str, *, title: str = "") -> bool:
        lowered_title = title.lower()
        lowered_html = html.lower()
        return "登录" in title or "loginwrap" in lowered_html or "leyoujia.com/login" in lowered_html or "<title>登录-乐有家" in html
