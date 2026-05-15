"""
摘要报告导出器
生成人类可读的 keyword_summary.txt
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from config.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


class SummaryExporter:
    """生成关键词采集摘要报告"""

    def export_per_root(
        self,
        root_keyword: str,
        raw_df: pd.DataFrame,
        clean_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
        out_dir: Optional[Path] = None,
    ) -> None:
        """为单个词根生成摘要 txt"""
        if out_dir is None:
            folder_name = root_keyword.lower().replace(" ", "-")
            out_dir = OUTPUT_DIR / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        report = self._build_report(root_keyword, raw_df, clean_df, cluster_df)
        path = out_dir / "keyword_summary.txt"
        path.write_text(report, encoding="utf-8")
        logger.info("[Summary] 摘要报告已写入: %s", path)

    def export_global(
        self,
        all_raw: pd.DataFrame,
        all_clean: pd.DataFrame,
        all_clusters: pd.DataFrame,
        root_keywords: list[str],
    ) -> None:
        """生成全局摘要报告"""
        report = self._build_global_report(all_raw, all_clean, all_clusters, root_keywords)
        path = OUTPUT_DIR / "SUMMARY_REPORT.txt"
        path.write_text(report, encoding="utf-8")
        logger.info("[Summary] 全局摘要报告已写入: %s", path)

    def _build_report(
        self,
        root_keyword: str,
        raw_df: pd.DataFrame,
        clean_df: pd.DataFrame,
        cluster_df: pd.DataFrame,
    ) -> str:
        """构建单词根摘要文本"""
        lines = [
            "=" * 60,
            f"  SEO 关键词采集摘要报告",
            f"  词根: {root_keyword}",
            f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "【采集数量】",
            f"  原始关键词:  {len(raw_df):>6} 条",
            f"  清洗后关键词:{len(clean_df):>6} 条",
            f"  去重率:      {self._dedup_rate(raw_df, clean_df)}",
            "",
        ]

        # 渠道来源统计
        if not raw_df.empty and "channel" in raw_df.columns:
            lines += ["【渠道来源统计（原始）】"]
            channel_counts = raw_df["channel"].value_counts()
            for ch, cnt in channel_counts.items():
                lines.append(f"  {ch:<30} {cnt:>5} 条")
            lines.append("")

        # 关键词类型分布
        if not clean_df.empty and "keyword_type" in clean_df.columns:
            lines += ["【关键词类型分布（清洗后）】"]
            type_counts = clean_df["keyword_type"].value_counts()
            for ktype, cnt in type_counts.items():
                lines.append(f"  {ktype:<40} {cnt:>5} 条")
            lines.append("")

        # 意图分布
        if not clean_df.empty and "search_intent" in clean_df.columns:
            lines += ["【搜索意图分布】"]
            intent_counts = clean_df["search_intent"].value_counts()
            for intent, cnt in intent_counts.items():
                lines.append(f"  {intent:<20} {cnt:>5} 条")
            lines.append("")

        # 商业价值分布
        if not clean_df.empty and "commercial_value" in clean_df.columns:
            lines += ["【商业价值分布】"]
            val_counts = clean_df["commercial_value"].value_counts()
            for val, cnt in val_counts.items():
                lines.append(f"  {val:<10} {cnt:>5} 条")
            lines.append("")

        # Top 20 高价值关键词
        if not clean_df.empty:
            high_value = clean_df[
                clean_df.get("commercial_value", pd.Series(dtype=str)) == "High"
            ] if "commercial_value" in clean_df.columns else pd.DataFrame()
            if not high_value.empty:
                lines += ["【Top 20 高商业价值关键词】"]
                for kw in high_value["keyword"].head(20).tolist():
                    lines.append(f"  · {kw}")
                lines.append("")

        # 聚类摘要
        if not cluster_df.empty and "cluster_label" in cluster_df.columns:
            lines += ["【聚类分布（Top 10 聚类）】"]
            cluster_counts = cluster_df["cluster_label"].value_counts().head(10)
            for label, cnt in cluster_counts.items():
                lines.append(f"  {str(label):<50} {cnt:>4} 条")
            lines.append("")

        lines += ["=" * 60]
        return "\n".join(lines)

    def _build_global_report(
        self,
        all_raw: pd.DataFrame,
        all_clean: pd.DataFrame,
        all_clusters: pd.DataFrame,
        root_keywords: list[str],
    ) -> str:
        """构建全局摘要"""
        lines = [
            "=" * 60,
            "  SEO 关键词采集 - 全局汇总报告",
            f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            f"【词根列表】",
        ]
        for kw in root_keywords:
            lines.append(f"  · {kw}")
        lines += [
            "",
            f"【总计】",
            f"  原始关键词总量:  {len(all_raw):>6} 条",
            f"  清洗后总量:      {len(all_clean):>6} 条",
            f"  聚类数量:        {all_clusters['cluster_id'].nunique() if not all_clusters.empty and 'cluster_id' in all_clusters.columns else 0}",
            "",
        ]

        if not all_raw.empty and "root_keyword" in all_raw.columns:
            lines += ["【各词根采集量（原始）】"]
            root_counts = all_raw["root_keyword"].value_counts()
            for root, cnt in root_counts.items():
                lines.append(f"  {root:<40} {cnt:>5} 条")
            lines.append("")

        if not all_clean.empty and "keyword_type" in all_clean.columns:
            lines += ["【全局关键词类型分布】"]
            type_counts = all_clean["keyword_type"].value_counts()
            for ktype, cnt in type_counts.items():
                lines.append(f"  {ktype:<40} {cnt:>5} 条")
            lines.append("")

        lines += ["=" * 60]
        return "\n".join(lines)

    @staticmethod
    def _dedup_rate(raw_df: pd.DataFrame, clean_df: pd.DataFrame) -> str:
        if raw_df.empty:
            return "N/A"
        rate = (1 - len(clean_df) / max(len(raw_df), 1)) * 100
        return f"{rate:.1f}%"
