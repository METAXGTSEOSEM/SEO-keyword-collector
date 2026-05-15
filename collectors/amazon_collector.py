"""
Amazon 采集器
- Amazon 搜索建议词
"""
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class AmazonCollector(BaseCollector):
    """Amazon 关键词采集器"""

    CHANNEL_NAME = "amazon"
    SUGGEST_URL = "https://completion.amazon.com/api/2017/suggestions"
    SEARCH_URL = "https://www.amazon.com/s"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Amazon] 开始采集: %s", self.root_keyword)
        self._collect_suggest()
        self._collect_suggest_extended()
        logger.info("[Amazon] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── Amazon Suggest ────────────────────────────────────────
    def _collect_suggest(self) -> None:
        """采集 Amazon 搜索建议"""
        params = {
            "session-id": "000-0000000-0000000",
            "customer-id": "",
            "request-id": "auto",
            "page-type": "Search",
            "lop": "en_US",
            "site-variant": "desktop",
            "client-info": "amazon-search-ui",
            "mid": "ATVPDKIKX0DER",  # Amazon US marketplace ID
            "alias": "aps",
            "b2b": "0",
            "fresh": "0",
            "ks": "80",
            "prefix": self.root_keyword,
            "event": "onKeyPress",
            "limit": "11",
            "fb": "1",
            "suggestion-type": "KEYWORD",
            "_": "1",
        }
        resp = self._get(self.SUGGEST_URL, params=params)
        if not resp:
            # 尝试备用 API
            self._collect_suggest_fallback()
            return
        try:
            data = resp.json()
            for item in data.get("suggestions", []):
                kw = item.get("value", "")
                if kw:
                    self._add_keyword(kw, source="amazon_suggest")
        except Exception as exc:
            logger.warning("[Amazon Suggest] 解析失败: %s", exc)
            self._collect_suggest_fallback()

    def _collect_suggest_fallback(self) -> None:
        """备用：使用旧版 Amazon Suggest API"""
        url = f"https://completion.amazon.com/search/complete"
        params = {
            "method": "completion",
            "q": self.root_keyword,
            "search-alias": "aps",
            "client": "amazon-search-ui",
            "mkt": "1",
        }
        resp = self._get(url, params=params)
        if not resp:
            return
        try:
            data = resp.json()
            suggestions = data[1] if len(data) > 1 else []
            for kw in suggestions:
                self._add_keyword(kw, source="amazon_suggest")
        except Exception as exc:
            logger.warning("[Amazon Suggest Fallback] 解析失败: %s", exc)

    def _collect_suggest_extended(self) -> None:
        """扩展修饰词"""
        modifiers = [
            "price", "for warehouse", "industrial", "heavy duty",
            "electric", "hydraulic", "specification", "supplier",
        ]
        for mod in modifiers:
            query = f"{self.root_keyword} {mod}"
            params = {
                "session-id": "000-0000000-0000000",
                "prefix": query,
                "alias": "aps",
                "mid": "ATVPDKIKX0DER",
                "limit": "11",
                "suggestion-type": "KEYWORD",
            }
            resp = self._get(self.SUGGEST_URL, params=params)
            if resp:
                try:
                    data = resp.json()
                    for item in data.get("suggestions", []):
                        kw = item.get("value", "")
                        if kw:
                            self._add_keyword(kw, source="amazon_suggest_ext")
                except Exception:
                    pass
            self._sleep()
