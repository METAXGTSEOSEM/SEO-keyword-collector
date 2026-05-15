"""
Bing 采集器
- Bing Suggest（自动补全）
- Bing 搜索结果标题和描述
"""
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class BingCollector(BaseCollector):
    """Bing 关键词采集器"""

    CHANNEL_NAME = "bing"
    SUGGEST_URL = "https://api.bing.com/osjson.aspx"
    SEARCH_URL = "https://www.bing.com/search"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Bing] 开始采集: %s", self.root_keyword)
        self._collect_suggest()
        self._collect_suggest_extended()
        self._collect_serp()
        logger.info("[Bing] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── Bing Suggest ──────────────────────────────────────────
    def _collect_suggest(self) -> None:
        """采集 Bing 自动补全"""
        params = {"query": self.root_keyword, "form": "OSJRLH"}
        resp = self._get(self.SUGGEST_URL, params=params)
        if not resp:
            return
        try:
            data = json.loads(resp.text)
            suggestions = data[1] if len(data) > 1 else []
            for kw in suggestions:
                self._add_keyword(kw, source="bing_suggest")
        except Exception as exc:
            logger.warning("[Bing Suggest] 解析失败: %s", exc)

    def _collect_suggest_extended(self) -> None:
        """扩展修饰词 Suggest"""
        modifiers = [
            "price", "manufacturer", "supplier", "factory", "custom",
            "oem", "buy", "for sale", "specification", "quote",
            "china", "how", "what", "best", "vs", "certified",
        ]
        for mod in modifiers:
            query = f"{self.root_keyword} {mod}"
            params = {"query": query, "form": "OSJRLH"}
            resp = self._get(self.SUGGEST_URL, params=params)
            if resp:
                try:
                    data = json.loads(resp.text)
                    for kw in (data[1] if len(data) > 1 else []):
                        self._add_keyword(kw, source="bing_suggest_ext")
                except Exception:
                    pass
            self._sleep()

    # ─── Bing SERP ─────────────────────────────────────────────
    def _collect_serp(self) -> None:
        """采集 Bing SERP 标题和描述"""
        params = {"q": self.root_keyword, "count": "10", "setlang": "en"}
        resp = self._get(self.SEARCH_URL, params=params)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        # 自然搜索结果
        for item in soup.select("li.b_algo"):
            title_el = item.select_one("h2 a")
            title = title_el.get_text(strip=True) if title_el else ""
            desc_el = item.select_one("div.b_caption p")
            description = desc_el.get_text(strip=True) if desc_el else ""
            url = title_el["href"] if title_el and title_el.get("href") else ""

            if title:
                self._add_keyword(
                    title,
                    source="bing_serp_title",
                    title=title,
                    description=description,
                    url=url,
                )

        # Related Searches
        for el in soup.select("li.b_rs a, div.b_rs a"):
            text = el.get_text(strip=True)
            if text:
                self._add_keyword(text, source="bing_related")
