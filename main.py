"""
工业 B2B 多渠道 SEO 关键词采集系统
主程序入口

运行方式:
    uv run main.py
    或
    python main.py
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

# ─── 路径修复（确保子包可以正常导入）──────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import (
    CHANNELS_ENABLED,
    CHECKPOINT_DIR,
    LOG_DIR,
    OUTPUT_DIR,
)
from collectors import (
    AlibabaCollector,
    AmazonCollector,
    BingCollector,
    CompetitorCollector,
    ForumCollector,
    GoogleCollector,
    MadeinchinaCollector,
    TrendsCollector,
    YouTubeCollector,
)
from collectors.base_collector import KeywordRecord
from analyzers import (
    KeywordCleaner,
    KeywordClassifier,
    IntentAnalyzer,
    KeywordClusterer,
    PageMapper,
)
from exporters import CsvExporter, SummaryExporter

# ─── 日志配置 ──────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            LOG_DIR / f"collect_{time.strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("main")


# ═══════════════════════════════════════════════════════════════
# 断点续跑支持
# ═══════════════════════════════════════════════════════════════

def _checkpoint_path(root_keyword: str) -> Path:
    """返回断点文件路径"""
    safe_name = root_keyword.lower().replace(" ", "_")
    return CHECKPOINT_DIR / f"{safe_name}.json"


def _save_checkpoint(root_keyword: str, records: list[dict]) -> None:
    """保存采集结果到断点文件"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = _checkpoint_path(root_keyword)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("[Checkpoint] 已保存 %d 条到: %s", len(records), path)


def _load_checkpoint(root_keyword: str) -> Optional[list[dict]]:
    """加载断点文件（如果存在）"""
    path = _checkpoint_path(root_keyword)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("[Checkpoint] 已加载断点: %d 条", len(data))
        return data
    return None


def _clear_checkpoint(root_keyword: str) -> None:
    """清除断点文件（采集完成后调用）"""
    path = _checkpoint_path(root_keyword)
    if path.exists():
        path.unlink()


# ═══════════════════════════════════════════════════════════════
# 采集逻辑
# ═══════════════════════════════════════════════════════════════

def collect_for_root(root_keyword: str) -> list[dict]:
    """
    对单个词根执行全渠道采集。
    支持断点续跑：如果存在断点，直接加载不重新采集。
    返回 dict 列表（可直接构建 DataFrame）。
    """
    # 检查断点
    cached = _load_checkpoint(root_keyword)
    if cached:
        print(f"\n  ✓ 发现断点数据（{len(cached)} 条），跳过重新采集。")
        print(f"    如需重新采集，请删除: {_checkpoint_path(root_keyword)}")
        return cached

    all_records: list[dict] = []

    # ─── 所有采集器配置 ────────────────────────────────────────
    collector_registry = [
        ("google_suggest",  GoogleCollector),
        ("bing_suggest",    BingCollector),
        ("youtube_suggest", YouTubeCollector),
        ("amazon_suggest",  AmazonCollector),
        ("alibaba_suggest", AlibabaCollector),
        ("madeinchina",     MadeinchinaCollector),
        ("reddit",          ForumCollector),
        ("competitor",      CompetitorCollector),
        ("google_trends",   TrendsCollector),
    ]

    total_collectors = len(collector_registry)
    for idx, (channel_key, CollectorClass) in enumerate(collector_registry, 1):
        # 检查渠道开关
        if not CHANNELS_ENABLED.get(channel_key, True):
            print(f"  [{idx}/{total_collectors}] ⏭  {channel_key} 已禁用，跳过")
            continue

        print(f"  [{idx}/{total_collectors}] 🔍 正在采集: {channel_key} ...", end=" ", flush=True)
        try:
            collector = CollectorClass(root_keyword)
            records: list[KeywordRecord] = collector.collect()
            count = len(records)
            all_records.extend([r.to_dict() for r in records])
            print(f"✓ {count} 条")
        except Exception as exc:
            logger.exception("[%s] 采集器异常，已跳过: %s", channel_key, exc)
            print(f"✗ 失败（已跳过）: {exc}")

    # 保存断点
    _save_checkpoint(root_keyword, all_records)
    return all_records


