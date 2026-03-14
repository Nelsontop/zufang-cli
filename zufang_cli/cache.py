from __future__ import annotations

import json
import time
from typing import Any

from .constants import CONFIG_DIR, INDEX_CACHE_FILE
from .exceptions import CacheMissError
from .models import Listing


def save_index(items: list[Listing], source: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source,
        "saved_at": time.time(),
        "count": len(items),
        "items": [item.to_dict() for item in items],
    }
    INDEX_CACHE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_payload() -> dict[str, Any]:
    if not INDEX_CACHE_FILE.exists():
        raise CacheMissError("No cached search results. Run `zufang search` first.")
    try:
        return json.loads(INDEX_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CacheMissError("Cached results are unreadable.") from exc


def get_by_index(index: int) -> Listing:
    payload = _load_payload()
    items = payload.get("items", [])
    if index <= 0 or index > len(items):
        raise CacheMissError(f"Index {index} is outside cached result range (1..{len(items)}).")
    return Listing(**{k: v for k, v in items[index - 1].items() if k != "key"})


def get_by_key(key: str) -> Listing:
    payload = _load_payload()
    for item in payload.get("items", []):
        if item.get("key") == key:
            return Listing(**{k: v for k, v in item.items() if k != "key"})
    raise CacheMissError(f"Cached result {key!r} not found.")


def get_cache_info() -> dict[str, Any]:
    try:
        payload = _load_payload()
    except CacheMissError:
        return {"exists": False, "count": 0}
    return {
        "exists": True,
        "count": payload.get("count", 0),
        "source": payload.get("source", ""),
        "saved_at": payload.get("saved_at", 0),
    }

