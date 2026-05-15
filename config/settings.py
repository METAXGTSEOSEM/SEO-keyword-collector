"""
全局配置文件 - SEO关键词采集系统
"""
import os
from pathlib import Path

# ─── 项目根目录 ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
CHECKPOINT_DIR = BASE_DIR / ".checkpoints"

# 确保目录存在
for _dir in [OUTPUT_DIR, LOG_DIR, CHECKPOINT_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ─── 请求配置 ─────────────────────────────────────────────────
REQUEST_TIMEOUT = 15          # 秒
REQUEST_DELAY_MIN = 1.0       # 最小延迟（秒）
REQUEST_DELAY_MAX = 3.0       # 最大延迟（秒）
MAX_RETRIES = 3               # 最大重试次数
CONCURRENT_LIMIT = 3          # 并发限制

# ─── 代理配置（预留接口）─────────────────────────────────────
PROXY_ENABLED = False
PROXY_LIST = [
    # "http://user:pass@host:port",
    # "socks5://user:pass@host:port",
]

# ─── Playwright 配置 ──────────────────────────────────────────
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_SLOW_MO = 500      # 毫秒，0=关闭

# ─── User-Agent 池 ────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36",
]

# ─── 采集渠道开关 ─────────────────────────────────────────────
CHANNELS_ENABLED = {
    "google_suggest":   True,
    "google_related":   True,
    "google_paa":       True,
    "google_serp":      True,
    "bing_suggest":     True,
    "bing_serp":        True,
    "youtube_suggest":  True,
    "youtube_serp":     True,
    "amazon_suggest":   True,
    "alibaba_suggest":  True,
    "alibaba_titles":   True,
    "madeinchina":      True,
    "reddit":           True,
    "quora":            False,   # Quora 反爬严格，默认关闭
    "competitor":       True,
    "google_trends":    True,
}

# ─── 竞品域名列表 ─────────────────────────────────────────────
COMPETITOR_DOMAINS = [
    # 用户可在此添加竞品域名，系统将抓取其 title/meta/H1/H2
    # "www.competitor-a.com",
    # "www.competitor-b.com",
]

# ─── NLP 聚类配置 ─────────────────────────────────────────────
CLUSTER_MIN_DF = 1            # 最小文档频率
CLUSTER_N_COMPONENTS = 50     # SVD 维度
CLUSTER_N_CLUSTERS = 20       # KMeans 聚类数

# ─── 关键词过滤配置 ───────────────────────────────────────────
MIN_KEYWORD_LENGTH = 3        # 最短关键词字符数
MAX_KEYWORD_LENGTH = 120      # 最长关键词字符数
MIN_WORD_COUNT = 1            # 最少单词数

# ─── 预留 API 接口配置 ────────────────────────────────────────
SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY", "")
AHREFS_API_KEY = os.getenv("AHREFS_API_KEY", "")
GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")

# ─── 目标市场语言/国家 ────────────────────────────────────────
TARGET_COUNTRIES = ["US", "GB", "DE", "AE", "BR", "ZA"]
TARGET_LANGUAGE = "en"

# ─── Google Trends 配置 ───────────────────────────────────────
TRENDS_TIMEFRAME = "today 12-m"   # 过去12个月
TRENDS_GEO = ""                    # 全球
