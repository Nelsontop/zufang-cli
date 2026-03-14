from __future__ import annotations

import csv
import json
import webbrowser
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit, urlunsplit

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..constants import PROVIDER_NAMES
from ..models import Listing, SearchOptions, SearchResult
from ..output import console, structured_output_options
from ..service import get_service
from ._common import run_command


def _provider_tuple(value: str) -> tuple[str, ...]:
    if value == "all":
        return tuple(PROVIDER_NAMES.keys())
    return (value,)


def _provider_choices() -> list[str]:
    return ["all", *PROVIDER_NAMES.keys()]


def _text_cell(value: str, *, style: str = "", justify: str = "left") -> Text:
    cell = Text(value or "-", style=style, justify=justify)
    cell.no_wrap = True
    cell.overflow = "ellipsis"
    return cell


def _price_header(sort: str) -> str:
    if sort == "price_asc":
        return "Rent \u2191"
    if sort == "price_desc":
        return "Rent \u2193"
    return "Rent"


def _display_url(value: str) -> str:
    parsed = urlsplit(value)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _price_cell(item: Listing, sort: str, index: int) -> Text:
    label = item.price_text or "-"
    style = "yellow"
    if sort == "price_asc":
        style = "bold bright_green" if index == 1 else "green"
    elif sort == "price_desc":
        style = "bold bright_red" if index == 1 else "red"
    return _text_cell(label, style=style, justify="right")


def _build_table(result: SearchResult, *, wide: bool) -> Table:
    table = Table(
        title=f"Rental search: {result.keyword or '(all)'} in {result.city_name} ({len(result.items)} items)",
        box=box.ASCII,
        show_lines=False,
        pad_edge=True,
        collapse_padding=False,
        title_justify="left",
    )
    table.add_column("#", style="dim", width=4, justify="right", no_wrap=True)
    table.add_column("Source", style="cyan", width=10, no_wrap=True)
    table.add_column("Title", style="bold", width=30 if wide else 24, overflow="ellipsis")
    table.add_column(_price_header(result.sort), width=15, justify="right", no_wrap=True)
    if wide:
        table.add_column("Layout", style="green", width=12, no_wrap=True)
        table.add_column("Area", style="magenta", width=10, justify="right", no_wrap=True)
        table.add_column("Location", style="blue", width=18, no_wrap=True)
        table.add_column("Community", style="blue", width=16, no_wrap=True)
        table.add_column("Orient", style="magenta", width=8, no_wrap=True)
        table.add_column("Floor", style="dim", width=14, no_wrap=True)
        table.add_column("Broker", style="green", width=12, no_wrap=True)
        table.add_column("Tags", style="dim", width=18, no_wrap=True)
        table.add_column("Link", style="blue", width=34, no_wrap=True)
    else:
        table.add_column("Info", style="green", width=16, no_wrap=True)
        table.add_column("Area Name", style="blue", width=22, no_wrap=True)
        table.add_column("Link", style="blue", width=28, no_wrap=True)
    return table


def _render_table(result: SearchResult, *, wide: bool = False) -> None:
    table = _build_table(result, wide=wide)
    render_console = Console(stderr=True, width=180 if wide else 140)

    for index, item in enumerate(result.items, start=1):
        area_text = f"{item.area_sqm:.1f} sqm" if item.area_sqm is not None else "-"
        area_name = " / ".join(part for part in [item.district, item.bizcircle, item.community] if part) or "-"
        location = " / ".join(part for part in [item.district, item.bizcircle] if part) or "-"
        tags = ", ".join(item.tags[:3 if wide else 4]) if item.tags else "-"
        link = _display_url(item.url)
        row = [
            _text_cell(str(index), style="dim", justify="right"),
            _text_cell(item.provider_name, style="cyan"),
            _text_cell(item.title, style="bold"),
            _price_cell(item, result.sort, index),
        ]
        if wide:
            row.extend(
                [
                    _text_cell(item.layout or "-", style="green"),
                    _text_cell(area_text, style="magenta", justify="right"),
                    _text_cell(location, style="blue"),
                    _text_cell(item.community or "-", style="blue"),
                    _text_cell(item.orientation or "-", style="magenta"),
                    _text_cell(item.floor or "-", style="dim"),
                    _text_cell(item.agent_name or item.source_brand or "-", style="green"),
                    _text_cell(tags, style="dim"),
                    _text_cell(link, style="blue"),
                ]
            )
        else:
            info_text = " / ".join(part for part in [item.layout or "-", area_text] if part) or "-"
            row.extend(
                [
                    _text_cell(info_text, style="green"),
                    _text_cell(area_name, style="blue"),
                    _text_cell(link, style="blue"),
                ]
            )
        table.add_row(*row)

    render_console.print(table)
    if result.warnings:
        for warning in result.warnings:
            render_console.print(f"[yellow]{warning}[/yellow]")
    render_console.print("[dim]Use `zufang show <index>` or `zufang open <index>` for cached detail links.[/dim]")


def _render_listing(item: Listing) -> None:
    area_text = f"{item.area_sqm:.1f} sqm" if item.area_sqm is not None else "-"
    tag_text = ", ".join(item.tags) if item.tags else "-"
    location = " / ".join(part for part in [item.city_name or item.city_slug, item.district, item.bizcircle] if part)
    panel = Panel(
        "\n".join(
            [
                f"[bold cyan]{item.title}[/bold cyan]",
                f"Provider: {item.provider_name}",
                f"Price: {item.price_text or '-'}",
                f"Layout: {item.layout or '-'}",
                f"Area: {area_text}",
                f"Floor: {item.floor or '-'}",
                f"Orientation: {item.orientation or '-'}",
                f"Rent type: {item.rent_type or '-'}",
                f"Location: {location or '-'}",
                f"Community: {item.community or '-'}",
                f"Address: {item.address or '-'}",
                f"Subway: {item.subway or '-'}",
                f"Tags: {tag_text}",
                f"Agent / Brand: {item.agent_name or item.source_brand or '-'}",
                f"URL: {item.url}",
            ]
        ),
        title=item.key,
        border_style="cyan",
    )
    console.print(panel)


