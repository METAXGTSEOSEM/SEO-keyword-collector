"""
SEO 页面类型推荐器
根据关键词类型和意图，推荐最适合的页面类型
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ─── 页面类型映射规则 ──────────────────────────────────────────
# (keyword_type, search_intent) → page_type
PAGE_TYPE_MATRIX: dict[tuple[str, str], str] = {
    # 核心产品词
    ("Core Product Keyword", "Transactional"):    "Product Page",
    ("Core Product Keyword", "Commercial"):       "Category / Collection Page",
    ("Core Product Keyword", "Informational"):    "Product Detail Page",
    ("Core Product Keyword", "Navigational"):     "Product Page",

    # 供应商/工厂词
    ("Supplier / Factory / Manufacturer Keyword", "Transactional"):  "Supplier Landing Page",
    ("Supplier / Factory / Manufacturer Keyword", "Commercial"):     "About / Company Page",
    ("Supplier / Factory / Manufacturer Keyword", "Informational"):  "About / Company Page",

    # OEM/ODM
    ("Custom / OEM / ODM Keyword", "Transactional"):  "Custom Order / RFQ Page",
    ("Custom / OEM / ODM Keyword", "Commercial"):     "OEM Service Page",
    ("Custom / OEM / ODM Keyword", "Informational"):  "Blog / Guide Page",

    # 规格参数
    ("Specification Keyword", "Transactional"):   "Product Spec Page",
    ("Specification Keyword", "Informational"):   "Technical Datasheet Page",
    ("Specification Keyword", "Commercial"):      "Product Comparison Page",

    # 应用场景
    ("Application Keyword", "Informational"):     "Application / Use-case Page",
    ("Application Keyword", "Commercial"):        "Solution Page",
    ("Application Keyword", "Transactional"):     "Product Category Page",

    # 行业关键词
    ("Industry Keyword", "Informational"):        "Industry Solution Page",
    ("Industry Keyword", "Commercial"):           "Industry Landing Page",

    # 问题解决
    ("Problem Solving Keyword", "Informational"): "Blog / FAQ Page",
    ("Problem Solving Keyword", "Commercial"):    "FAQ / Troubleshooting Page",

    # 认证
    ("Certification Keyword", "Informational"):   "Certification Page",
    ("Certification Keyword", "Commercial"):      "Quality Assurance Page",

    # 长尾词
    ("Long Tail Keyword", "Informational"):       "Blog / Guide Page",
    ("Long Tail Keyword", "Commercial"):          "Landing Page",
    ("Long Tail Keyword", "Transactional"):       "Product / Category Page",

    # 竞品
    ("Competitor Keyword", "Commercial"):         "Comparison Page",
    ("Competitor Keyword", "Informational"):      "Blog / Comparison Article",

    # 工业通用
    ("Industrial Keyword", "Informational"):      "Industry Blog Page",
    ("Industrial Keyword", "Commercial"):         "Category Page",
    ("Industrial Keyword", "Transactional"):      "Product Category Page",

    # 低意图
    ("Low Intent / Negative Keyword", "Informational"): "Skip / No Page Needed",
    ("Low Intent / Negative Keyword", "Commercial"):    "Skip / No Page Needed",
    ("Low Intent / Negative Keyword", "Transactional"): "Skip / No Page Needed",
}


class PageMapper:
    """SEO 页面类型推荐器"""

    def map(self, df: pd.DataFrame) -> pd.DataFrame:
        """为每条关键词推荐 page_type"""
        logger.info("开始页面类型推荐 %d 条", len(df))
        df = df.copy()
        df["page_type"] = df.apply(self._map_row, axis=1)
        logger.info("页面类型推荐完成")
        return df

    def _map_row(self, row: pd.Series) -> str:
        """推荐单条记录的页面类型"""
        ktype = row.get("keyword_type", "")
        intent = row.get("search_intent", "")
        # 精确匹配
        key = (ktype, intent)
        if key in PAGE_TYPE_MATRIX:
            return PAGE_TYPE_MATRIX[key]
        # 只用 keyword_type 匹配（忽略 intent）
        for (kt, _intent), page in PAGE_TYPE_MATRIX.items():
            if kt == ktype:
                return page
        return "Blog / General Page"
