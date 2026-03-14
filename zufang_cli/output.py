from __future__ import annotations

import json
import sys
from typing import Any, Optional

import click
import yaml
from rich.console import Console

from .constants import SCHEMA_VERSION
from .exceptions import error_code_for_exception

console = Console(stderr=True)


def wrap_envelope(data: Any = None, *, ok: bool = True, error: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    payload = {
        "ok": ok,
        "schema_version": SCHEMA_VERSION,
        "data": data if ok else None,
    }
    if not ok:
        payload["error"] = error or {}
    return payload


def print_structured(data: Any, *, as_json: bool, as_yaml: bool) -> None:
    payload = wrap_envelope(data, ok=True)
    if as_json:
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if as_yaml or not sys.stdout.isatty():
        click.echo(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def print_error(exc: Exception, *, as_json: bool, as_yaml: bool) -> None:
    code = error_code_for_exception(exc)
    if as_json or as_yaml or not sys.stdout.isatty():
        payload = wrap_envelope(
            ok=False,
            error={
                "code": code,
                "message": str(exc),
            },
        )
        if as_json:
            click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
            return
        click.echo(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
        return
    console.print(f"[red]{code}: {exc}[/red]")


def structured_output_options(command: Any) -> Any:
    command = click.option("--yaml", "as_yaml", is_flag=True, help="Output YAML envelope.")(command)
    command = click.option("--json", "as_json", is_flag=True, help="Output JSON envelope.")(command)
    return command
