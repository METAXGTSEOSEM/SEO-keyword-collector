# 工业 B2B 多渠道 SEO 关键词采集系统

> **Industrial B2B Multi-Channel SEO Keyword Collection System**  
> 自动从 Google / Bing / YouTube / Amazon / Alibaba / Made-in-China / Reddit / 竞品网站 / Google Trends 多渠道采集 B2B 工业关键词，并完成清洗、分类、聚类和导出。

---

## 📁 项目结构

```
seo-keyword-collector/
├── main.py                      # 主程序入口
├── requirements.txt
│
├── config/
│   └── settings.py              # 全局配置（渠道开关、代理、参数）
│
├── collectors/                  # 各渠道采集器
│   ├── base_collector.py        # 抽象基类（UA轮换、限速、重试）
│   ├── google_collector.py      # Google Suggest + PAA + SERP
│   ├── bing_collector.py        # Bing Suggest + SERP
│   ├── youtube_collector.py     # YouTube Suggest + SERP
│   ├── amazon_collector.py      # Amazon Suggest
│   ├── alibaba_collector.py     # Alibaba Suggest + 产品标题
│   ├── madeinchina_collector.py # Made-in-China 产品标题
│   ├── forum_collector.py       # Reddit / Quora 问题词
│   ├── competitor_collector.py  # 竞品 Title/Meta/H1/H2/URL
│   └── trends_collector.py      # Google Trends 相关查询
│
├── analyzers/                   # 分析处理器
│   ├── cleaner.py               # 清洗、去重
│   ├── classifier.py            # 13种类型分类
│   ├── intent_analyzer.py       # 搜索意图判断
│   ├── clusterer.py             # TF-IDF + KMeans 聚类
│   └── page_mapper.py           # SEO 页面类型推荐
│
├── exporters/                   # 导出器
│   ├── csv_exporter.py          # CSV 输出
│   └── summary_exporter.py      # TXT 摘要报告
│
├── output/                      # 输出目录（自动创建）
│   ├── hydraulic-cargo-lift/
│   │   ├── keywords_raw.csv
│   │   ├── keywords_clean.csv
│   │   ├── keyword_clusters.csv
│   │   └── keyword_summary.txt
│   ├── all_keywords.csv
│   ├── all_keywords_clean.csv
│   ├── all_keyword_clusters.csv
│   ├── final_keyword_map.csv
│   └── SUMMARY_REPORT.txt
│
└── logs/                        # 日志目录（自动创建）
```

---

## ⚙️ 安装与配置

### 1. 克隆项目

```powershell
cd f:\DevStream-Python\projects\seo-keyword-collector
```

### 2. 安装依赖（使用 uv）

```powershell
# 初始化 uv 项目（如果尚未初始化）
uv init --python 3.12

# 安装生产依赖
uv add requests beautifulsoup4 lxml playwright pandas numpy scikit-learn pytrends python-dotenv tqdm

# 安装 Playwright 浏览器（Chromium，用于 JS 渲染）
uv run playwright install chromium
```

### 3. 配置渠道开关（可选）

编辑 `config/settings.py`：

```python
CHANNELS_ENABLED = {
    "google_suggest": True,
    "bing_suggest":   True,
    "reddit":         True,
    "competitor":     False,  # 关闭某渠道
    ...
}
```

### 4. 配置竞品域名（可选）

```python
COMPETITOR_DOMAINS = [
    "www.competitor-a.com",
    "www.competitor-b.com",
]
```

---

## 🚀 运行

### Windows 运行命令

```powershell
# 方式一（uv，推荐）
cd f:\DevStream-Python\projects\seo-keyword-collector
uv run main.py

# 方式二（直接 Python）
python main.py
```

### 示例交互

