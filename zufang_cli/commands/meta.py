from __future__ import annotations

import click
from rich.table import Table

from ..output import console, structured_output_options
from ..service import get_service, list_supported_cities
from ._common import run_command


@click.command()
@structured_output_options
def providers(as_json: bool, as_yaml: bool) -> None:
    def _action() -> dict:
        with get_service() as service:
            rows = service.provider_names()
        return {
            "providers": [
                {
                    "name": name,
                    "display_name": display_name,
                    "search": True,
                    "deep_detail": False,
                }
                for name, display_name in rows
            ]
        }

    def _render(data: dict) -> None:
        table = Table(title="Providers", show_lines=False)
        table.add_column("Name", style="cyan")
        table.add_column("Display", style="green")
        table.add_column("Search", style="yellow")
        table.add_column("Deep Detail", style="dim")
        for row in data["providers"]:
            table.add_row(row["name"], row["display_name"], "yes", "best-effort only")
        console.print(table)

    run_command(_action, render=_render, as_json=as_json, as_yaml=as_yaml)


@click.command()
@structured_output_options
def cities(as_json: bool, as_yaml: bool) -> None:
    def _action() -> dict:
        return {
            "cities": [
                {
                    "slug": slug,
                    "display_name": name,
                }
                for slug, name in list_supported_cities()
            ]
        }

    def _render(data: dict) -> None:
        table = Table(title="Common City Aliases", show_lines=False)
        table.add_column("Slug", style="cyan")
        table.add_column("Display", style="green")
        for row in data["cities"]:
            table.add_row(row["slug"], row["display_name"])
        console.print(table)

    run_command(_action, render=_render, as_json=as_json, as_yaml=as_yaml)

