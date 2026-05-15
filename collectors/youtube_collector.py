"""
YouTube 采集器
- YouTube Suggest
- YouTube 搜索结果标题
"""
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """YouTube 关键词采集器"""

    CHANNEL_NAME = "youtube"
    SUGGEST_URL = "https://suggestqueries.google.com/complete/search"
    SEARCH_URL = "https://www.youtube.com/results"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[YouTube] 开始采集: %s", self.root_keyword)
        self._collect_suggest()
        self._collect_suggest_extended()
        self._collect_serp()
        logger.info("[YouTube] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── YouTube Suggest ───────────────────────────────────────
    def _collect_suggest(self) -> None:
        """通过 Google Suggest API（client=youtube）采集 YouTube 建议词"""
        params = {
            "client": "youtube",
            "q": self.root_keyword,
            "hl": "en",
            "ds": "yt",
        }
        resp = self._get(self.SUGGEST_URL, params=params)
        if not resp:
            return
        try:
            # YouTube suggest 返回 JSONP 格式，需要清理
            text = resp.text
            # 去除 JSONP 包装
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                suggestions = data[1] if len(data) > 1 else []
                for item in suggestions:
                    kw = item[0] if isinstance(item, list) else item
                    if isinstance(kw, str):
                        self._add_keyword(kw, source="youtube_suggest")
        except Exception as exc:
            logger.warning("[YouTube Suggest] 解析失败: %s", exc)

    def _collect_suggest_extended(self) -> None:
        """扩展修饰词"""
        modifiers = [
            "how to", "installation", "working", "review", "demo",
            "vs", "price", "china factory", "manufacturer",
        ]
        for mod in modifiers:
            query = f"{self.root_keyword} {mod}"
            params = {
                "client": "youtube",
                "q": query,
                "hl": "en",
                "ds": "yt",
            }
            resp = self._get(self.SUGGEST_URL, params=params)
            if resp:
                try:
                    text = resp.text
                    match = re.search(r'\[.*\]', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        suggestions = data[1] if len(data) > 1 else []
                        for item in suggestions:
                            kw = item[0] if isinstance(item, list) else item
                            if isinstance(kw, str):
                                self._add_keyword(kw, source="youtube_suggest_ext")
                except Exception:
                    pass
            self._sleep()

    # ─── YouTube SERP ──────────────────────────────────────────
    def _collect_serp(self) -> None:
        """采集 YouTube 搜索结果标题（静态页面解析）"""
        params = {"search_query": self.root_keyword}
        resp = self._get(self.SEARCH_URL, params=params)
        if not resp:
            return
        try:
            # YouTube 搜索结果嵌入在 JSON 数据中
            match = re.search(r'var ytInitialData = ({.*?});</script>', resp.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                contents = (
                    data.get("contents", {})
                    .get("twoColumnSearchResultsRenderer", {})
                    .get("primaryContents", {})
                    .get("sectionListRenderer", {})
                    .get("contents", [])
                )
                for section in contents:
                    items = (
                        section.get("itemSectionRenderer", {})
                        .get("contents", [])
                    )
                    for item in items:
                        video = item.get("videoRenderer", {})
                        title_runs = video.get("title", {}).get("runs", [])
                        title = "".join(r.get("text", "") for r in title_runs)
                        video_id = video.get("videoId", "")
                        if title:
                            self._add_keyword(
                                title,
                                source="youtube_serp",
                                title=title,
                                url=f"https://www.youtube.com/watch?v={video_id}",
                            )
        except Exception as exc:
            logger.warning("[YouTube SERP] 解析失败: %s", exc)
