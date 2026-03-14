from __future__ import annotations

from pathlib import Path

APP_NAME = "zufang-cli"
SCHEMA_VERSION = "1"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
INDEX_CACHE_FILE = CONFIG_DIR / "index_cache.json"

PROVIDER_NAMES = {
    "anjuke": "Anjuke",
    "ke": "Beike",
    "lianjia": "Lianjia",
    "qfang": "Qfang",
    "zufun": "Zufun",
    "leyoujia": "Leyoujia",
}

CITY_HOST_ALIASES = {
    "bj": "beijing",
    "sh": "shanghai",
    "gz": "guangzhou",
    "sz": "shenzhen",
    "hz": "hangzhou",
    "nj": "nanjing",
    "cd": "chengdu",
    "cq": "chongqing",
    "wh": "wuhan",
    "tj": "tianjin",
    "xa": "xian",
    "su": "suzhou",
    "fs": "foshan",
    "dg": "dongguan",
    "cs": "changsha",
    "qd": "qingdao",
}

DEFAULT_CITY = "bj"
DEFAULT_LIMIT = 30
DEFAULT_PAGES = 1
DEFAULT_TIMEOUT = 20.0
DEFAULT_DELAY = 0.6
DEFAULT_MAX_RETRIES = 2

RENT_TYPE_LABELS = {
    "all": "all",
    "whole": "whole",
    "shared": "shared",
}

CITY_ALIASES = {
    "bj": ("bj", "Beijing"),
    "beijing": ("bj", "Beijing"),
    "beijingshi": ("bj", "Beijing"),
    "北京": ("bj", "Beijing"),
    "北京市": ("bj", "Beijing"),
    "sh": ("sh", "Shanghai"),
    "shanghai": ("sh", "Shanghai"),
    "上海": ("sh", "Shanghai"),
    "上海市": ("sh", "Shanghai"),
    "gz": ("gz", "Guangzhou"),
    "guangzhou": ("gz", "Guangzhou"),
    "广州": ("gz", "Guangzhou"),
    "广州市": ("gz", "Guangzhou"),
    "sz": ("sz", "Shenzhen"),
    "shenzhen": ("sz", "Shenzhen"),
    "深圳": ("sz", "Shenzhen"),
    "深圳市": ("sz", "Shenzhen"),
    "hz": ("hz", "Hangzhou"),
    "hangzhou": ("hz", "Hangzhou"),
    "杭州": ("hz", "Hangzhou"),
    "杭州市": ("hz", "Hangzhou"),
    "nj": ("nj", "Nanjing"),
    "nanjing": ("nj", "Nanjing"),
    "南京": ("nj", "Nanjing"),
    "南京市": ("nj", "Nanjing"),
    "cd": ("cd", "Chengdu"),
    "chengdu": ("cd", "Chengdu"),
    "成都": ("cd", "Chengdu"),
    "成都市": ("cd", "Chengdu"),
    "cq": ("cq", "Chongqing"),
    "chongqing": ("cq", "Chongqing"),
    "重庆": ("cq", "Chongqing"),
    "重庆市": ("cq", "Chongqing"),
    "wh": ("wh", "Wuhan"),
    "wuhan": ("wh", "Wuhan"),
    "武汉": ("wh", "Wuhan"),
    "武汉市": ("wh", "Wuhan"),
    "tj": ("tj", "Tianjin"),
    "tianjin": ("tj", "Tianjin"),
    "天津": ("tj", "Tianjin"),
    "天津市": ("tj", "Tianjin"),
    "xa": ("xa", "Xi'an"),
    "xian": ("xa", "Xi'an"),
    "西安": ("xa", "Xi'an"),
    "西安市": ("xa", "Xi'an"),
    "su": ("su", "Suzhou"),
    "suzhou": ("su", "Suzhou"),
    "苏州": ("su", "Suzhou"),
    "苏州市": ("su", "Suzhou"),
    "fs": ("fs", "Foshan"),
    "foshan": ("fs", "Foshan"),
    "佛山": ("fs", "Foshan"),
    "佛山市": ("fs", "Foshan"),
    "dg": ("dg", "Dongguan"),
    "dongguan": ("dg", "Dongguan"),
    "东莞": ("dg", "Dongguan"),
    "东莞市": ("dg", "Dongguan"),
    "cs": ("cs", "Changsha"),
    "changsha": ("cs", "Changsha"),
    "长沙": ("cs", "Changsha"),
    "长沙市": ("cs", "Changsha"),
    "qd": ("qd", "Qingdao"),
    "qingdao": ("qd", "Qingdao"),
    "青岛": ("qd", "Qingdao"),
    "青岛市": ("qd", "Qingdao"),
}

COMMON_CITIES = [
    ("bj", "Beijing"),
    ("sh", "Shanghai"),
    ("gz", "Guangzhou"),
    ("sz", "Shenzhen"),
    ("hz", "Hangzhou"),
    ("nj", "Nanjing"),
    ("cd", "Chengdu"),
    ("cq", "Chongqing"),
    ("wh", "Wuhan"),
    ("tj", "Tianjin"),
    ("xa", "Xi'an"),
    ("su", "Suzhou"),
    ("fs", "Foshan"),
    ("dg", "Dongguan"),
    ("cs", "Changsha"),
    ("qd", "Qingdao"),
]

DESKTOP_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}

MOBILE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
        "Mobile/15E148 Safari/604.1"
    ),
}
