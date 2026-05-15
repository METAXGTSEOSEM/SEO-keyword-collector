"""
Google Trends 采集器
- 相关查询（Related Queries）
- Rising Queries（上升中的查询）
"""
import logging

from collectors.base_collector import BaseCollector, KeywordRecord

logger = logging.getLogger(__name__)


class TrendsCollector(BaseCollector):
    """Google Trends 关键词采集器"""

    CHANNEL_NAME = "google_trends"

    def collect(self) -> list[KeywordRecord]:
        logger.info("[Trends] 开始采集: %s", self.root_keyword)
        self._collect_trends()
        logger.info("[Trends] 完成，共采集 %d 条", len(self.results))
        return self.results

    def _collect_trends(self) -> None:
        """使用 pytrends 采集 Google Trends 相关查询"""
        try:
            from pytrends.request import TrendReq
            from config.settings import TRENDS_GEO, TRENDS_TIMEFRAME

            pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
            pytrends.build_payload(
                [self.root_keyword[:100]],  # pytrends 关键词长度限制
                cat=0,
                timeframe=TRENDS_TIMEFRAME,
                geo=TRENDS_GEO,
                gprop="",
            )

            # Related Queries
            related = pytrends.related_queries()
            for kw_type in ["top", "rising"]:
                df = related.get(self.root_keyword[:100], {}).get(kw_type)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        kw = str(row.get("query", "")).strip()
                        if kw:
                            self._add_keyword(
                                kw,
                                source=f"google_trends_{kw_type}",
                            )

            # Related Topics（获取相关主题词）
            topics = pytrends.related_topics()
            for kw_type in ["top", "rising"]:
                df = topics.get(self.root_keyword[:100], {}).get(kw_type)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        topic = str(row.get("topic_title", "")).strip()
                        if topic:
                            self._add_keyword(
                                topic,
                                source=f"google_trends_topic_{kw_type}",
                            )

        except ImportError:
            logger.warning("[Trends] pytrends 未安装，跳过 Google Trends 采集")
        except Exception as exc:
            logger.warning("[Trends] 采集失败: %s", exc)
