from __future__ import annotations

import csv
import json
from pathlib import Path

from click.testing import CliRunner

from zufang_cli.cli import cli
from zufang_cli.commands.search import _build_table
from zufang_cli.models import Listing, SearchResult

runner = CliRunner()


class FakeService:
    def __init__(self) -> None:
        self.item = Listing(
            provider="anjuke",
            provider_name="Anjuke",
            id="123",
            title="Sunny room",
            url="https://example.com/123",
            city_slug="bj",
            city_name="Beijing",
            district="Haidian",
            bizcircle="Zhongguancun",
            community="Test Home",
            address="Haidian - Zhongguancun",
            price=5200,
            price_text="5200 yuan/month",
            area_sqm=31.0,
            layout="1br",
            floor="Mid/18",
            orientation="South",
            tags=["Subway", "VR"],
            source_brand="Test Brand",
        )

    def __enter__(self) -> FakeService:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def search(self, options, progress_callback=None) -> SearchResult:
        return SearchResult(
            items=[self.item],
            warnings=[],
            city_slug="bj",
            city_name="Beijing",
            keyword=options.keyword,
            providers=["Anjuke"],
            page=options.page,
            pages=options.pages,
            sort=options.sort,
        )

    def show(self, index: int) -> Listing:
        assert index == 1
        return self.item

    def get_cached_listing(self, reference: str) -> Listing:
        assert reference in {"1", "anjuke:123"}
        return self.item

    def provider_names(self):
        return [
            ("anjuke", "Anjuke"),
            ("ke", "Beike"),
            ("lianjia", "Lianjia"),
            ("qfang", "Qfang"),
            ("zufun", "Zufun"),
            ("leyoujia", "Leyoujia"),
        ]


def test_help_lists_commands():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for command in ["search", "show", "open", "export", "providers", "cities"]:
        assert command in result.output


def test_search_json(monkeypatch):
    monkeypatch.setattr("zufang_cli.commands.search.get_service", lambda: FakeService())
    result = runner.invoke(cli, ["search", "room", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["data"]["count"] == 1
    assert payload["data"]["items"][0]["title"] == "Sunny room"


def test_search_help_has_wide():
    result = runner.invoke(cli, ["search", "--help"])
    assert result.exit_code == 0
    assert "--wide" in result.output
    assert "shenzhen" in result.output
    assert "qfang" in result.output
    assert "leyoujia" in result.output


def test_search_table_supports_wide_and_sort(monkeypatch):
    monkeypatch.setattr("zufang_cli.commands.search.get_service", lambda: FakeService())
    result = runner.invoke(cli, ["search", "room", "--wide", "--sort", "price_desc"])
    assert result.exit_code == 0
    assert "Sunny room" in result.output


def test_build_table_wide_has_extra_columns():
    service = FakeService()
    result = SearchResult(
        items=[service.item],
        warnings=[],
        city_slug="bj",
        city_name="Beijing",
        keyword="room",
        providers=["Anjuke"],
        page=1,
        pages=1,
        sort="price_desc",
    )
    table = _build_table(result, wide=True)
    headers = [column.header for column in table.columns]
    assert "Source" in headers
    assert "Broker" in headers
    assert "Floor" in headers
    assert "Orient" in headers
    assert "Link" in headers
    assert "Rent ↓" in headers


def test_show_json(monkeypatch):
    monkeypatch.setattr("zufang_cli.commands.search.get_service", lambda: FakeService())
    result = runner.invoke(cli, ["show", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["data"]["title"] == "Sunny room"


def test_open_json(monkeypatch):
    monkeypatch.setattr("zufang_cli.commands.search.get_service", lambda: FakeService())
    monkeypatch.setattr("zufang_cli.commands.search.webbrowser.open", lambda url: True)
    result = runner.invoke(cli, ["open", "1", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["data"]["url"] == "https://example.com/123"
    assert payload["data"]["opened"] is True


def test_providers_json(monkeypatch):
    monkeypatch.setattr("zufang_cli.commands.meta.get_service", lambda: FakeService())
    result = runner.invoke(cli, ["providers", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["data"]["providers"][0]["name"] == "anjuke"


def test_export_csv(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("zufang_cli.commands.search.get_service", lambda: FakeService())
    output_path = tmp_path / "rent.csv"
    result = runner.invoke(
        cli,
        ["export", "room", "--format", "csv", "--output", str(output_path)],
    )
    assert result.exit_code == 0
    rows = list(csv.DictReader(output_path.open(encoding="utf-8-sig")))
    assert len(rows) == 1
    assert rows[0]["title"] == "Sunny room"
