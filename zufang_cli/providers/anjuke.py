from __future__ import annotations

import re
from html import unescape
from typing import Optional

from bs4 import BeautifulSoup

from ..constants import DESKTOP_HEADERS, PROVIDER_NAMES
from ..exceptions import ParseError, ProviderBlockedError
from ..http import HttpClient
from ..models import Listing
from .base import BaseProvider


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_price(value: str) -> Optional[int]:
    match = re.search(r"(\d+)", value.replace(",", ""))
    return int(match.group(1)) if match else None


def _parse_area(value: str) -> Optional[float]:
    match = re.search(r"([\d.]+)", value)
    return float(match.group(1)) if match else None


def _normalize_rent_type(value: str, tags: list[str]) -> tuple[str, str]:
    choices = [value, *tags]
    joined = " ".join(filter(None, choices))
    if "合租" in joined:
        return "shared", "shared"
    if "整租" in joined:
        return "whole", "whole"
    return "unknown", ""


def _clean_floor(value: str) -> str:
    cleaned = re.sub(r"\d+日内实拍验真", "", value)
    cleaned = re.sub(r"实拍验真", "", cleaned)
    return _clean(cleaned)


class AnjukeProvider(BaseProvider):
    name = "anjuke"
    display_name = PROVIDER_NAMES["anjuke"]

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    def build_list_url(self, city_slug: str, page: int) -> str:
        base = f"https://{city_slug}.zu.anjuke.com/fangyuan/"
        if page <= 1:
            return base
        return f"{base}p{page}/"

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        html = self.http.get_text(self.build_list_url(city_slug, page), headers=DESKTOP_HEADERS)
        return self.parse_list(html, city_slug)

    def parse_list(self, html: str, city_slug: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        title = _clean(soup.title.get_text()) if soup.title else ""
        if "验证码" in title or "访问过于频繁" in soup.get_text(" ", strip=True):
            raise ProviderBlockedError("Anjuke list page is asking for captcha verification.")

        items: list[Listing] = []
        for card in soup.select("div.zu-itemmod"):
            link_tag = card.select_one("h3 a[href]") or card.select_one("a.img[href]")
            if not link_tag:
                continue
            href = unescape(link_tag.get("href", ""))
            id_match = re.search(r"/fangyuan/(\d+)", href)
            if not id_match:
                continue

            detail_bits = card.select_one("p.details-item.tag")
            detail_parts: list[str] = []
            if detail_bits:
                detail_text = _clean(detail_bits.get_text(" ", strip=True))
                detail_parts = [_clean(part).replace(" ", "") for part in detail_text.split("|") if _clean(part)]

            address_tag = card.select_one("address.details-item.tag")
            community = ""
            address = ""
            district = ""
            bizcircle = ""
            if address_tag:
                community_link = address_tag.select_one("a")
                community = _clean(community_link.get_text()) if community_link else ""
                address_text = _clean(address_tag.get_text(" ", strip=True))
                address_text = address_text.replace(community, "", 1).strip()
                address_parts = [_clean(part) for part in re.split(r"[-－]", address_text) if _clean(part)]
                if address_parts:
                    district = address_parts[0]
                if len(address_parts) > 1:
                    bizcircle = address_parts[1]
                address = " - ".join(address_parts)

            tags = [_clean(tag.get_text()) for tag in card.select("p.details-item.bot-tag span")]
            rent_type, rent_type_text = _normalize_rent_type("", tags)

            price_text = _clean(card.select_one("strong.price").get_text()) if card.select_one("strong.price") else ""
            image_tag = card.select_one("img.thumbnail")
            image_url = ""
            if image_tag:
                image_url = image_tag.get("lazy_src") or image_tag.get("src") or ""

            orientation = ""
            for tag in tags:
                if any(token in tag for token in ("东", "西", "南", "北")):
                    orientation = tag
                    break

            listing = Listing(
                provider=self.name,
                provider_name=self.display_name,
                id=id_match.group(1),
                title=_clean(link_tag.get_text(" ", strip=True)),
                url=href,
                city_slug=city_slug,
                district=district,
                bizcircle=bizcircle,
                community=community,
                address=address,
                price=_parse_price(price_text),
                price_text=f"{price_text} yuan/month" if price_text else "",
                area_sqm=_parse_area(detail_parts[1]) if len(detail_parts) > 1 else None,
                layout=detail_parts[0] if detail_parts else "",
                floor=_clean_floor(detail_parts[2]) if len(detail_parts) > 2 else "",
                orientation=orientation,
                rent_type=rent_type,
                rent_type_text=rent_type_text,
                tags=tags,
                agent_name=_clean(card.select_one("span.jjr-info").get_text()) if card.select_one("span.jjr-info") else "",
                image_url=image_url,
                detail_available=False,
            )
            items.append(listing)

        if not items:
            raise ParseError("Anjuke parser found no rental listings on the page.")
        return items
