"""
Made-in-China 采集器
- 产品标题
- 相关搜索词
"""
import json
import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class MadeinchinaCollector(BaseCollector):
    """Made-in-China.com 关键词采集器"""

    CHANNEL_NAME = "madeinchina"
    SEARCH_URL = "https://www.made-in-china.com/multi-search/{keyword}/F1/"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Made-in-China] 开始采集: %s", self.root_keyword)
        self._collect_product_titles()
        logger.info("[Made-in-China] 完成，共采集 %d 条", len(self.results))
        return self.results

    def _collect_product_titles(self) -> None:
        """采集 Made-in-China 产品标题和相关搜索词"""
        keyword_slug = self.root_keyword.replace(" ", "-")
        url = self.SEARCH_URL.format(keyword=quote_plus(keyword_slug))

        resp = self._get(url)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        # 产品标题
        title_selectors = [
            "h2.product-name",
            "div.product-title a",
            "span.product-name",
            "a.title",
        ]
        for sel in title_selectors:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if text and len(text) > 5:
                    self._add_keyword(
                        text,
                        source="madeinchina_product_title",
                        url=url,
                    )

        # 相关搜索词
        for el in soup.select("div.related-search a, div.hot-search a"):
            text = el.get_text(strip=True)
            if text:
                self._add_keyword(text, source="madeinchina_related")

        # 分类导航词
        for el in soup.select("ul.category-list a, div.filter-item a"):
            text = el.get_text(strip=True)
            if text and len(text) > 3:
                self._add_keyword(text, source="madeinchina_category")

        # 扩展：第 2 页
        self._sleep()
        url2 = self.SEARCH_URL.format(keyword=quote_plus(keyword_slug)) + "?pageNum=2"
        resp2 = self._get(url2)
        if resp2:
            soup2 = BeautifulSoup(resp2.text, "html.parser")
            for sel in title_selectors:
                for el in soup2.select(sel):
                    text = el.get_text(strip=True)
                    if text and len(text) > 5:
                        self._add_keyword(text, source="madeinchina_product_title")
