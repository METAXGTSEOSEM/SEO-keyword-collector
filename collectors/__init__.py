"""
collectors 包初始化
"""
from collectors.amazon_collector import AmazonCollector
from collectors.alibaba_collector import AlibabaCollector
from collectors.bing_collector import BingCollector
from collectors.competitor_collector import CompetitorCollector
from collectors.forum_collector import ForumCollector
from collectors.google_collector import GoogleCollector
from collectors.madeinchina_collector import MadeinchinaCollector
from collectors.trends_collector import TrendsCollector
from collectors.youtube_collector import YouTubeCollector

__all__ = [
    "AmazonCollector",
    "AlibabaCollector",
    "BingCollector",
    "CompetitorCollector",
    "ForumCollector",
    "GoogleCollector",
    "MadeinchinaCollector",
    "TrendsCollector",
    "YouTubeCollector",
]
