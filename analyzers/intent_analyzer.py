"""
搜索意图分析器
判断关键词的搜索意图：Informational / Navigational / Commercial / Transactional
"""
import logging
import re

import pandas as pd

logger = logging.getLogger(__name__)

# ─── 意图规则 ──────────────────────────────────────────────────

INTENT_RULES: list[tuple[str, str]] = [
    # Transactional（购买/询价意图）- 优先级最高
    (
        "Transactional",
        r"\b(?:buy|purchase|order|quote|price|pricing|cost|get a quote|rfq"
        r"|request for quotation|buy now|add to cart|shop|wholesale|bulk order"
        r"|for sale|stock|in stock|delivery|shipping|lead time|moq)\b"
        r"|price$|\bprice\b",
    ),

    # Commercial Investigation（调查比较意图）
    (
        "Commercial",
        r"\b(?:best|top|review|reviews|rating|compare|vs|versus|alternative"
        r"|recommendation|suggest|which|choose|selection|brand|brands"
        r"|manufacturer|supplier|factory|oem|odm|custom|certified)\b",
    ),

    # Navigational（品牌/网站导航）
    (
        "Navigational",
        r"\b(?:official|website|login|contact|about us|company|corporation"
        r"|inc\.|ltd\.|co\.|group|homepage|site)\b",
    ),

    # Informational（信息获取意图）
    (
        "Informational",
        r"^(?:how|what|why|when|where|who|which|can|is|are|does|do)\b"
        r"|\?$"
        r"|\b(?:guide|tutorial|tips|how to|definition|meaning|explain"
        r"|introduction|overview|history|type|types of|difference between"
        r"|working principle|mechanism|installation|maintenance|troubleshoot"
        r"|specification|technical|standard|regulation|certification)\b",
    ),
]

# ─── 商业价值判断 ───────────────────────────────────────────────

HIGH_COMMERCIAL_VALUE_PATTERNS = re.compile(
    r"\b(?:manufacturer|factory|supplier|oem|odm|custom|wholesale|bulk"
    r"|quote|price|buy|for sale|rfq|heavy duty|industrial|certification"
    r"|certified|export|import|b2b)\b",
    re.IGNORECASE,
)

LOW_COMMERCIAL_VALUE_PATTERNS = re.compile(
    r"\b(?:free|diy|homemade|how to make|history|definition|wikipedia"
    r"|invention|who invented|what is|rental|second.?hand|used)\b",
    re.IGNORECASE,
)


class IntentAnalyzer:
    """
    搜索意图分析器。
    为每条关键词分配：search_intent + commercial_value。
    """

    def __init__(self) -> None:
        self._compiled_intent = [
            (intent, re.compile(pattern, re.IGNORECASE))
            for intent, pattern in INTENT_RULES
        ]

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        """对 DataFrame 中的关键词批量分析意图"""
        logger.info("开始意图分析 %d 条关键词", len(df))
        df = df.copy()
        df["search_intent"] = df["keyword"].apply(self._detect_intent)
        df["commercial_value"] = df["keyword"].apply(self._assess_commercial_value)
        logger.info("意图分析完成")
        return df

    def _detect_intent(self, keyword: str) -> str:
        """判断单个关键词的搜索意图"""
        kw = keyword.lower().strip()
        for intent, pattern in self._compiled_intent:
            if pattern.search(kw):
                return intent
        return "Informational"   # 默认：信息意图

    def _assess_commercial_value(self, keyword: str) -> str:
        """
        评估商业价值：High / Medium / Low
        基于关键词中是否包含商业意图词汇。
        """
        if HIGH_COMMERCIAL_VALUE_PATTERNS.search(keyword):
            return "High"
        if LOW_COMMERCIAL_VALUE_PATTERNS.search(keyword):
            return "Low"
        word_count = len(keyword.split())
        if word_count >= 3:
            return "Medium"
        return "Low"
