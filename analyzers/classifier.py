"""
关键词分类器
将关键词分类为 13 种 B2B 工业关键词类型
"""
import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ─── 分类规则（按优先级排序，先匹配先得） ──────────────────────

CLASSIFICATION_RULES: list[tuple[str, list[str]]] = [
    # ① 品牌关键词
    ("Brand Keyword", [
        r"\b(?:brand|branded|trademark|logo)\b",
    ]),

    # ② 供应商/工厂/制造商关键词
    ("Supplier / Factory / Manufacturer Keyword", [
        r"\b(?:manufacturer|factory|supplier|producer|vendor|maker|brand owner"
        r"|oem manufacturer|odm manufacturer|made in china|china factory"
        r"|chinese manufacturer|wholesale supplier|bulk supplier)\b",
    ]),

    # ③ 定制/OEM/ODM 关键词
    ("Custom / OEM / ODM Keyword", [
        r"\b(?:custom|oem|odm|bespoke|tailor.?made|customized|custom.?built"
        r"|custom.?design|private label|white label|made.?to.?order)\b",
    ]),

    # ④ 认证关键词
    ("Certification Keyword", [
        r"\b(?:ce certified|iso|atex|ul listed|rohs|reach|fcc|iec|ansi|din"
        r"|certification|certified|certificate|approval|compliant|standard"
        r"|explosion.?proof|safety standard)\b",
    ]),

    # ⑤ 规格参数关键词
    ("Specification Keyword", [
        r"\b(?:\d+\s*(?:ton|kg|lb|t)\b|\d+\s*(?:kw|hp|w|v|a|rpm|hz)"
        r"|\d+\s*(?:m|ft|inch|mm|cm)\b|capacity|load|speed|power|voltage"
        r"|dimension|size|weight|specification|spec|model|series|type"
        r"|hydraulic|electric|pneumatic|diesel|manual|automatic|semi.?auto)\b",
    ]),

    # ⑥ 应用场景关键词
    ("Application Keyword", [
        r"\b(?:for warehouse|for factory|for construction|for mining|for port"
        r"|for shipyard|for garage|for workshop|for loading dock|for logistics"
        r"|for hospital|for airport|for cold storage|industrial use"
        r"|heavy duty|heavy.?load|warehouse use|cargo handling|material handling)\b",
    ]),

    # ⑦ 行业关键词
    ("Industry Keyword", [
        r"\b(?:manufacturing|logistics|warehousing|construction|mining|shipbuilding"
        r"|automotive|pharmaceutical|food processing|cold chain|aerospace"
        r"|oil and gas|petrochemical|steel|chemical industry|textile)\b",
    ]),

    # ⑧ 问题解决关键词
    ("Problem Solving Keyword", [
        r"^(?:how to|how do|what is|what are|why|when to|where to"
        r"|can i|should i|is it|which is better|vs|comparison)"
        r"|\?$"
        r"|problem|issue|fail|broken|repair|troubleshoot|fix|error|fault",
    ]),

    # ⑨ 竞品关键词（需要配合品牌库使用，此处用通用模式）
    ("Competitor Keyword", [
        r"\b(?:vs|versus|alternative|compare|comparison|instead of|better than"
        r"|competitor|competing|rival|similar to)\b",
    ]),

    # ⑩ 长尾关键词（判断条件：词数 ≥ 4 且不属于其他高优先级类型）
    # 此项在分类逻辑末尾通过词数判断

    # ⑪ 低意图/负向关键词
    ("Low Intent / Negative Keyword", [
        r"\b(?:rental|rent|hire|second.?hand|used|refurbished|repair|spare part"
        r"|diy|how to make|homemade|free download|pdf|manual download"
        r"|wikipedia|history|invention|who invented|definition of)\b",
    ]),

    # ⑫ 核心产品关键词（兜底：包含词根本身）
    # 在最终判断中处理

    # ⑬ 工业通用关键词
    ("Industrial Keyword", [
        r"\b(?:industrial|heavy industrial|commercial|professional|heavy.?duty"
        r"|high.?capacity|high.?performance|robust|rugged|durable)\b",
    ]),
]


class KeywordClassifier:
    """
    关键词分类器。
    对 DataFrame 中每条关键词打上 keyword_type 标签。
    """

    def __init__(self, root_keywords: Optional[list[str]] = None) -> None:
        """
        Args:
            root_keywords: 用户输入的词根列表，用于识别「核心产品关键词」
        """
        self.root_keywords = [kw.lower() for kw in (root_keywords or [])]
        self._compiled_rules = self._compile_rules()

    def _compile_rules(self) -> list[tuple[str, re.Pattern]]:
        """预编译所有规则的正则"""
        compiled = []
        for label, patterns in CLASSIFICATION_RULES:
            merged = "|".join(f"(?:{p})" for p in patterns)
            compiled.append((label, re.compile(merged, re.IGNORECASE)))
        return compiled

    def classify(self, df: pd.DataFrame) -> pd.DataFrame:
        """对整个 DataFrame 进行分类，填充 keyword_type 列"""
        logger.info("开始分类 %d 条关键词", len(df))
        df = df.copy()
        df["keyword_type"] = df["keyword"].apply(self._classify_one)
        logger.info("分类完成")
        return df

    def _classify_one(self, keyword: str) -> str:
        """对单个关键词进行分类"""
        kw_lower = keyword.lower().strip()

        # 优先判断：低意图关键词（提前检查）
        low_intent_re = re.compile(
            r"\b(?:rental|rent|hire|second.?hand|used|refurbished|repair|spare part"
            r"|diy|how to make|homemade|free download|pdf manual|wikipedia"
            r"|history|invention|who invented|definition of)\b",
            re.IGNORECASE,
        )
        if low_intent_re.search(kw_lower):
            return "Low Intent / Negative Keyword"

        # 核心产品关键词：keyword 中包含词根
        for root in self.root_keywords:
            if root in kw_lower or all(
                word in kw_lower for word in root.split()[:2]
            ):
                word_count = len(kw_lower.split())
                if word_count <= 3:
                    return "Core Product Keyword"

        # 按优先级遍历规则
        for label, pattern in self._compiled_rules:
            if pattern.search(kw_lower):
                return label

        # 长尾判断：词数 ≥ 4 且未被分类
        word_count = len(kw_lower.split())
        if word_count >= 4:
            return "Long Tail Keyword"

        # 核心产品词（宽松匹配）
        if self.root_keywords:
            root_words = set()
            for root in self.root_keywords:
                root_words.update(root.split())
            kw_words = set(kw_lower.split())
            overlap = root_words & kw_words
            if len(overlap) >= 1:
                return "Core Product Keyword"

        return "Industrial Keyword"
