"""
关键词 NLP 聚类器
使用 TF-IDF + TruncatedSVD + KMeans 对关键词进行语义聚类
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class KeywordClusterer:
    """
    关键词聚类器。
    使用 TF-IDF + SVD 降维 + KMeans 聚类。
    对小数据集自动降低聚类数量，确保稳健运行。
    """

    def __init__(
        self,
        n_clusters: int = 20,
        n_components: int = 50,
        min_df: int = 1,
        random_state: int = 42,
    ) -> None:
        self.n_clusters = n_clusters
        self.n_components = n_components
        self.min_df = min_df
        self.random_state = random_state

    def cluster(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        对 DataFrame 中的关键词进行聚类，添加 cluster_id 和 cluster_label 列。
        """
        if df.empty or len(df) < 3:
            logger.warning("数据量不足，跳过聚类")
            df = df.copy()
            df["cluster_id"] = 0
            df["cluster_label"] = "cluster_0"
            return df

        try:
            return self._run_clustering(df)
        except Exception as exc:
            logger.warning("聚类失败，跳过: %s", exc)
            df = df.copy()
            df["cluster_id"] = 0
            df["cluster_label"] = "cluster_0"
            return df

    def _run_clustering(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行实际聚类逻辑"""
        from sklearn.cluster import KMeans
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import Normalizer

        keywords = df["keyword"].tolist()
        n = len(keywords)

        # 自动调整参数防止越界
        n_clusters = min(self.n_clusters, n - 1, 50)
        n_components = min(self.n_components, n - 1, n_clusters)

        if n_clusters < 2:
            df = df.copy()
            df["cluster_id"] = 0
            df["cluster_label"] = "cluster_0"
            return df

        logger.info("开始 TF-IDF + SVD + KMeans 聚类，n=%d k=%d", n, n_clusters)

        # TF-IDF 向量化（字符 n-gram 比词 n-gram 对短文本更鲁棒）
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=self.min_df,
            max_features=20000,
            sublinear_tf=True,
        )
        X = vectorizer.fit_transform(keywords)

        # SVD 降维
        svd = TruncatedSVD(n_components=n_components, random_state=self.random_state)
        normalizer = Normalizer(copy=False)
        X_reduced = normalizer.fit_transform(svd.fit_transform(X))

        # KMeans 聚类
        km = KMeans(
            n_clusters=n_clusters,
            init="k-means++",
            max_iter=300,
            n_init=10,
            random_state=self.random_state,
        )
        labels = km.fit_predict(X_reduced)

        df = df.copy()
        df["cluster_id"] = labels

        # 为每个聚类生成标签（用聚类中最短且最代表性的关键词）
        cluster_labels = self._generate_cluster_labels(df)
        df["cluster_label"] = df["cluster_id"].map(cluster_labels)

        logger.info("聚类完成，共 %d 个聚类", n_clusters)
        return df

    def _generate_cluster_labels(self, df: pd.DataFrame) -> dict[int, str]:
        """
        为每个聚类生成可读标签。
        策略：取该聚类中词频最高的短关键词（2-3词）。
        """
        cluster_labels: dict[int, str] = {}

        for cluster_id in df["cluster_id"].unique():
            subset = df[df["cluster_id"] == cluster_id]["keyword"]
            # 优先选词数少（2-3词）且出现频率高的词
            candidates = [kw for kw in subset if 1 <= len(kw.split()) <= 3]
            if candidates:
                # 取最短的（最接近核心词）
                label = min(candidates, key=len)
            else:
                label = subset.iloc[0] if len(subset) > 0 else f"cluster_{cluster_id}"

            cluster_labels[cluster_id] = f"[{cluster_id}] {label}"

        return cluster_labels

    def get_cluster_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成聚类摘要：每个聚类的关键词数量、代表词"""
        if "cluster_id" not in df.columns:
            return pd.DataFrame()

        summary_rows = []
        for cluster_id in sorted(df["cluster_id"].unique()):
            subset = df[df["cluster_id"] == cluster_id]
            label = subset["cluster_label"].iloc[0] if len(subset) > 0 else ""
            keywords_sample = " | ".join(subset["keyword"].head(5).tolist())
            summary_rows.append({
                "cluster_id": cluster_id,
                "cluster_label": label,
                "keyword_count": len(subset),
                "sample_keywords": keywords_sample,
                "keyword_types": "|".join(subset["keyword_type"].unique().tolist()) if "keyword_type" in subset.columns else "",
            })

        return pd.DataFrame(summary_rows)
