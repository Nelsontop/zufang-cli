# zufang-cli

[English README](./README.md)

面向中文租房网站的跨平台租房搜索 CLI。

当前支持的数据源：
- 安居客
- 贝壳
- 链家
- Q房网
- 自如寓系租房网（`zufun`）
- 乐有家

## 功能

- 一条命令聚合多个租房平台的房源
- 默认表格输出，展示数据来源和详情链接
- 支持 `--json` 和 `--yaml` 结构化输出
- 支持中文城市参数，例如 `--city 深圳`
- 支持自然语言地点短语拆词，例如 `深圳市宝安区西乡`
- 支持价格、租赁方式、页数、数据源等筛选
- 支持 `show` 查看最近一次搜索缓存中的房源详情
- 支持 `open` 直接打开缓存中的详情链接
- 支持 `export` 导出 CSV 或 JSON
- `search` 过程中支持百分比进度条

## 安装

要求 Python `3.9+`。

```bash
pip install -e .
```

安装后执行：

```bash
zufang --help
```

## 常用命令

```bash
zufang providers
zufang cities
zufang search 深圳市宝安区西乡 --city 深圳
zufang search 西乡 --city 深圳 --provider zufun --limit 5
zufang search 回龙观 --city 北京 --sort price_desc --wide
zufang show 1
zufang open 1
zufang export 西乡 --city 深圳 --provider zufun --output rent.csv
```

## 搜索输出

- 默认输出为表格
- `--wide` 展示更多列
- `--json` 和 `--yaml` 切换为结构化输出
- 在交互式终端中执行 `search` 时，会显示按 `provider × page` 计算的百分比进度条
- 结构化输出模式不会显示进度条，避免污染机器可读结果

示例：

```bash
zufang search 宝安区西乡 --city 深圳 --provider zufun --limit 5
```

## 常用参数

```bash
zufang search 关键词 \
  --city 深圳 \
  --provider all \
  --pages 1 \
  --limit 30 \
  --min-price 2000 \
  --max-price 5000 \
  --rent-type whole \
  --sort price_asc \
  --wide
```

## 数据源说明

- `zufun` 目前服务端筛选路径最稳定
- `qfang` 源站可能会超时或直接返回 `502`
- `lianjia` 和 `leyoujia` 的筛选页可能会跳转到登录保护页
- 当某个数据源本身不稳定时，即使查询有效，也可能返回较少结果或空结果

## 开发

运行测试：

```bash
python -m pytest
```

主要入口：

- `zufang_cli/cli.py`
- `zufang_cli/commands/search.py`
- `zufang_cli/service.py`
