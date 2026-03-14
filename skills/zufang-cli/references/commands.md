# Commands

## Discovery

- List providers: `zufang providers`
- List supported cities: `zufang cities`

## Search

- All providers, table output: `zufang search 深圳市宝安区西乡 --city 深圳`
- One provider, structured output: `zufang search 宝安区西乡 --city 深圳 --provider zufun --limit 5 --json`
- Wider table: `zufang search 回龙观 --city 北京 --wide --sort price_desc`
- Price filter: `zufang search 西乡 --city 深圳 --min-price 2000 --max-price 5000`

## Cached Results

- Show row `1`: `zufang show 1`
- Open row `1`: `zufang open 1`
- Open by cache key: `zufang open zufun:181093`
- Open a raw URL: `zufang open https://sz.zufun.cn/apt/181093`

## Export

- CSV: `zufang export 西乡 --city 深圳 --provider zufun --output rent.csv`
- JSON: `zufang export 回龙观 --city 北京 --format json --output rent.json`

## Provider Notes

- `zufun` has the most reliable server-side route filtering in the current implementation.
- `qfang` may timeout or return 502 from the source site. Re-check with a live request before changing code.
- `lianjia` and `leyoujia` may hit login-protected filtered pages. The CLI can fall back to public list pages when that happens.
