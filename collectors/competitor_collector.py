"""
竞品网站采集器
- 抓取竞品页面 Title / Meta Description / H1 / H2 / URL
- 支持用户在 config/settings.py 中配置竞品域名
"""
import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector, KeywordRecord
from config.settings import COMPETITOR_DOMAINS

logger = logging.getLogger(__name__)


class CompetitorCollector(BaseCollector):
    """竞品网站关键词采集器"""

    CHANNEL_NAME = "competitor"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Competitor] 开始采集: %s", self.root_keyword)

        if not COMPETITOR_DOMAINS:
            # 没有配置竞品域名时，通过 Google 找到竞品页面
            self._discover_competitors_via_google()
        else:
            for domain in COMPETITOR_DOMAINS:
                self._scrape_domain(domain)

        logger.info("[Competitor] 完成，共采集 %d 条", len(self.results))
        return self.results

    # ─── 通过 Google 发现竞品 ──────────────────────────────────
    def _discover_competitors_via_google(self) -> None:
        """通过 Google 搜索词根，获取排名靠前的竞品页面"""
        url = "https://www.google.com/search"
        params = {
            "q": f"{self.root_keyword} manufacturer supplier",
            "hl": "en",
            "gl": "us",
            "num": "10",
        }
        resp = self._get(url, params=params)
        if not resp:
            return
        soup = BeautifulSoup(resp.text, "html.parser")

        competitor_urls = []
        for a_tag in soup.select("div.tF2Cxc a[href], div.g a[href]"):
            href = a_tag.get("href", "")
            if href.startswith("http") and not any(
                skip in href for skip in [
                    "google.com", "youtube.com", "wikipedia.org",
                    "amazon.com", "alibaba.com",
                ]
            ):
                parsed = urlparse(href)
                if parsed.netloc and parsed.netloc not in [
                    urlparse(u).netloc for u in competitor_urls
                ]:
                    competitor_urls.append(href)

        for competitor_url in competitor_urls[:5]:  # 最多取前5个
            self._sleep()
            self._scrape_url(competitor_url)

    # ─── 抓取指定域名 ──────────────────────────────────────────
    def _scrape_domain(self, domain: str) -> None:
        """抓取配置的竞品域名首页和搜索页"""
        base_url = f"https://{domain}"
        self._scrape_url(base_url)
        # 尝试抓取该域名的产品搜索页
        search_url = f"{base_url}/search?q={self.root_keyword.replace(' ', '+')}"
        self._sleep()
        self._scrape_url(search_url)

    # ─── 核心 URL 抓取 ─────────────────────────────────────────
    def _scrape_url(self, url: str) -> None:
        """抓取一个 URL，提取 SEO 相关关键词"""
        resp = self._get(url)
        if not resp:
            return

        soup = BeautifulSoup(resp.text, "html.parser")
        domain = urlparse(url).netloc

        # ① Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if title:
            self._add_keyword(
                title,
                source=f"competitor:{domain}",
                title=title,
                url=url,
            )

        # ② Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            desc = meta_desc.get("content", "")
            if desc:
                self._add_keyword(
                    desc,
                    source=f"competitor:{domain}",
                    description=desc,
                    url=url,
                )

        # ③ H1 标签
        for h1 in soup.find_all("h1"):
            text = h1.get_text(strip=True)
            if text:
                self._add_keyword(
                    text,
                    source=f"competitor:{domain}:h1",
                    title=title,
                    url=url,
                )

        # ④ H2 标签
        for h2 in soup.find_all("h2"):
            text = h2.get_text(strip=True)
            if text and len(text) < 100:
                self._add_keyword(
                    text,
                    source=f"competitor:{domain}:h2",
                    title=title,
                    url=url,
                )

        # ⑤ 从 URL 中提取关键词片段
        path = urlparse(url).path
        slug_words = re.sub(r'[-_/]', ' ', path).strip()
        if slug_words and len(slug_words) > 3:
            self._add_keyword(
                slug_words,
                source=f"competitor:{domain}:url_slug",
                url=url,
            )

        # ⑥ 抓取页面内部链接的 anchor text（产品相关链接）
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            anchor = a_tag.get_text(strip=True)
            if (
                anchor
                and 3 < len(anchor) < 80
                and any(
                    kw in anchor.lower()
                    for kw in self.root_keyword.lower().split()
                )
            ):
                self._add_keyword(
                    anchor,
                    source=f"competitor:{domain}:anchor",
                    url=urljoin(url, href),
                )
