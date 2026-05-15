"""
论坛采集器（Reddit / Quora）
- Reddit 行业问题词和用户真实需求
- Quora 问题词（备用）
"""
import json
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class ForumCollector(BaseCollector):
    """Reddit / Quora 关键词采集器"""

    CHANNEL_NAME = "forum"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Forum] 开始采集: %s", self.root_keyword)
        self._collect_reddit()
        self._collect_quora()
        logger.info("[Forum] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── Reddit ────────────────────────────────────────────────
    def _collect_reddit(self) -> None:
        """通过 Reddit JSON API 采集问题和标题"""
        # Reddit Search API（公开，不需要认证）
        url = "https://www.reddit.com/search.json"
        params = {
            "q": self.root_keyword,
            "sort": "relevance",
            "t": "all",
            "limit": "25",
            "type": "link",
        }
        headers = {"User-Agent": f"python-seo-collector/1.0 by /u/seo_bot"}
        resp = self._get(url, params=params, headers=headers)
        if not resp:
            return
        try:
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "")
                post_url = post_data.get("url", "")

                if title:
                    self._add_keyword(
                        title,
                        source="reddit_post_title",
                        title=title,
                        description=selftext[:200],
                        url=post_url,
                    )

                # 从帖子正文中提取问题句
                for sentence in re.split(r'[.!?\n]', selftext):
                    sentence = sentence.strip()
                    if (
                        sentence
                        and "?" in sentence
                        and 10 < len(sentence) < 200
                    ):
                        self._add_keyword(sentence, source="reddit_question")
        except Exception as exc:
            logger.warning("[Reddit] 解析失败: %s", exc)

        # 采集相关 Subreddit 讨论
        self._sleep()
        self._collect_reddit_subreddit()

    def _collect_reddit_subreddit(self) -> None:
        """在工业相关 subreddit 中搜索"""
        subreddits = [
            "r/manufacturing",
            "r/engineering",
            "r/industrial",
            "r/logistics",
            "r/warehousing",
        ]
        for sub in subreddits:
            url = f"https://www.reddit.com/{sub}/search.json"
            params = {
                "q": self.root_keyword,
                "restrict_sr": "1",
                "sort": "relevance",
                "limit": "10",
            }
            headers = {"User-Agent": "python-seo-collector/1.0"}
            resp = self._get(url, params=params, headers=headers)
            if resp:
                try:
                    data = resp.json()
                    for post in data.get("data", {}).get("children", []):
                        title = post.get("data", {}).get("title", "")
                        if title:
                            self._add_keyword(
                                title,
                                source=f"reddit_{sub.replace('r/', '')}",
                                title=title,
                            )
                except Exception:
                    pass
            self._sleep()

    # ─── Quora ─────────────────────────────────────────────────
    def _collect_quora(self) -> None:
        """
        采集 Quora 问题词（通过 Google 搜索 site:quora.com）
        注意：Quora 直接访问有严格的反爬，通过 Google 间接获取更稳定
        """
        url = "https://www.google.com/search"
        params = {
            "q": f"site:quora.com {self.root_keyword}",
            "hl": "en",
            "num": "10",
        }
        resp = self._get(url, params=params)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        for block in soup.select("div.tF2Cxc, div.g"):
            title_el = block.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""
            desc_el = block.select_one("div.VwiC3b")
            description = desc_el.get_text(strip=True) if desc_el else ""
            a_el = block.select_one("a[href]")
            url_link = a_el["href"] if a_el else ""

            if title and "quora.com" in url_link.lower():
                self._add_keyword(
                    title,
                    source="quora_question",
                    title=title,
                    description=description,
                    url=url_link,
                )
