from __future__ import annotations

import json
from unittest.mock import MagicMock

from zufang_cli.models import Listing, SearchOptions
from zufang_cli.providers.anjuke import AnjukeProvider
from zufang_cli.providers.ke import KeProvider
from zufang_cli.providers.lianjia import LianjiaProvider
from zufang_cli.providers.leyoujia import LeyoujiaProvider
from zufang_cli.providers.qfang import QfangProvider
from zufang_cli.providers.zufun import ZufunProvider
from zufang_cli.service import ZufangService, build_search_tokens, infer_city_and_keyword, normalize_city_slug

ANJUKE_HTML = """
<html>
  <head><title>Beijing rent</title></head>
  <body>
    <div class="zu-itemmod clearfix">
      <a class="img" href="https://bj.zu.anjuke.com/fangyuan/1234567890">
        <img class="thumbnail" lazy_src="https://img.example.com/1.jpg" />
      </a>
      <div class="zu-info">
        <h3>
          <a href="https://bj.zu.anjuke.com/fangyuan/1234567890">
            <b class="strongbox">Sunny master bedroom near subway</b>
          </a>
        </h3>
        <p class="details-item tag">
          <b>3</b>室<b>1</b>厅<span>|</span><b>19</b>平米<span>|</span>低楼层(共六层)
        </p>
        <address class="details-item tag">
          <a href="https://beijing.anjuke.com/community/view/56813">Longyueyuan</a>
          Changping<span class="horiz-line">-</span>Huilongguan<span class="horiz-line">-</span>Wenhua East Rd
        </address>
        <p class="details-item bot-tag">
          <span class="cls-common">Shared</span>
          <span class="cls-common">South</span>
          <span class="cls-common">Near subway</span>
        </p>
        <p class="detail-jjr"><span class="jjr-info">Alice</span></p>
      </div>
      <div class="zu-side">
        <strong class="price">1999</strong>
        <span class="unit">yuan/month</span>
      </div>
    </div>
  </body>
</html>
"""


KE_HTML = r"""
<html>
  <body>
    <script>
      window.__TEST__ = JSON.parse(JSON.stringify([
        {
          "house_code": "BJ123",
          "house_title": "Whole rent / Test Apartment 2br",
          "house_url": "/chuzu/bj/zufang/BJ123.html",
          "hdic_district_name": "Haidian",
          "hdic_bizcircle_name": "Zhongguancun",
          "hdic_resblock_name": "Test Community",
          "address": "Haidian - Zhongguancun",
          "discount_price": "6500",
          "rent_area": "89.5",
          "house_layout": "2br1lr1bath",
          "floor_level": "Mid/18",
          "frame_orientation": "South",
          "rent_type_name": "Whole rent",
          "app_source_brand_name": "Lianjia",
          "list_picture": "https://img.example.com/2.jpg",
          "nearest_line_name": "Line 10",
          "nearest_subway_station_name": "Zhichunli",
          "house_tags": [
            {"val": "VR"},
            {"val": "Elevator"}
          ]
        }
      ]));
    </script>
  </body>
</html>
"""


QFANG_HTML = """
<html>
  <body>
    <ul>
      <li class="items clearfix">
        <div class="photo-wrap fl">
          <a class="link" href="/rent/505075787?insource=rent_list&amp;top=1" target="_blank">
            <img class="lazy-load" data-original="//img.example.com/qfang.jpg" />
          </a>
        </div>
        <div class="list-main fl">
          <div class="list-main-header clearfix">
            <a class="house-title fl" href="/rent/505075787?insource=rent_list&amp;top=1" target="_blank">宝安好房直租</a>
          </div>
          <div class="house-metas clearfix">
            <p class="meta-items">3室1厅</p>
            <p class="meta-items">90.4㎡</p>
            <p class="meta-items">精装</p>
            <p class="meta-items">低楼层(共25层)</p>
            <p class="meta-items"><a href="/rent/h1">整租</a></p>
            <p class="meta-items">东北</p>
            <p class="meta-items">有电梯</p>
          </div>
          <div class="house-location clearfix">
            <div class="text fl clearfix">
              <a class="link fl" href="/garden/desc/800160" target="_blank">桂芳园五期</a>
              宝安 - 西乡
            </div>
          </div>
          <div class="distance">距离1号线西乡站约417米</div>
          <div class="house-tags clearfix">
            <p class="default orange fl">品质物业</p>
            <p class="default fl">随时看房</p>
          </div>
        </div>
        <div class="list-price">
          <p class="bigger"><span class="amount">4600</span><span class="unit">元/月</span></p>
        </div>
      </li>
    </ul>
  </body>
</html>
"""


