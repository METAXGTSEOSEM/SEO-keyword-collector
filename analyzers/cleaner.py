"""
关键词清洗器
- 去重、过滤无效词、标准化格式
"""
import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ─── 停用词（无意义的单独词） ──────────────────────────────────
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "it", "as", "be",
    "was", "are", "were", "been", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "shall",
    "can", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "each", "few", "more", "most", "other", "some", "such", "than",
    "too", "very", "just", "than", "then", "there", "these", "those",
    "what", "when", "where", "who", "which", "why", "how",
}

# ─── 低价值词模式（负向关键词） ────────────────────────────────
LOW_VALUE_PATTERNS = [
    r"\bporn\b", r"\bsex\b", r"\badult\b", r"\bcasino\b",
    r"\bgambling\b", r"\bdrug\b", r"\billegal\b",
    r"^\d+$",                    # 纯数字
    r"^[^a-zA-Z0-9\s\-]+$",     # 纯特殊字符
]

# ─── 字符黑名单 ────────────────────────────────────────────────
CHAR_BLACKLIST = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')


class KeywordCleaner:
    """
    关键词清洗器。
    输入 DataFrame，输出清洗后的 DataFrame。
    """

    def __init__(
        self,
        min_length: int = 3,
        max_length: int = 120,
        min_words: int = 1,
        max_words: int = 15,
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.min_words = min_words
        self.max_words = max_words
        self._low_value_re = re.compile(
            "|".join(LOW_VALUE_PATTERNS), re.IGNORECASE
        )

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        主清洗流程：
        1. 规范化文本
        2. 长度过滤
        3. 低价值过滤
        4. 去重
        """
        logger.info("清洗前行数: %d", len(df))

        if df.empty:
            return df

        # ① 规范化
        df = df.copy()
        df["keyword"] = df["keyword"].astype(str).apply(self._normalize)

        # ② 过滤空值
        df = df[df["keyword"].str.len() >= self.min_length]

        # ③ 长度过滤
        df = df[df["keyword"].str.len() <= self.max_length]

        # ④ 单词数过滤
        word_counts = df["keyword"].str.split().str.len()
        df = df[(word_counts >= self.min_words) & (word_counts <= self.max_words)]

        # ⑤ 低价值模式过滤
        mask_low = df["keyword"].apply(self._is_low_value)
        df = df[~mask_low]

        # ⑥ 纯停用词过滤（单词且在停用词表中）
        def is_all_stopwords(kw: str) -> bool:
            words = kw.lower().split()
            return all(w in STOPWORDS for w in words)

        df = df[~df["keyword"].apply(is_all_stopwords)]

        # ⑦ 去重（保留每个 keyword 的第一条记录，按来源丰富度排序）
        df = self._dedup(df)

        logger.info("清洗后行数: %d", len(df))
        return df.reset_index(drop=True)

    def _normalize(self, text: str) -> str:
        """规范化：去除控制字符、多余空格、统一小写"""
        if not isinstance(text, str):
            return ""
        # 去除控制字符
        text = CHAR_BLACKLIST.sub("", text)
        # 去除 HTML 实体残留
        text = re.sub(r"&[a-z]+;", " ", text)
        text = re.sub(r"&#?\w+;", " ", text)
        # 统一引号
        text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        # 合并多余空格
        text = re.sub(r"\s+", " ", text).strip()
        # 小写化
        text = text.lower()
        return text

    def _is_low_value(self, kw: str) -> bool:
        """判断是否为低价值关键词"""
        return bool(self._low_value_re.search(kw))

    def _dedup(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        智能去重：
        - 相同 keyword 保留第一条
        - 但合并来源信息（source / channel 拼接）
        """
        if df.empty:
            return df

        # 按 keyword 聚合 source
        agg_source = (
            df.groupby("keyword")["source"]
            .apply(lambda x: "|".join(sorted(set(x.astype(str)))))
            .reset_index()
            .rename(columns={"source": "source_merged"})
        )

        # 保留每个 keyword 第一条出现的其他字段
        df_first = df.drop_duplicates(subset=["keyword"], keep="first")
        df_merged = df_first.merge(agg_source, on="keyword", how="left")
        df_merged["source"] = df_merged["source_merged"]
        df_merged.drop(columns=["source_merged"], inplace=True)

        return df_merged
