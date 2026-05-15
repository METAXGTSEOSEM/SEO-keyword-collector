"""
Alibaba 采集器
- Alibaba 搜索建议词
- Alibaba 产品标题（关键词提取）
"""
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class AlibabaCollector(BaseCollector):
    """Alibaba.com 关键词采集器"""

    CHANNEL_NAME = "alibaba"
    SUGGEST_URL = "https://www.alibaba.com/search/suggest_new"
    SEARCH_URL = "https://www.alibaba.com/trade/search"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Alibaba] 开始采集: %s", self.root_keyword)
        self._collect_suggest()
        self._collect_product_titles()
        logger.info("[Alibaba] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── Alibaba Suggest ───────────────────────────────────────
    def _collect_suggest(self) -> None:
        """采集 Alibaba 搜索建议"""
        params = {
            "keyword": self.root_keyword,
            "country": "US",
            "lang": "en",
        }
        resp = self._get(self.SUGGEST_URL, params=params)
        if not resp:
            return
        try:
            data = resp.json()
            for item in data.get("result", {}).get("list", []):
                kw = item.get("keyword", "")
                if kw:
                    self._add_keyword(kw, source="alibaba_suggest")
        except Exception as exc:
            logger.warning("[Alibaba Suggest] 解析失败: %s", exc)
            # 备用：尝试 HTML 解析
            self._collect_suggest_html()

    def _collect_suggest_html(self) -> None:
        """备用：HTML 方式采集 Alibaba Suggest"""
        url = f"https://www.alibaba.com/Products/{quote_plus(self.root_keyword)}.html"
        resp = self._get(url)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")
        # 产品标题
        for el in soup.select("h2.organic-gallery-title__outter, h2.search-card-e-title"):
            text = el.get_text(strip=True)
            if text:
                self._add_keyword(text, source="alibaba_title_html")

    # ─── Alibaba 产品标题 ──────────────────────────────────────
    def _collect_product_titles(self) -> None:
        """采集 Alibaba 搜索结果中的产品标题"""
        params = {
            "fsb": "y",
            "IndexArea": "product_en",
            "keywords": self.root_keyword,
            "tab": "all",
            "page": "1",
        }
        resp = self._get(self.SEARCH_URL, params=params)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        # 尝试多种选择器
        selectors = [
            "h2.organic-gallery-title__outter",
            "h2.search-card-e-title",
            "div.search-card-e-title span",
            "a.elements-title-normal__outter",
        ]
        for sel in selectors:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if text and len(text) > 5:
                    self._add_keyword(
                        text,
                        source="alibaba_product_title",
                        url=self.SEARCH_URL,
                    )

        # 从 JSON-LD 提取
        for script in soup.find_all("script", type="application/json"):
            try:
                data = json.loads(script.string)
                for item in data if isinstance(data, list) else [data]:
                    name = item.get("name", "")
                    if name:
                        self._add_keyword(name, source="alibaba_jsonld")
            except Exception:
                pass