ZUFUN_HTML = """
<html>
  <body>
    <div class="building-item">
      <div class="ppt-wrap">
        <div class="ppt-info">
          <div class="title-wrap">
            <a href="https://sz.zufun.cn/property/114553/" target="_blank">永丰四区</a>
            <div class="label-wrap">
              <div><span class="label-name">公寓直租</span></div>
              <div><span class="label-name">无中介费</span></div>
            </div>
          </div>
          <p class="ppt-addr">
            <a class="link" href="https://sz.zufun.cn/zufang-list-c3530/" target="_blank">宝安</a> -
            <a class="link" href="https://sz.zufun.cn/zufang-list-c3530-a2934/" target="_blank">西乡</a>
            （距<a class="link" href="https://sz.zufun.cn/zufang-sub-s1-ss64/">坪洲地铁站</a>66米）
          </p>
        </div>
      </div>
      <div class="apt-items">
        <a class="apt-item link" href="https://sz.zufun.cn/apt/181093" target="_blank">
          <ul>
            <li class="col-md-2 ppt-title">整租一居</li>
            <li class="col-md-3">25平米</li>
            <li class="col-md-2">8楼</li>
            <li class="col-md-3"><span class="c-orange indent">1480</span>元/月</li>
            <li class="col-md-2 pic-wrap">
              <img alt="永丰四区整租一居" data-original="https://img.example.com/zufun.jpg" />
            </li>
          </ul>
        </a>
      </div>
    </div>
  </body>
</html>
"""


LEYOUJIA_HTML = """
<html>
  <body>
    <div class="list-box">
      <li class="item clearfix">
        <div class="img">
          <a houseid="589640" href="/zf/detail/UgRoe5bPvnPVEg5ewfdzPB" target="_blank">
            <img data-original="https://img.example.com/leyoujia.jpg" />
          </a>
        </div>
        <div class="text">
          <p class="tit">
            <a houseid="589640" href="/zf/detail/UgRoe5bPvnPVEg5ewfdzPB" target="_blank">整租 星河世纪大厦1房1厅朝南</a>
          </p>
          <p class="attr">
            <span>1房1厅1卫</span>
            <span>朝南</span>
            <span>建筑面积33.97㎡</span>
          </p>
          <p class="attr">
            <span>精装</span>
            <span>高楼层(共32层)</span>
            <span>2006年建成</span>
          </p>
          <p class="attr">
            <span><a href="/xq/detail/410" target="_blank">星河世纪大厦</a></span>
            <span>
              <a href="/zf/a5/">宝安</a> -
              <a href="/zf/a5q16/">新安</a>
            </span>
          </p>
          <p class="labs clearfix">
            <span class="lab">距1号线新安站363米</span>
            <span class="lab">拎包入住</span>
          </p>
        </div>
        <div class="price">
          <p class="sup"><span class="salePrice">5500</span>元/月</p>
          <p class="sub">整租 | 押二付一</p>
        </div>
      </li>
    </div>
  </body>
</html>
"""


QFANG_ROUTE_BASE = """
<html><body>
  <a href="/rent/nanshan">南山</a>
  <a href="/rent/baoan">宝安</a>
</body></html>
"""

QFANG_ROUTE_BAOAN = """
<html><body>
  <a href="/rent/baoan-xixiang">西乡</a>
  <a href="/rent/baoan-xinan">新安</a>
</body></html>
"""

ZUFUN_ROUTE_BASE = """
<html><body>
  <a href="https://sz.zufun.cn/zufang-list-c3530/">宝安</a>
</body></html>
"""

ZUFUN_ROUTE_BAOAN = """
<html><body>
  <a href="https://sz.zufun.cn/zufang-list-c3530-a2934/">西乡</a>
</body></html>
"""

LEYOUJIA_ROUTE_BASE = """
<html><body>
  <a href="/zf/a5/">宝安</a>
  <a href="/zf/a3/">南山</a>
</body></html>
"""

LEYOUJIA_ROUTE_BAOAN = """
<html><body>
  <a href="/zf/a5q16/">新安</a>
  <a href="/zf/a5q11/">西乡</a>
</body></html>
"""


