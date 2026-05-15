# 工业 B2B 多渠道 SEO 关键词采集系统

> **Industrial B2B Multi-Channel SEO Keyword Collection System**  
> 自动从 Google / Bing / YouTube / Amazon / Alibaba / Made-in-China / Reddit / 竞品网站 / Google Trends 多渠道采集 B2B 工业关键词，并完成清洗、分类、聚类和导出。

---

## 📁 项目结构

```
seo-keyword-collector/
├── main.py                      # 主程序入口
├── pyproject.toml               # uv 依赖声明（自动管理）
├── requirements.txt             # pip 备用依赖列表
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
│   ├── classifier.py            # 13 种类型分类
│   ├── intent_analyzer.py       # 搜索意图判断
│   ├── clusterer.py             # TF-IDF + KMeans 聚类
│   └── page_mapper.py           # SEO 页面类型推荐
│
├── exporters/                   # 导出器
│   ├── csv_exporter.py          # CSV 输出
│   └── summary_exporter.py      # TXT 摘要报告
│
├── output/                      # 输出目录（运行后自动生成）
│   ├── hydraulic-cargo-lift/    # 每个词根单独子目录
│   │   ├── keywords_raw.csv
│   │   ├── keywords_clean.csv
│   │   ├── keyword_clusters.csv
│   │   └── keyword_summary.txt
│   ├── all_keywords.csv         # 全部词根汇总
│   ├── all_keywords_clean.csv
│   ├── all_keyword_clusters.csv
│   ├── final_keyword_map.csv    # 高价值关键词地图
│   └── SUMMARY_REPORT.txt       # 全局摘要报告
│
├── logs/                        # 日志目录（运行后自动生成）
└── .checkpoints/                # 断点续跑缓存（运行后自动生成）
```

---

## ⚙️ 安装与配置

### 前置要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.12 | 必须 |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | 最新版 | 推荐包管理器 |
| Git | 任意版本 | 用于克隆项目 |

安装 uv（如果未安装）：

```powershell
# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

### 第 1 步：克隆项目

```powershell
git clone https://github.com/METAXGTSEOSEM/SEO-keyword-collector.git
cd SEO-keyword-collector
```

---

### 第 2 步：安装依赖

```powershell
# uv 会自动读取 pyproject.toml，创建虚拟环境并安装所有依赖
uv sync
```

> **注意**：不需要手动运行 `uv init`，项目已包含 `pyproject.toml`。

**备用方案（使用 pip）：**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### 第 3 步：安装 Playwright 浏览器

```powershell
# 安装 Chromium 内核（部分采集器需要 JS 渲染时使用）
uv run playwright install chromium
```

> 如果不需要 JS 渲染功能，可跳过此步骤。系统会自动降级到 requests 模式。

---

### 第 4 步：配置（可选）

**关闭/开启采集渠道** — 编辑 `config/settings.py`：

```python
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
```

**配置竞品域名** — 编辑 `config/settings.py`：

```python
COMPETITOR_DOMAINS = [
    "www.competitor-a.com",
    "www.competitor-b.com",
]
```

**配置请求延迟**（高频采集时建议调大）：

```python
REQUEST_DELAY_MIN = 2.0   # 建议 2.0 以上，避免被 Google 限速
REQUEST_DELAY_MAX = 4.0
```

---

## 🚀 运行

### Windows 运行命令

```powershell
# 方式一：uv（推荐，自动使用项目虚拟环境）
uv run main.py

# 方式二：激活虚拟环境后运行
.venv\Scripts\activate
python main.py
```

> ⚠️ **不要** 直接用系统 `python main.py`（未激活虚拟环境时会报找不到依赖包）。

---

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

💾 导出文件...
  ✓ 词根 'hydraulic cargo lift' 处理完成
  📁 输出目录: output/hydraulic-cargo-lift/

🎉 全部完成！总耗时: 142.3 秒
```

---

## 📊 输出字段说明

| 字段 | 说明 |
|------|------|
| `keyword` | 关键词（已规范化小写） |
| `root_keyword` | 对应的词根 |
| `source` | 具体来源（如 `google_suggest`、`bing_serp`） |
| `channel` | 渠道名称（`google` / `bing` / `youtube` 等） |
| `keyword_type` | 关键词类型（13 种分类，见下表） |
| `search_intent` | 搜索意图（`Transactional` / `Commercial` / `Informational` / `Navigational`） |
| `page_type` | 推荐 SEO 页面类型 |
| `commercial_value` | 商业价值（`High` / `Medium` / `Low`） |
| `title` | 来源页面标题 |
| `description` | 来源页面描述 |
| `url` | 来源 URL |
| `collected_at` | 采集时间（UTC ISO 格式） |
| `cluster_id` | 聚类 ID |
| `cluster_label` | 聚类标签（含代表词） |

---

## 🔑 关键词分类（13 种）

| 类型 | 说明 | 示例 |
|------|------|------|
| Core Product Keyword | 核心产品词 | `hydraulic cargo lift` |
| Supplier / Factory / Manufacturer Keyword | 供应商/工厂/制造商词 | `cargo lift manufacturer china` |
| Custom / OEM / ODM Keyword | 定制/OEM/ODM 词 | `custom hydraulic lift oem` |
| Specification Keyword | 规格参数词 | `2000kg capacity hydraulic lift` |
| Application Keyword | 应用场景词 | `cargo lift for warehouse` |
| Industry Keyword | 行业词 | `logistics material handling` |
| Industrial Keyword | 工业通用词 | `heavy duty industrial lift` |
| Problem Solving Keyword | 问题解决词 | `how to install a cargo lift` |
| Certification Keyword | 认证词 | `ce certified hydraulic lift` |
| Brand Keyword | 品牌词 | `toyota forklift` |
| Competitor Keyword | 竞品词 | `scissor lift vs cargo lift` |
| Long Tail Keyword | 长尾词 | `2 ton hydraulic cargo lift price china` |
| Low Intent / Negative Keyword | 低意图/负向词 | `used cargo lift rental` |

---

## 🔧 预留 API 接口

在项目根目录创建 `.env` 文件，填入 API 密钥即可启用付费数据源：

```ini
# .env  （此文件已加入 .gitignore，不会上传到 GitHub）
SEMRUSH_API_KEY=your_key_here
AHREFS_API_KEY=your_key_here
GOOGLE_ADS_DEVELOPER_TOKEN=your_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=123-456-7890
```

---

## ♻️ 断点续跑

采集中途中断后，**重新运行程序**会自动加载断点，跳过已完成的词根，无需重新采集。

- 断点文件位置：`.checkpoints/<词根>.json`
- 手动清除断点（强制重新采集）：删除对应的 `.checkpoints/*.json` 文件

---

## ⚠️ 注意事项

1. **Google 限速**：Google Suggest 是公开端点，大量请求会触发临时封禁，建议将 `REQUEST_DELAY_MIN` 设为 `2.0` 秒以上
2. **Playwright 可选**：如果没有安装 Chromium，JS 渲染功能会自动跳过，不影响其他渠道采集
3. **代理支持**：高频采集时，在 `config/settings.py` 中配置 `PROXY_LIST` 并设 `PROXY_ENABLED = True`
4. **Google Trends 限流**：`pytrends` 有速率限制，失败后自动跳过，不影响其他渠道
5. **Alibaba / Made-in-China**：这两个平台 HTML 结构会变化，如采集结果为空属正常，可通过更新 CSS 选择器适配

---

## 🔄 后续更新代码

```powershell
# 修改代码后，提交并推送到 GitHub
git add .
git commit -m "feat: 描述你的改动"
git push
```
