from __future__ import annotations

import json
from urllib.parse import urlencode, urljoin, urlsplit

from ..constants import MOBILE_HEADERS, PROVIDER_NAMES
from ..exceptions import ParseError
from ..models import Listing
from ..query import build_search_token_groups, normalize_query_text
from .beike_like import BeikeLikeProvider


class LianjiaProvider(BeikeLikeProvider):
    name = "lianjia"
    display_name = PROVIDER_NAMES["lianjia"]
    host = "m.lianjia.com"

    CITY_IDS = {
        "bj": "110000",
        "sh": "310000",
        "gz": "440100",
        "sz": "440300",
        "hz": "330100",
        "nj": "320100",
        "cd": "510100",
        "cq": "500000",
        "wh": "420100",
        "tj": "120000",
        "xa": "610100",
        "su": "320500",
        "fs": "440600",
        "dg": "441900",
        "cs": "430100",
        "qd": "370200",
    }

    TYPE_SCORES = {
        "bizcircle": 80,
        "district": 70,
        "station": 65,
        "subway_station": 65,
        "subway": 60,
        "resblock": 30,
    }

    def search_page(self, city_slug: str, page: int, keyword: str = "") -> list[Listing]:
        base_url = self.build_list_url(city_slug, page)
        if not keyword:
            html = self.http.get_text(base_url, headers=MOBILE_HEADERS)
            return self.parse_list(html, city_slug)

        filtered_url = self._resolve_filtered_url(city_slug, keyword)
        page_url = self._paginate_url(filtered_url, page)
        html = self.http.get_text(page_url, headers=MOBILE_HEADERS)
        if self._looks_like_login(html):
            html = self.http.get_text(base_url, headers=MOBILE_HEADERS)
            return self.parse_list(html, city_slug)
        try:
            return self.parse_list(html, city_slug)
        except ParseError:
            if filtered_url == self.build_list_url(city_slug, 1):
                raise
            html = self.http.get_text(base_url, headers=MOBILE_HEADERS)
            return self.parse_list(html, city_slug)

    def _resolve_filtered_url(self, city_slug: str, keyword: str) -> str:
        current_url = self.build_list_url(city_slug, 1)
        city_id = self.CITY_IDS.get(city_slug)
        if not city_id:
            return current_url

        for token_group in build_search_token_groups(keyword):
            next_url = self._resolve_group_url(city_slug, city_id, token_group, current_url)
            if next_url:
                current_url = next_url
        return current_url

    def _resolve_group_url(self, city_slug: str, city_id: str, token_group: list[str], current_url: str) -> str:
        seen: set[str] = set()
        for token in token_group:
            if token in seen:
                continue
            seen.add(token)
            suggestion = self._suggest(city_slug, city_id, token, current_url)
            if suggestion:
                return suggestion
        return ""

    def _suggest(self, city_slug: str, city_id: str, query: str, current_url: str) -> str:
        params = urlencode(
            {
                "city_id": city_id,
                "channel": "rent",
                "query": query,
                "rt": "",
                "source": "",
            }
        )
        url = f"https://{self.host}/chuzu/{city_slug}/suggest?{params}"
        text = self.http.get_text(url, headers=MOBILE_HEADERS)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return ""

        current_path = urlsplit(current_url).path.rstrip("/")
        best_uri = ""
        best_score = 0
        query_norm = normalize_query_text(query)
        for item in payload.get("data", []):
            uri = str(item.get("uri", "")).strip()
            if not uri:
                continue
            name_norm = normalize_query_text(str(item.get("name", "")))
            score = self.TYPE_SCORES.get(str(item.get("type", "")), 10)
            count = int(item.get("count") or 0)
            if count > 0:
                score += min(count, 5000) // 500
            if name_norm == query_norm:
                score += 40
            elif name_norm in query_norm or query_norm in name_norm:
                score += 25
            uri_path = urlsplit(uri).path.rstrip("/")
            if current_path and uri_path.startswith(current_path) and uri_path != current_path:
                score += 30
            if score > best_score:
                best_score = score
                best_uri = uri
        if not best_uri:
            return ""
        return urljoin(f"https://{self.host}", best_uri)

    def _paginate_url(self, url: str, page: int) -> str:
        if page <= 1:
            return url
        return url.rstrip("/") + f"/pg{page}/"

    def _looks_like_login(self, html: str) -> bool:
        return "clogin.lianjia.com/login" in html.lower()