class MappingHttp:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def get_text(self, url: str, **_: object) -> str:
        if url in self.mapping:
            return self.mapping[url]
        raise AssertionError(f"Unexpected URL: {url}")

    def close(self) -> None:
        return None


class LianjiaSuggestHttp:
    def get_text(self, url: str, **_: object) -> str:
        if "query=%E5%AE%9D%E5%AE%89%E5%8C%BA" in url:
            return json.dumps(
                {
                    "data": [
                        {
                            "type": "district",
                            "name": "宝安区",
                            "uri": "/chuzu/sz/zufang/baoanqu/?sug=%E5%AE%9D%E5%AE%89%E5%8C%BA",
                            "count": 4101,
                        }
                    ]
                }
            )
        if "query=%E8%A5%BF%E4%B9%A1" in url:
            return json.dumps(
                {
                    "data": [
                        {
                            "type": "bizcircle",
                            "name": "西乡",
                            "uri": "/chuzu/sz/zufang/baoanqu/xixiang/?sug=%E8%A5%BF%E4%B9%A1",
                            "count": 1024,
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    def close(self) -> None:
        return None


def test_anjuke_parser_extracts_listing():
    provider = AnjukeProvider(MagicMock())
    items = provider.parse_list(ANJUKE_HTML, "bj")
    assert len(items) == 1
    item = items[0]
    assert item.id == "1234567890"
    assert item.provider == "anjuke"
    assert item.title == "Sunny master bedroom near subway"
    assert item.price == 1999
    assert item.community == "Longyueyuan"
    assert item.district == "Changping"
    assert item.bizcircle == "Huilongguan"
    assert item.agent_name == "Alice"


def test_ke_parser_extracts_listing():
    provider = KeProvider(MagicMock())
    items = provider.parse_list(KE_HTML, "bj")
    assert len(items) == 1
    item = items[0]
    assert item.id == "BJ123"
    assert item.provider == "ke"
    assert item.price == 6500
    assert item.area_sqm == 89.5
    assert item.community == "Test Community"
    assert item.subway == "Line 10 Zhichunli"
    assert item.tags == ["VR", "Elevator"]


def test_lianjia_parser_extracts_listing():
    provider = LianjiaProvider(MagicMock())
    items = provider.parse_list(KE_HTML, "sz")
    assert len(items) == 1
    item = items[0]
    assert item.provider == "lianjia"
    assert item.url == "https://m.lianjia.com/chuzu/bj/zufang/BJ123.html"


def test_qfang_parser_extracts_listing():
    provider = QfangProvider(MagicMock())
    items = provider.parse_list(QFANG_HTML, "sz")
    assert len(items) == 1
    item = items[0]
    assert item.id == "505075787"
    assert item.provider == "qfang"
    assert item.community == "桂芳园五期"
    assert item.district == "宝安"
    assert item.bizcircle == "西乡"
    assert item.price == 4600
    assert item.orientation == "东北"
    assert item.subway == "距离1号线西乡站约417米"
    assert item.url == "https://shenzhen.qfang.com/rent/505075787"


def test_zufun_parser_extracts_listing():
    provider = ZufunProvider(MagicMock())
    items = provider.parse_list(ZUFUN_HTML, "sz")
    assert len(items) == 1
    item = items[0]
    assert item.id == "181093"
    assert item.provider == "zufun"
    assert item.community == "永丰四区"
    assert item.district == "宝安"
    assert item.bizcircle == "西乡"
    assert item.subway == "坪洲地铁站"
    assert item.price == 1480
    assert item.layout == "整租一居"


def test_leyoujia_parser_extracts_listing():
    provider = LeyoujiaProvider(MagicMock())
    items = provider.parse_list(LEYOUJIA_HTML, "sz")
    assert len(items) == 1
    item = items[0]
    assert item.id == "589640"
    assert item.provider == "leyoujia"
    assert item.community == "星河世纪大厦"
    assert item.district == "宝安"
    assert item.bizcircle == "新安"
    assert item.price == 5500
    assert item.orientation == "朝南"
    assert item.url == "https://shenzhen.leyoujia.com/zf/detail/UgRoe5bPvnPVEg5ewfdzPB"


def test_qfang_resolves_server_side_route():
    provider = QfangProvider(MappingHttp({
        "https://shenzhen.qfang.com/rent": QFANG_ROUTE_BASE,
        "https://shenzhen.qfang.com/rent/baoan": QFANG_ROUTE_BAOAN,
    }))
    assert provider._resolve_list_url("sz", "宝安区西乡") == "https://shenzhen.qfang.com/rent/baoan-xixiang"


def test_zufun_resolves_server_side_route():
    provider = ZufunProvider(MappingHttp({
        "https://sz.zufun.cn/zufang-list/": ZUFUN_ROUTE_BASE,
        "https://sz.zufun.cn/zufang-list-c3530/": ZUFUN_ROUTE_BAOAN,
    }))
    assert provider._resolve_list_url("sz", "宝安区西乡") == "https://sz.zufun.cn/zufang-list-c3530-a2934/"


def test_leyoujia_resolves_server_side_route():
    provider = LeyoujiaProvider(MappingHttp({
        "https://shenzhen.leyoujia.com/zf/": LEYOUJIA_ROUTE_BASE,
        "https://shenzhen.leyoujia.com/zf/a5/": LEYOUJIA_ROUTE_BAOAN,
    }))
    assert provider._resolve_list_url("sz", "宝安区西乡") == "https://shenzhen.leyoujia.com/zf/a5q11/"


def test_lianjia_resolves_server_side_route_from_suggest():
    provider = LianjiaProvider(LianjiaSuggestHttp())
    assert provider._resolve_filtered_url("sz", "宝安区西乡") == "https://m.lianjia.com/chuzu/sz/zufang/baoanqu/xixiang/?sug=%E8%A5%BF%E4%B9%A1"


def test_infer_city_and_keyword_from_chinese_location_phrase():
    city, keyword = infer_city_and_keyword("深圳市宝安区", "bj")
    assert city == "sz"
    assert keyword == "宝安区"


def test_infer_city_and_keyword_from_city_district_and_street_phrase():
    city, keyword = infer_city_and_keyword("深圳市宝安区西乡", "bj")
    assert city == "sz"
    assert keyword == "宝安区西乡"


def test_infer_city_and_keyword_with_explicit_chinese_city_strips_duplicate_prefix():
    city, keyword = infer_city_and_keyword("深圳市宝安区西乡", "深圳")
    assert city == "sz"
    assert keyword == "宝安区西乡"


def test_build_search_tokens_splits_location_phrase():
    tokens = build_search_tokens("宝安区西乡街道桥头地铁站")
    assert "宝安区" in tokens
    assert "宝安" in tokens
    assert "西乡街道" in tokens
    assert "西乡" in tokens
    assert "桥头地铁站" in tokens
    assert "桥头" in tokens


def test_normalize_city_slug_accepts_chinese_city_alias():
    slug, city_name = normalize_city_slug("深圳")
    assert slug == "sz"
    assert city_name == "Shenzhen"


def test_filter_matches_location_tokens_across_fields():
    service = ZufangService(http_client=MagicMock())
    item = Listing(
        provider="ke",
        provider_name="Beike",
        id="SZ1",
        title="整租 测试房源",
        url="https://example.com",
        city_slug="sz",
        city_name="Shenzhen",
        district="宝安区",
        bizcircle="西乡",
        community="测试小区",
        address="宝安区 - 西乡",
        subway="11号线 桥头",
        price=3200,
        price_text="3200 yuan/month",
    )
    assert service._filter_items([item], "宝安区西乡", None, None, "all") == [item]
    assert service._filter_items([item], "桥头地铁站", None, None, "all") == [item]
    service.close()


def test_service_reports_progress_updates():
    service = ZufangService(http_client=MagicMock())
    service.providers = {
        "anjuke": MagicMock(
            display_name="Anjuke",
            search_page=MagicMock(
                return_value=[
                    Listing(
                        provider="anjuke",
                        provider_name="Anjuke",
                        id="123",
                        title="Sunny room",
                        url="https://example.com/123",
                        city_slug="bj",
                        price=5200,
                        price_text="5200 yuan/month",
                    )
                ]
            ),
        )
    }
    states = []
    result = service.search(
        SearchOptions(keyword="room", city_slug="bj", providers=("anjuke",), pages=1),
        progress_callback=states.append,
    )
    assert result.items[0].city_name == "Beijing"
    assert len(states) == 1
    assert states[0].completed == 1
    assert states[0].total == 1
    assert states[0].provider == "anjuke"
    assert states[0].provider_name == "Anjuke"
    assert states[0].page == 1
    service.close()