# ═══════════════════════════════════════════════════════════════
# 分析流水线
# ═══════════════════════════════════════════════════════════════

def analyze_pipeline(
    raw_records: list[dict],
    root_keywords: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    执行完整分析流水线：
    清洗 → 分类 → 意图 → 页面类型 → 聚类
    返回: (raw_df, clean_df, cluster_df)
    """
    raw_df = pd.DataFrame(raw_records)
    if raw_df.empty:
        logger.warning("原始数据为空，跳过分析")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    print("\n📊 开始分析流水线...")

    # ① 清洗
    print("  [1/5] 清洗关键词...", end=" ", flush=True)
    cleaner = KeywordCleaner()
    clean_df = cleaner.clean(raw_df)
    print(f"✓ {len(clean_df)} 条（清除 {len(raw_df) - len(clean_df)} 条）")

    # ② 分类
    print("  [2/5] 关键词分类...", end=" ", flush=True)
    classifier = KeywordClassifier(root_keywords=root_keywords)
    clean_df = classifier.classify(clean_df)
    print("✓")

    # ③ 意图分析
    print("  [3/5] 搜索意图分析...", end=" ", flush=True)
    intent_analyzer = IntentAnalyzer()
    clean_df = intent_analyzer.analyze(clean_df)
    print("✓")

    # ④ 页面类型推荐
    print("  [4/5] 页面类型推荐...", end=" ", flush=True)
    page_mapper = PageMapper()
    clean_df = page_mapper.map(clean_df)
    print("✓")

    # ⑤ 聚类
    print("  [5/5] NLP 聚类分析...", end=" ", flush=True)
    from config.settings import CLUSTER_N_CLUSTERS, CLUSTER_N_COMPONENTS
    clusterer = KeywordClusterer(
        n_clusters=CLUSTER_N_CLUSTERS,
        n_components=CLUSTER_N_COMPONENTS,
    )
    cluster_df = clusterer.cluster(clean_df)
    cluster_summary = clusterer.get_cluster_summary(cluster_df)
    print(f"✓ {cluster_df['cluster_id'].nunique() if not cluster_df.empty else 0} 个聚类")

    return raw_df, clean_df, cluster_df


# ═══════════════════════════════════════════════════════════════
# 用户输入处理
# ═══════════════════════════════════════════════════════════════

def prompt_root_keywords() -> list[str]:
    """
    交互式获取用户输入的词根列表。
    支持多行或逗号分隔。
    """
    print("\n" + "═" * 60)
    print("  🏭 工业 B2B 多渠道 SEO 关键词采集系统")
    print("═" * 60)
    print()
    print("请输入产品词根，可多个，一行一个或用逗号分隔。")
    print("输入完成后，空行回车继续（或直接按 Ctrl+C 退出）。")
    print()
    print("示例:")
    print("  hydraulic cargo lift")
    print("  freight elevator")
    print("  scissor lift")
    print()
    print("─" * 60)

    lines = []
    try:
        while True:
            line = input(">>> ").strip()
            if not line:
                if lines:
                    break
                continue
            lines.append(line)
    except KeyboardInterrupt:
        print("\n\n退出。")
        sys.exit(0)

    # 解析：支持逗号分隔
    keywords = []
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        keywords.extend([p for p in parts if p])

    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower not in seen:
            seen.add(kw_lower)
            unique_keywords.append(kw.lower())

    return unique_keywords


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """程序主入口"""
    start_time = time.time()

    # ─── 获取词根输入 ──────────────────────────────────────────
    root_keywords = prompt_root_keywords()
    if not root_keywords:
        print("❌ 未输入任何词根，退出。")
        sys.exit(1)

    print(f"\n✅ 已接收 {len(root_keywords)} 个词根:")
    for kw in root_keywords:
        print(f"   · {kw}")

    # ─── 初始化导出器 ──────────────────────────────────────────
    csv_exporter = CsvExporter()
    summary_exporter = SummaryExporter()

    # ─── 全局汇总容器 ──────────────────────────────────────────
    all_raw_dfs: list[pd.DataFrame] = []
    all_clean_dfs: list[pd.DataFrame] = []
    all_cluster_dfs: list[pd.DataFrame] = []

    # ─── 逐词根处理 ────────────────────────────────────────────
    for i, root_keyword in enumerate(root_keywords, 1):
        print(f"\n{'═' * 60}")
        print(f"  [{i}/{len(root_keywords)}] 处理词根: {root_keyword}")
        print("═" * 60)

        # ① 采集
        print(f"\n🌐 开始多渠道采集...")
        raw_records = collect_for_root(root_keyword)
        print(f"\n  → 采集完成，原始记录: {len(raw_records)} 条")

        if not raw_records:
            print("  ⚠️  未采集到任何数据，跳过此词根")
            continue

        # ② 分析（仅针对当前词根的数据）
        root_raw_df, root_clean_df, root_cluster_df = analyze_pipeline(
            raw_records,
            root_keywords=[root_keyword],
        )

        # ③ 导出单词根文件
        print(f"\n💾 导出文件...")
        out_dir = csv_exporter.export_per_root(
            root_keyword,
            root_raw_df,
            root_clean_df,
            root_cluster_df,
        )
        summary_exporter.export_per_root(
            root_keyword,
            root_raw_df,
            root_clean_df,
            root_cluster_df,
            out_dir=out_dir,
        )

        # ④ 收集到全局列表
        if not root_raw_df.empty:
            all_raw_dfs.append(root_raw_df)
        if not root_clean_df.empty:
            all_clean_dfs.append(root_clean_df)
        if not root_cluster_df.empty:
            all_cluster_dfs.append(root_cluster_df)

        # ⑤ 清除断点（采集和导出都完成）
        _clear_checkpoint(root_keyword)

        print(f"  ✓ 词根 '{root_keyword}' 处理完成")
        print(f"  📁 输出目录: {out_dir}")

    # ─── 汇总所有词根 ──────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print("  🔄 生成全局汇总文件...")
    print("═" * 60)

    if all_raw_dfs:
        all_raw = pd.concat(all_raw_dfs, ignore_index=True)
        all_clean = pd.concat(all_clean_dfs, ignore_index=True) if all_clean_dfs else pd.DataFrame()
        all_clusters = pd.concat(all_cluster_dfs, ignore_index=True) if all_cluster_dfs else pd.DataFrame()

        # 构建 final_keyword_map（高价值关键词映射表）
        final_map = _build_final_keyword_map(all_clean)

        csv_exporter.export_all(all_raw, all_clean, all_clusters, final_map)
        summary_exporter.export_global(all_raw, all_clean, all_clusters, root_keywords)

        elapsed = time.time() - start_time
        print(f"\n{'═' * 60}")
        print("  🎉 全部完成！")
        print(f"  总耗时: {elapsed:.1f} 秒")
        print(f"  原始关键词总量: {len(all_raw)} 条")
        print(f"  清洗后总量:     {len(all_clean)} 条")
        print(f"  输出目录: {OUTPUT_DIR}")
        print("═" * 60)
    else:
        print("  ⚠️  没有成功采集到任何数据。")


def _build_final_keyword_map(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    构建 final_keyword_map：
    过滤掉低意图词，保留 High/Medium 商业价值的关键词，
    按 keyword_type + search_intent 排序。
    """
    if clean_df.empty:
        return pd.DataFrame()

    # 过滤低意图词
    mask = clean_df.get("keyword_type", pd.Series(dtype=str)) != "Low Intent / Negative Keyword"
    df = clean_df[mask].copy() if "keyword_type" in clean_df.columns else clean_df.copy()

    # 按商业价值和关键词类型排序
    value_order = {"High": 0, "Medium": 1, "Low": 2}
    if "commercial_value" in df.columns:
        df["_val_order"] = df["commercial_value"].map(value_order).fillna(3)
        df = df.sort_values(["_val_order", "keyword_type", "keyword"])
        df.drop(columns=["_val_order"], inplace=True)

    return df.reset_index(drop=True)


if __name__ == "__main__":
    main()
