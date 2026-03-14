from __future__ import annotations

import re

from .constants import CITY_ALIASES, DEFAULT_CITY

LONG_LOCATION_SUFFIXES = (
    "\u5730\u94c1\u7ad9",
    "\u8857\u9053",
    "\u5927\u9053",
    "\u5927\u8857",
    "\u53f7\u7ebf",
    "\u5730\u94c1",
)

SHORT_LOCATION_SUFFIXES = (
    "\u533a",
    "\u53bf",
    "\u9547",
    "\u4e61",
    "\u8857",
    "\u8def",
    "\u7ad9",
)

LOCATION_SUFFIXES = LONG_LOCATION_SUFFIXES + SHORT_LOCATION_SUFFIXES


def normalize_city_slug(value: str) -> tuple[str, str]:
    key = value.strip().lower()
    if not key:
        key = DEFAULT_CITY
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    return key, key.upper()


def normalize_query_text(value: str) -> str:
    cleaned = re.sub(r"\s+", "", value)
    cleaned = re.sub(r"[ /,\-.\u00b7\uff0c\u3002(){}\[\]]+", "", cleaned)
    return cleaned.casefold()


def _add_token(bucket: list[str], seen: set[str], value: str) -> None:
    token = normalize_query_text(value)
    if token and token not in seen:
        seen.add(token)
        bucket.append(token)


def _expand_location_piece(piece: str) -> list[str]:
    variants = [piece]
    for suffix in LOCATION_SUFFIXES:
        if piece.endswith(suffix) and len(piece) - len(suffix) >= 2:
            variants.append(piece[: -len(suffix)])
            break
    return variants


def _consume_location_piece(value: str) -> tuple[str, str]:
    for index in range(1, len(value)):
        for suffix in LONG_LOCATION_SUFFIXES:
            if value.startswith(suffix, index):
                end = index + len(suffix)
                return value[:end], value[end:]

        if value[index] in SHORT_LOCATION_SUFFIXES:
            if any(value.startswith(suffix, index + 1) for suffix in LONG_LOCATION_SUFFIXES):
                continue
            end = index + 1
            return value[:end], value[end:]

    return value, ""


def build_search_token_groups(keyword: str) -> list[list[str]]:
    query = keyword.strip()
    if not query:
        return []

    groups: list[list[str]] = []
    for part in re.split(r"[\s,/\uff0c\u3001]+", query):
        part = part.strip()
        if not part:
            continue

        working = part
        while working:
            piece, working = _consume_location_piece(working.strip())
            if not piece:
                continue

            group: list[str] = []
            seen: set[str] = set()
            for variant in _expand_location_piece(piece):
                _add_token(group, seen, variant)
            if group:
                groups.append(group)

    if not groups:
        fallback: list[str] = []
        seen: set[str] = set()
        _add_token(fallback, seen, query)
        if fallback:
            groups.append(fallback)
    return groups


def build_search_tokens(keyword: str) -> list[str]:
    tokens: list[str] = []
    for group in build_search_token_groups(keyword):
        tokens.extend(group)
    return tokens


def _strip_city_prefix_alias(query: str, city_slug: str) -> str:
    for alias, (alias_slug, _city_name) in sorted(CITY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias_slug != city_slug:
            continue
        if query.casefold().startswith(alias.casefold()):
            remaining = query[len(alias) :].strip()
            return re.sub(r"\s+", " ", remaining).strip()
    return query


def infer_city_and_keyword(keyword: str, city_slug: str) -> tuple[str, str]:
    explicit_city = city_slug.strip()
    query = keyword.strip()
    if explicit_city and explicit_city.lower() != DEFAULT_CITY:
        normalized_city, _city_name = normalize_city_slug(explicit_city)
        return normalized_city, _strip_city_prefix_alias(query, normalized_city)

    for alias, (slug, _city_name) in sorted(CITY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if query.casefold().startswith(alias.casefold()):
            remaining = query[len(alias) :].strip()
            remaining = re.sub(r"\s+", " ", remaining).strip()
            return slug, remaining

    return explicit_city or DEFAULT_CITY, query
