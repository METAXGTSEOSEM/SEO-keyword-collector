"""
采集器基类 - 所有渠道 Collector 的父类
"""
import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests

from config.settings import (
    MAX_RETRIES,
    PROXY_ENABLED,
    PROXY_LIST,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    USER_AGENTS,
)

logger = logging.getLogger(__name__)


@dataclass
class KeywordRecord:
    """标准关键词记录结构"""
    keyword: str
    root_keyword: str
    source: str            # URL 或来源描述
    channel: str           # 采集渠道名称
    keyword_type: str = ""
    search_intent: str = ""
    page_type: str = ""
    commercial_value: str = ""
    title: str = ""
    description: str = ""
    url: str = ""
    language: str = "en"
    country: str = "US"
    collected_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """转为字典，方便写入 DataFrame"""
        return {
            "keyword": self.keyword.strip().lower(),
            "root_keyword": self.root_keyword,
            "source": self.source,
            "channel": self.channel,
            "keyword_type": self.keyword_type,
            "search_intent": self.search_intent,
            "page_type": self.page_type,
            "commercial_value": self.commercial_value,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "language": self.language,
            "country": self.country,
            "collected_at": self.collected_at,
        }


class BaseCollector(ABC):
    """
    所有渠道采集器的抽象基类。
    提供：随机UA、代理轮换、限速、重试、错误隔离。
    """

    CHANNEL_NAME: str = "base"

    def __init__(self, root_keyword: str) -> None:
        self.root_keyword = root_keyword
        self.results: list[KeywordRecord] = []
        self.session = self._build_session()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # ─── Session 构建 ──────────────────────────────────────────
    def _build_session(self) -> requests.Session:
        """构建带随机UA和代理的 requests.Session"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self._random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        })
        if PROXY_ENABLED and PROXY_LIST:
            proxy = random.choice(PROXY_LIST)
            session.proxies = {"http": proxy, "https": proxy}
        return session

    def _random_ua(self) -> str:
        """随机返回一个 User-Agent"""
        return random.choice(USER_AGENTS)

    def _rotate_ua(self) -> None:
        """切换随机 User-Agent"""
        self.session.headers["User-Agent"] = self._random_ua()

    # ─── 限速与请求 ────────────────────────────────────────────
    def _sleep(self) -> None:
        """随机延迟，避免触发反爬"""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    def _get(self, url: str, params: Optional[dict] = None, **kwargs) -> Optional[requests.Response]:
        """
        带重试的 GET 请求。失败时自动跳过，不影响其他采集器。
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._rotate_ua()
                resp = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                    **kwargs,
                )
                resp.raise_for_status()
                return resp
            except Exception as exc:
                self.logger.warning(
                    "GET 失败 (attempt %d/%d): %s → %s",
                    attempt, MAX_RETRIES, url, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)  # 指数退避
        return None

    # ─── 记录写入 ──────────────────────────────────────────────
    def _add_keyword(
        self,
        keyword: str,
        source: str = "",
        title: str = "",
        description: str = "",
        url: str = "",
        country: str = "US",
    ) -> None:
        """添加一条标准关键词记录"""
        kw = keyword.strip().lower()
        if not kw or len(kw) < 2:
            return
        record = KeywordRecord(
            keyword=kw,
            root_keyword=self.root_keyword,
            source=source or self.CHANNEL_NAME,
            channel=self.CHANNEL_NAME,
            title=title,
            description=description,
            url=url,
            country=country,
        )
        self.results.append(record)

    # ─── 抽象接口 ──────────────────────────────────────────────
    @abstractmethod
    def collect(self) -> list[KeywordRecord]:
        """
        执行采集，返回 KeywordRecord 列表。
        子类必须实现此方法。
        """
        ...

    # ─── 辅助：Playwright 代理封装 ─────────────────────────────
    async def _playwright_get(self, url: str, wait_selector: Optional[str] = None) -> Optional[str]:
        """
        使用 Playwright 获取页面 HTML（用于需要 JS 渲染的页面）。
        返回页面 HTML 字符串，失败返回 None。
        """
        try:
            from playwright.async_api import async_playwright
            from config.settings import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_SLOW_MO

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=PLAYWRIGHT_HEADLESS,
                    slow_mo=PLAYWRIGHT_SLOW_MO,
                )
                context = await browser.new_context(
                    user_agent=self._random_ua(),
                    locale="en-US",
                )
                page = await context.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                if wait_selector:
                    try:
                        await page.wait_for_selector(wait_selector, timeout=8000)
                    except Exception:
                        pass
                html = await page.content()
                await browser.close()
                return html
        except Exception as exc:
            self.logger.warning("Playwright 获取失败: %s → %s", url, exc)
            return None
