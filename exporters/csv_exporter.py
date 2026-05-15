"""
CSV 导出器
负责将 DataFrame 写入各种格式的 CSV 文件
"""
import logging
from pathlib import Path

import pandas as pd

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)

# 标准输出字段顺序
OUTPUT_COLUMNS = [
    "keyword", "root_keyword", "source", "channel",
    "keyword_type", "search_intent", "page_type", "commercial_value",
    "title", "description", "url",
    "language", "country", "collected_at",
    "cluster_id", "cluster_label",
]


class CsvExporter:
    """CSV 文件导出器"""

    def export_per_root(
        self,
        root_keyword: str,
        raw_df: pd.DataFrame,
        clean_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
    ) -> Path:
        """
        为单个词根导出三个文件：
        - keywords_raw.csv
        - keywords_clean.csv
        - keyword_clusters.csv
        返回该词根的输出目录 Path。
        """
        folder_name = root_keyword.lower().replace(" ", "-")
        out_dir = OUTPUT_DIR / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        self._write(raw_df, out_dir / "keywords_raw.csv")
        self._write(clean_df, out_dir / "keywords_clean.csv")
        self._write(cluster_df, out_dir / "keyword_clusters.csv")

        logger.info("[CSV] 词根 '%s' 文件已写入: %s", root_keyword, out_dir)
        return out_dir

    def export_all(
        self,
        raw_df: pd.DataFrame,
        clean_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
        final_map_df: pd.DataFrame,
    ) -> None:
        """导出全部词根汇总文件"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self._write(raw_df, OUTPUT_DIR / "all_keywords.csv")
        self._write(clean_df, OUTPUT_DIR / "all_keywords_clean.csv")
        self._write(cluster_df, OUTPUT_DIR / "all_keyword_clusters.csv")
        self._write(final_map_df, OUTPUT_DIR / "final_keyword_map.csv")

        logger.info("[CSV] 汇总文件已写入: %s", OUTPUT_DIR)

    def _write(self, df: pd.DataFrame, path: Path) -> None:
        """写入 CSV，自动对齐列顺序"""
        if df is None or df.empty:
            logger.warning("[CSV] DataFrame 为空，跳过写入: %s", path)
            return
        # 补全缺失列
        for col in OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        # 按标准列顺序输出
        cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
        # 加上额外列（不在标准列表中的）
        extra_cols = [c for c in df.columns if c not in OUTPUT_COLUMNS]
        final_cols = cols + extra_cols

        df[final_cols].to_csv(path, index=False, encoding="utf-8-sig")
        logger.info("[CSV] 写入 %d 条 → %s", len(df), path)