```
════════════════════════════════════════════════════════════
  🏭 工业 B2B 多渠道 SEO 关键词采集系统
════════════════════════════════════════════════════════════

请输入产品词根，可多个，一行一个或用逗号分隔。
输入完成后，空行回车继续。

>>> hydraulic cargo lift
>>> freight elevator
>>> scissor lift
>>> （空行回车）

✅ 已接收 3 个词根:
   · hydraulic cargo lift
   · freight elevator
   · scissor lift

════════════════════════════════════════════════════════════
  [1/3] 处理词根: hydraulic cargo lift
════════════════════════════════════════════════════════════

🌐 开始多渠道采集...
  [1/9] 🔍 正在采集: google_suggest ... ✓ 234 条
  [2/9] 🔍 正在采集: bing_suggest ...   ✓ 187 条
  [3/9] 🔍 正在采集: youtube_suggest .. ✓ 56 条
  [4/9] 🔍 正在采集: amazon_suggest ...  ✓ 44 条
  [5/9] 🔍 正在采集: alibaba_suggest ..  ✓ 89 条
  [6/9] 🔍 正在采集: madeinchina ...    ✓ 112 条
  [7/9] 🔍 正在采集: reddit ...         ✓ 38 条
  [8/9] 🔍 正在采集: competitor ...     ✓ 67 条
  [9/9] 🔍 正在采集: google_trends ...  ✓ 25 条

  → 采集完成，原始记录: 852 条

📊 开始分析流水线...
  [1/5] 清洗关键词... ✓ 412 条（清除 440 条）
  [2/5] 关键词分类... ✓
  [3/5] 搜索意图分析... ✓
  [4/5] 页面类型推荐... ✓
  [5/5] NLP 聚类分析... ✓ 20 个聚类
```

---

## 📊 输出字段说明

| 字段 | 说明 |
|------|------|
| `keyword` | 关键词（已规范化小写） |
| `root_keyword` | 对应的词根 |
| `source` | 具体来源（如 google_suggest, bing_serp） |
| `channel` | 渠道名称（google/bing/youtube 等） |
| `keyword_type` | 关键词类型（13种分类） |
| `search_intent` | 搜索意图（Transactional/Commercial/Informational/Navigational） |
| `page_type` | 推荐 SEO 页面类型 |
| `commercial_value` | 商业价值（High/Medium/Low） |
| `title` | 来源页面标题 |
| `description` | 来源页面描述 |
| `url` | 来源 URL |
| `collected_at` | 采集时间（UTC ISO 格式） |
| `cluster_id` | 聚类 ID |
| `cluster_label` | 聚类标签（含代表词） |

---

## 🔑 关键词分类（13种）

| 类型 | 说明 | 示例 |
|------|------|------|
| Core Product Keyword | 核心产品词 | "hydraulic cargo lift" |
| Supplier / Factory / Manufacturer Keyword | 供应商词 | "cargo lift manufacturer china" |
| Custom / OEM / ODM Keyword | 定制词 | "custom hydraulic lift oem" |
| Industrial Keyword | 工业通用词 | "heavy duty industrial lift" |
| Competitor Keyword | 竞品词 | "scissor lift vs cargo lift" |
| Brand Keyword | 品牌词 | "toyota forklift" |
| Problem Solving Keyword | 问题词 | "how to install a cargo lift" |
| Application Keyword | 应用场景词 | "cargo lift for warehouse" |
| Industry Keyword | 行业词 | "logistics material handling" |
| Certification Keyword | 认证词 | "ce certified hydraulic lift" |
| Long Tail Keyword | 长尾词 | "2 ton hydraulic cargo lift price china" |
| Specification Keyword | 规格参数词 | "2000kg capacity hydraulic lift" |
| Low Intent / Negative Keyword | 低意图词 | "used cargo lift rental" |

---

## 🔧 预留 API 接口

配置环境变量启用付费 API：

```powershell
# .env 文件（项目根目录）
SEMRUSH_API_KEY=your_key_here
AHREFS_API_KEY=your_key_here
GOOGLE_ADS_DEVELOPER_TOKEN=your_token
GOOGLE_ADS_CUSTOMER_ID=123-456-7890
```

---

## ♻️ 断点续跑

如果采集中途中断，重新运行程序后会自动从断点恢复，无需重新采集已完成的词根。

断点文件保存在 `.checkpoints/` 目录。

---

## ⚠️ 注意事项

1. **Google 限速**：Google Suggest API 是公开端点，但大量请求会被临时封禁，建议设置 `REQUEST_DELAY_MIN = 2.0`
2. **Playwright**：需要先运行 `uv run playwright install chromium` 安装浏览器
3. **代理**：如需高频采集，建议在 `config/settings.py` 中配置代理列表
4. **pytrends**：Google Trends 有速率限制，如失败会自动跳过，不影响其他渠道
