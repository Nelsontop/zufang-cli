from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from ..query import normalize_query_text


@dataclass(frozen=True)
class RouteOption:
    label: str
    url: str
    normalized_label: str


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_route_label(value: str) -> str:
    cleaned = clean_text(value)
    cleaned = re.sub(r"\(\d+\)$", "", cleaned)
    cleaned = re.sub(r"^[^\u4e00-\u9fffA-Za-z0-9]+", "", cleaned)
    cleaned = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]+", "", cleaned)
    return normalize_query_text(cleaned)


def collect_route_options(
    html: str,
    base_url: str,
    *,
    href_predicate: Callable[[str], bool],
    selector: str = "a[href]",
) -> list[RouteOption]:
    soup = BeautifulSoup(html, "html.parser")
    options: list[RouteOption] = []
    seen: set[tuple[str, str]] = set()
    for anchor in soup.select(selector):
        href = anchor.get("href", "").strip()
        if not href or not href_predicate(href):
            continue

        normalized_label = normalize_route_label(anchor.get_text(" ", strip=True))
        if not normalized_label:
            continue

        resolved_url = urljoin(base_url, href)
        key = (normalized_label, resolved_url)
        if key in seen:
            continue
        seen.add(key)
        options.append(
            RouteOption(
                label=clean_text(anchor.get_text(" ", strip=True)),
                url=resolved_url,
                normalized_label=normalized_label,
            )
        )
    return options


def select_best_route(options: Iterable[RouteOption], token_group: list[str], *, current_url: str = "") -> Optional[str]:
    best_url: Optional[str] = None
    best_score = 0
    current_path = urlsplit(current_url).path.rstrip("/")
    for option in options:
        for index, candidate in enumerate(token_group):
            candidate_norm = normalize_query_text(candidate)
            score = _route_score(option.normalized_label, candidate_norm, index)
            if score <= 0:
                continue
            option_path = urlsplit(option.url).path.rstrip("/")
            if current_path and option_path.startswith(current_path) and option_path != current_path:
                score += 25
            if score > best_score:
                best_score = score
                best_url = option.url
    return best_url


def add_query_page(url: str, page: int, *, name: str = "page") -> str:
    if page <= 1:
        return url
    parsed = urlsplit(url)
    query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_items[name] = str(page)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query_items), ""))


def add_path_page(url: str, page: int, *, prefix: str = "page") -> str:
    if page <= 1:
        return url
    normalized = url.rstrip("/") + "/"
    return urljoin(normalized, f"{prefix}{page}/")


def _route_score(label_norm: str, candidate_norm: str, candidate_index: int) -> int:
    if not label_norm or not candidate_norm:
        return 0
    if len(label_norm) < 2:
        return 0
    penalty = candidate_index * 2
    if label_norm == candidate_norm:
        return 120 - penalty + len(label_norm)
    if label_norm in candidate_norm:
        return 100 - penalty + len(label_norm)
    if candidate_norm in label_norm:
        return 90 - penalty + len(candidate_norm)
    if label_norm.startswith(candidate_norm) or candidate_norm.startswith(label_norm):
        return 80 - penalty + min(len(label_norm), len(candidate_norm))
    return 0
