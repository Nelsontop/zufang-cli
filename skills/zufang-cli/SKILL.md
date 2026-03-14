---
name: zufang-cli
description: Use when Codex needs to search Chinese rental listings with the local `zufang` CLI in this repository, compare results across Anjuke, Beike, Lianjia, Qfang, Zufun, and Leyoujia, inspect cached rows, open listing links, export search results, or debug provider-specific routing and parsing behavior.
---

# zufang-cli

## Quick Start

- Work from the repository root.
- Prefer the installed `zufang` entrypoint. If it is unavailable, run `python -m zufang_cli.cli`.
- Prefer table output for human review. Add `--json` for automation, debugging, or test assertions.
- Read [references/commands.md](references/commands.md) for concrete command patterns.

## Search Workflow

1. Run `zufang search <query> --city <city>`.
2. Add `--provider <name>` when isolating one source.
3. Add `--wide`, `--sort`, `--limit`, `--min-price`, `--max-price`, or `--rent-type` only when needed.
4. If a query returns no rows, rerun it per provider with `--json` and inspect `warnings` before changing code.

## Cached Results And Links

- Use `zufang show <index>` to inspect the latest cached search row.
- Use `zufang open <index|provider:id|url>` to open a listing link directly.
- Assume each new search refreshes the cache and can invalidate old indices.

## Debugging Rules

- Validate code changes with `python -m pytest`.
- Start provider debugging with a single provider, city, and query known to return live data.
- Treat timeouts, 502s, captcha pages, and forced login pages as source-side constraints first. Confirm them with a live request before changing parser logic.
