# zufang-cli

[中文文档](./README.zh-CN.md)

Cross-provider rental listing CLI for Chinese rental sites.

Current providers:
- Anjuke
- Beike
- Lianjia
- Qfang
- Zufun
- Leyoujia

## Features

- Search rental listings across multiple providers with one command
- Default table output with source and detail link columns
- `--json` and `--yaml` structured output for automation
- Chinese city input such as `--city Shenzhen` or `--city sz`
- Query splitting for phrases such as `Shenzhen Baoan Xixiang` or Chinese location phrases
- Price, rent type, page count, and provider filters
- `show` for cached result details
- `open` for opening a cached listing link directly
- `export` to CSV or JSON
- Interactive progress bar during `search`

## Install

Python `3.9+` is required.

```bash
pip install -e .
```

After install:

```bash
zufang --help
```

## Commands

```bash
zufang providers
zufang cities
zufang search "Baoan Xixiang" --city sz
zufang search Xixiang --city sz --provider zufun --limit 5
zufang search Huilongguan --city bj --sort price_desc --wide
zufang show 1
zufang open 1
zufang export Xixiang --city sz --provider zufun --output rent.csv
```

## Search Output

- Default output is a table
- `--wide` shows more columns
- `--json` and `--yaml` switch to structured output
- Interactive terminal runs show a percentage progress bar while providers and pages are being fetched
- Structured output mode does not show the progress bar, to avoid corrupting machine-readable output

Example:

```bash
zufang search "Baoan Xixiang" --city sz --provider zufun --limit 5
```

## Common Options

```bash
zufang search KEYWORD \
  --city sz \
  --provider all \
  --pages 1 \
  --limit 30 \
  --min-price 2000 \
  --max-price 5000 \
  --rent-type whole \
  --sort price_asc \
  --wide
```

## Provider Notes

- `zufun` currently has the most reliable server-side route filtering
- `qfang` may timeout or return `502` from the source site
- `lianjia` and `leyoujia` filtered pages may redirect to login-protected pages
- When a provider is unstable, the CLI may return fewer rows or no rows even if the query is valid

## Development

Run tests:

```bash
python -m pytest
```

Project entrypoint:

- `zufang_cli/cli.py`

Main search command:

- `zufang_cli/commands/search.py`

Search service:

- `zufang_cli/service.py`