def _open_reference(reference: str) -> dict[str, Any]:
    url = reference
    title = ""
    key = ""
    if not reference.startswith(("http://", "https://")):
        with get_service() as service:
            listing = service.get_cached_listing(reference)
        url = listing.url
        title = listing.title
        key = listing.key

    opened = bool(webbrowser.open(url))
    return {
        "reference": reference,
        "key": key,
        "title": title,
        "url": url,
        "opened": opened,
    }


@click.command()
@click.argument("keyword")
@click.option("-c", "--city", default="bj", help="City slug or Chinese city name, for example sz/shenzhen/\u6df1\u5733.")
@click.option("-p", "--page", default=1, type=int, help="Start page for each provider.")
@click.option("--pages", default=1, type=int, help="How many pages to fetch per provider.")
@click.option("--provider", type=click.Choice(_provider_choices()), default="all", help="Source provider.")
@click.option("--limit", default=30, type=int, help="Max items after filtering.")
@click.option("--min-price", type=int, default=None, help="Minimum monthly rent.")
@click.option("--max-price", type=int, default=None, help="Maximum monthly rent.")
@click.option("--rent-type", type=click.Choice(["all", "whole", "shared"]), default="all", help="Rent type filter.")
@click.option("--sort", type=click.Choice(["default", "price_asc", "price_desc"]), default="default", help="Sort order.")
@click.option("--wide", is_flag=True, help="Show more columns in table output.")
@structured_output_options
def search(
    keyword: str,
    city: str,
    page: int,
    pages: int,
    provider: str,
    limit: int,
    min_price: Optional[int],
    max_price: Optional[int],
    rent_type: str,
    sort: str,
    wide: bool,
    as_json: bool,
    as_yaml: bool,
) -> None:
    def _action() -> SearchResult:
        options = SearchOptions(
            keyword=keyword,
            city_slug=city,
            providers=_provider_tuple(provider),
            page=page,
            pages=pages,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            rent_type=rent_type,
            sort=sort,
        )
        with get_service() as service:
            return service.search(options)

    def _render(data: SearchResult) -> None:
        _render_table(data, wide=wide)

    run_command(_action, render=_render, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("index", type=int)
@structured_output_options
def show(index: int, as_json: bool, as_yaml: bool) -> None:
    def _action() -> Listing:
        with get_service() as service:
            return service.show(index)

    def _render(data: Listing) -> None:
        _render_listing(data)

    run_command(_action, render=_render, as_json=as_json, as_yaml=as_yaml)


@click.command(name="open")
@click.argument("reference")
@structured_output_options
def open_command(reference: str, as_json: bool, as_yaml: bool) -> None:
    def _action() -> dict[str, Any]:
        return _open_reference(reference)

    def _render(data: dict[str, Any]) -> None:
        status = "Opened" if data["opened"] else "Tried to open"
        target = data["title"] or data["url"]
        console.print(f"[green]{status}[/green] {target}")
        console.print(f"[blue]{data['url']}[/blue]")

    run_command(_action, render=_render, as_json=as_json, as_yaml=as_yaml)


@click.command()
@click.argument("keyword")
@click.option("-c", "--city", default="bj", help="City slug or Chinese city name, for example sz/shenzhen/\u6df1\u5733.")
@click.option("-p", "--page", default=1, type=int, help="Start page for each provider.")
@click.option("--pages", default=1, type=int, help="How many pages to fetch per provider.")
@click.option("--provider", type=click.Choice(_provider_choices()), default="all", help="Source provider.")
@click.option("--limit", default=50, type=int, help="Max items after filtering.")
@click.option("--min-price", type=int, default=None, help="Minimum monthly rent.")
@click.option("--max-price", type=int, default=None, help="Maximum monthly rent.")
@click.option("--rent-type", type=click.Choice(["all", "whole", "shared"]), default="all", help="Rent type filter.")
@click.option("--sort", type=click.Choice(["default", "price_asc", "price_desc"]), default="default", help="Sort order.")
@click.option("-o", "--output", "output_path", required=True, help="Output path.")
@click.option("--format", "fmt", type=click.Choice(["json", "csv"]), default="csv", help="Output format.")
def export(
    keyword: str,
    city: str,
    page: int,
    pages: int,
    provider: str,
    limit: int,
    min_price: Optional[int],
    max_price: Optional[int],
    rent_type: str,
    sort: str,
    output_path: str,
    fmt: str,
) -> None:
    with get_service() as service:
        result = service.search(
            SearchOptions(
                keyword=keyword,
                city_slug=city,
                providers=_provider_tuple(provider),
                page=page,
                pages=pages,
                limit=limit,
                min_price=min_price,
                max_price=max_price,
                rent_type=rent_type,
                sort=sort,
            )
        )

    path = Path(output_path)
    if fmt == "json":
        path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "key",
                    "provider",
                    "provider_name",
                    "title",
                    "price",
                    "price_text",
                    "layout",
                    "area_sqm",
                    "district",
                    "bizcircle",
                    "community",
                    "address",
                    "rent_type",
                    "tags",
                    "url",
                ],
                extrasaction="ignore",
            )
            writer.writeheader()
            for item in result.items:
                row = item.to_dict()
                row["tags"] = ", ".join(item.tags)
                writer.writerow(row)
    console.print(f"[green]Exported {len(result.items)} items to {path}[/green]")
