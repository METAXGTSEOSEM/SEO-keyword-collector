"""
Google 采集器
- Google Suggest（自动补全）
- Google Related Searches（相关搜索）
- People Also Ask（PAA 问题词）
- Google SERP 标题和描述
"""
import json
import logging
import re
from typing import Optional
from urllib.parse import quote_plus, urlencode

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class GoogleCollector(BaseCollector):
    """Google 多功能关键词采集器"""

    CHANNEL_NAME = "google"

    # Suggest API（无需 JS 渲染）
    SUGGEST_URL = "https://suggestqueries.google.com/complete/search"
    # Google Search（需要 UA 模拟）
    SEARCH_URL = "https://www.google.com/search"

    def collect(self) -> list[KeywordRecord]:
        """执行全部 Google 采集逻辑"""
        logger.info("[Google] 开始采集: %s", self.root_keyword)

        self._collect_suggest()
        self._collect_alphabet_suggest()
        self._collect_serp()

        logger.info("[Google] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── Google Suggest ────────────────────────────────────────
    def _collect_suggest(self) -> None:
        """采集 Google 自动补全建议"""
        params = {
            "client": "firefox",
            "q": self.root_keyword,
            "hl": "en",
        }
        resp = self._get(self.SUGGEST_URL, params=params)
        if not resp:
            return
        try:
            data = json.loads(resp.text)
            suggestions = data[1] if len(data) > 1 else []
            for kw in suggestions:
                self._add_keyword(
                    kw,
                    source="google_suggest",
                    url=f"https://www.google.com/search?q={quote_plus(kw)}",
                )
        except Exception as exc:
            logger.warning("[Google Suggest] 解析失败: %s", exc)

    def _collect_alphabet_suggest(self) -> None:
        """
        字母扩展 Suggest：在词根后追加 a-z 和常用修饰词获取更多建议
        例如: "hydraulic cargo lift a", "hydraulic cargo lift b", ...
        """
        # 字母扩展
        for char in "abcdefghijklmnopqrstuvwxyz":
            query = f"{self.root_keyword} {char}"
            params = {"client": "firefox", "q": query, "hl": "en"}
            resp = self._get(self.SUGGEST_URL, params=params)
            if resp:
                try:
                    data = json.loads(resp.text)
                    for kw in (data[1] if len(data) > 1 else []):
                        self._add_keyword(kw, source="google_suggest_alpha")
                except Exception:
                    pass
            self._sleep()

        # 常用 B2B 修饰词扩展
        modifiers = [
            "price", "manufacturer", "factory", "supplier", "custom",
            "oem", "wholesale", "specification", "for sale", "quote",
            "cost", "buy", "china", "how to", "what is", "types of",
            "best", "top", "vs", "alternative", "certified",
        ]
        for mod in modifiers:
            query = f"{self.root_keyword} {mod}"
            params = {"client": "firefox", "q": query, "hl": "en"}
            resp = self._get(self.SUGGEST_URL, params=params)
            if resp:
                try:
                    data = json.loads(resp.text)
                    for kw in (data[1] if len(data) > 1 else []):
                        self._add_keyword(kw, source="google_suggest_modifier")
                except Exception:
                    pass
            self._sleep()

    # ─── Google SERP ───────────────────────────────────────────
    def _collect_serp(self) -> None:
        """采集 Google SERP：Related Searches、PAA、标题和描述"""
        params = {"q": self.root_keyword, "hl": "en", "gl": "us", "num": "10"}
        headers = {
            "User-Agent": self._random_ua(),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
        }
        resp = self._get(self.SEARCH_URL, params=params, headers=headers)
        if not resp:
            logger.warning("[Google SERP] 请求失败，跳过")
            return

        soup = BeautifulSoup(resp.text, "html.parser")

        # ① Related Searches
        self._parse_related_searches(soup)
        # ② People Also Ask
        self._parse_paa(soup)
        # ③ SERP 结果标题+描述
        self._parse_organic_results(soup)

    def _parse_related_searches(self, soup: BeautifulSoup) -> None:
        """解析 Google Related Searches 区域"""
        # 多种选择器兼容不同 Google 页面版本
        selectors = [
            "div.s75CSd",         # 常见格式
            "div[data-initq]",
            "a.k8XOCe",
            "div.B9g0yd",
        ]
        found = set()
        for sel in selectors:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if text and len(text) > 3 and text not in found:
                    found.add(text)
                    self._add_keyword(text, source="google_related_search")

        # 备用：搜索包含 "related" 的 span 文本
        for a_tag in soup.find_all("a", href=re.compile(r"/search\?q=")):
            text = a_tag.get_text(strip=True)
            if 4 < len(text) < 100 and text not in found:
                found.add(text)
                self._add_keyword(text, source="google_related_search")

    def _parse_paa(self, soup: BeautifulSoup) -> None:
        """解析 People Also Ask 问题"""
        paa_selectors = [
            "div.related-question-pair",
            "div[data-q]",
            "span.CSkcDe",
        ]
        found = set()
        for sel in paa_selectors:
            for el in soup.select(sel):
                text = el.get_text(strip=True)
                if text and "?" in text and text not in found:
                    found.add(text)
                    self._add_keyword(
                        text,
                        source="google_paa",
                    )

        # 备用：查找问题形态的文本节点
        for span in soup.find_all("span"):
            text = span.get_text(strip=True)
            if (
                text
                and text.endswith("?")
                and 10 < len(text) < 200
                and self.root_keyword.split()[0].lower() in text.lower()
                and text not in found
            ):
                found.add(text)
                self._add_keyword(text, source="google_paa")

    def _parse_organic_results(self, soup: BeautifulSoup) -> None:
        """解析 Google 自然搜索结果标题和描述"""
        # 自然结果容器
        result_blocks = soup.select("div.tF2Cxc, div.g")
        for block in result_blocks:
            # 标题
            title_el = block.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""

            # 描述
            desc_el = block.select_one("div.VwiC3b, span.aCOpRe")
            description = desc_el.get_text(strip=True) if desc_el else ""

            # URL
            a_el = block.select_one("a[href]")
            url = a_el["href"] if a_el else ""

            if title:
                # 从标题提取关键词片段
                self._add_keyword(
                    title,
                    source="google_serp_title",
                    title=title,
                    description=description,
                    url=url,
                )
