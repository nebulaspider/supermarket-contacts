# 🏪 SupermarketIQ — 全球超市客户情报平台

> **Global Retail Intelligence Platform** — 专业级 SaaS 仪表盘 + 全自动化数据管线
>
> 自动发现 → 智能抓取 → 清洗去重 → 质量验证 → 一键部署

---

## ✨ 平台特性

### 🎨 专业界面（Bright Data / Crawlbase 级）

- **双主题切换**：浅色 / 深色模式，一键切换，记忆偏好
- **仪表盘总览**：6 大 KPI 指标卡 + 国家分布柱状图 + 联系方式覆盖率图
- **客户名录**：专业数据表格，支持排序、筛选、分页、全局搜索（⌘K）
- **详情抽屉**：右侧滑出式详情面板，含质量评分环形图、一键复制
- **爬虫监控**：实时展示每个爬虫的运行状态、耗时、抓取量
- **数据质量**：逐字段完整度分析，可视化质量报告
- **响应式设计**：完美适配桌面、平板、手机

### 🔄 全自动化管线（5 步闭环）

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  自动发现     │ →  │  智能抓取     │ →  │  清洗去重     │ →  │  质量验证     │ →  │  自动部署     │
│  Auto        │    │  Scrapy      │    │  Merge &     │    │  Validate &  │    │  GitHub      │
│  Discover    │    │  Multi-brand │    │  Deduplicate │    │  Score       │    │  Pages       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     维基百科            14个品牌            模糊匹配           邮箱/电话验证         推送即部署
     商业目录            并行抓取            智能合并           质量评分(0-100)       定时+手动触发
```

| 步骤 | 模块 | 说明 |
|------|------|------|
| 1️⃣ 自动发现 | `auto_discover.py` | 从维基百科超市连锁列表自动发现新品牌，去重后输出候选列表 |
| 2️⃣ 智能抓取 | Scrapy + 14 个品牌爬虫 | 遵守 robots.txt，自动限速，UA 轮换，代理池可选 |
| 3️⃣ 清洗去重 | `data_manager.py` | 格式标准化 + 公司名模糊匹配去重 + 多源数据智能合并 |
| 4️⃣ 质量验证 | `data_manager.py` | 邮箱格式校验、电话号码校验、URL 校验、质量评分 |
| 5️⃣ 自动部署 | GitHub Actions | 定时/手动触发，数据量骤降保护，自动提交推送触发 Pages 重部署 |

---

## 📁 项目结构

```
supermarket-contacts/
├── index.html                      # 仪表盘主页
├── css/style.css                   # 专业级样式（双主题）
├── js/app.js                       # 前端逻辑（视图/图表/表格/抽屉）
├── data/
│   ├── clients.json                # 最终客户数据（前端读取）
│   ├── clients.scraped.json        # 爬虫临时输出
│   ├── clients.manual.json         # 手动补充数据（可选）
│   ├── new_brands.json             # 自动发现的新品牌
│   └── quality_report.json         # 数据质量报告
├── scraper/
│   ├── auto_discover.py            # 🔍 自动发现新品牌
│   ├── data_manager.py             # 📊 数据管理（合并/去重/验证/评分）
│   ├── run.py                      # 🚀 统一运行入口（完整管线）
│   ├── items.py                    # 数据字段定义
│   ├── settings.py                 # Scrapy 配置
│   ├── middlewares.py              # UA 轮换 + 代理中间件
│   ├── pipelines.py                # 清洗/去重/评分管道
│   └── spiders/                    # 14 个品牌爬虫
│       ├── base_spider.py
│       ├── walmart_spider.py
│       ├── costco_spider.py
│       ├── kroger_spider.py
│       ├── target_spider.py
│       ├── carrefour_spider.py
│       ├── tesco_spider.py
│       ├── aldi_spider.py
│       ├── lidl_spider.py
│       ├── metro_spider.py
│       ├── spar_spider.py
│       ├── seven_eleven_spider.py
│       ├── aeon_spider.py
│       ├── lotte_mart_spider.py
│       └── rt_mart_spider.py
├── .github/workflows/
│   └── update-data.yml             # 全自动化 CI/CD 管线（4 Jobs）
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 快速开始

### 本地运行完整管线

```bash
cd supermarket-contacts
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 运行完整管线（自动发现 + 爬虫 + 数据管理）
python scraper/run.py

# 或分步运行
python scraper/run.py --discover-only   # 只自动发现
python scraper/run.py --scrape-only     # 只跑爬虫
python scraper/run.py --manage-only     # 只做数据管理
python scraper/run.py --spider walmart  # 只跑指定爬虫
python scraper/run.py --list            # 列出所有爬虫
```

### 本地预览仪表盘

```bash
python -m http.server 8000
# 打开 http://localhost:8000
```

---

## 🌐 部署到 GitHub Pages

### 1. 创建仓库并推送

```bash
git init
git add .
git commit -m "Initial: SupermarketIQ platform"
git branch -M main
git remote add origin https://github.com/你的用户名/supermarket-contacts.git
git push -u origin main
```

### 2. 启用 GitHub Pages

- 仓库 → **Settings** → **Pages**
- Source: `Deploy from a branch`
- Branch: `main` / `/(root)`
- 保存后等待 1-2 分钟，网站上线

### 3. 配置自动化（可选）

- 仓库 → **Settings** → **Secrets and variables** → **Actions**
- 如需代理：添加 `PROXY_API_URL` Secret
- 无需代理可跳过，爬虫直连

### 4. 触发首次自动更新

- 仓库 → **Actions** → **SupermarketIQ — Full Automation Pipeline**
- 点击 **Run workflow** → 选择参数 → 运行

---

## ⚙️ 自动化管线详解

### GitHub Actions 工作流（4 个 Job 串行）

| Job | 名称 | 超时 | 说明 |
|-----|------|------|------|
| 1 | `auto-discover` | 10min | 从维基百科发现新品牌，输出 `new_brands.json` |
| 2 | `scrape` | 25min | 14 个品牌爬虫并行抓取，输出 `clients.scraped.json` |
| 3 | `data-management` | 10min | 合并爬虫数据+现有数据+手动数据，去重验证评分 |
| 4 | `deploy` | 5min | 验证数据量，提交推送，触发 Pages 重部署 |

### 安全保护机制

- **数据备份**：每次运行前备份 `clients.json`
- **空数据拦截**：新数据为空时自动失败，不覆盖
- **骤降保护**：数据量下降超 50% 时自动回滚（可 `force_update` 覆盖）
- **并发控制**：`concurrency` 确保同一时间只有一个管线运行

### 定时配置

默认每周一 UTC 02:00（北京时间 10:00）运行。修改 `.github/workflows/update-data.yml` 中的 `cron`：

```yaml
schedule:
  - cron: '0 2 * * 1'    # 每周一
  # - cron: '0 2 * * *'  # 每天
  # - cron: '0 */6 * * *' # 每6小时
```

---

## 🕷️ 已覆盖品牌（14 个）

| 区域 | 品牌 |
|------|------|
| 🇺🇸 美国 | Walmart, Costco, Kroger, Target |
| 🇪🇺 欧洲 | Carrefour, Tesco, Aldi, Lidl, Metro, SPAR |
| 🇯🇵 日本 | 7-Eleven, Aeon (永旺) |
| 🇰🇷 韩国 | Lotte Mart (乐天玛特) |
| 🇨🇳 中国 | RT-Mart (大润发) |

> 自动发现模块会持续从维基百科等来源发现新品牌，可轻松扩展爬虫覆盖。

### 添加新品牌爬虫

在 `scraper/spiders/` 新建 `xxx_spider.py`：

```python
import scrapy
from scraper.spiders.base_spider import BaseSupermarketSpider

class MyBrandSpider(BaseSupermarketSpider):
    name = 'mybrand'
    brand_name = 'MyBrand'
    country = 'Japan'
    city = 'Tokyo'
    address = '1-2-3 Example, Tokyo'
    website = 'https://www.mybrand.com'

    def start_requests(self):
        for url in ['https://www.mybrand.com/about', 'https://www.mybrand.com/contact']:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
```

然后在 `scraper/run.py` 的 `ALL_SPIDERS` 中添加 `'mybrand'`。

---

## 💬 WhatsApp / 微信数据获取

这两类数据通常不在企业官网公开，推荐以下方案：

| 方案 | 难度 | 说明 |
|------|------|------|
| **手动补充** | ⭐ | 编辑 `data/clients.manual.json`，管线会自动合并 |
| **B2B 平台** | ⭐⭐ | Alibaba / Global Sources 供应商页常有 WhatsApp 按钮 |
| **第三方 API** | ⭐⭐⭐ | Hunter.io / Apollo.io / Clearbit 企业数据 API |
| **LinkedIn 拓展** | ⭐⭐⭐ | 通过企业页找到采购联系人，获取其联系方式 |
| **展会名录** | ⭐⭐ | Anuga / SIAL / Retail Asia 展会名片收集 |

> 前端对缺失字段显示"待补充"，可通过业务拓展逐步完善。

---

## ⚖️ 合规性

### 已内置的合规措施

- ✅ `ROBOTSTXT_OBEY = True` — 严格遵守 robots.txt
- ✅ `DOWNLOAD_DELAY = 3.0` — 3 秒请求间隔 + AutoThrottle 动态调整
- ✅ User-Agent 轮换 — 降低被识别概率
- ✅ 仅收集公开企业商务信息 — 不涉及个人隐私
- ✅ 并发限制 — 每域名最多 2 并发请求

### 使用须知

1. 抓取前阅读目标网站 Terms of Service
2. 数据仅供内部业务拓展，不得转售
3. 收到企业删除请求时，从 `clients.json` 移除并禁用对应爬虫
4. 欧盟企业数据注意 GDPR，加州注意 CCPA
5. 中国网站注意《网络安全法》《数据安全法》

---

## ❓ FAQ

**Q: 免费 GitHub 账户能用吗？**
A: 可以。公开仓库 + GitHub Pages 完全免费。GitHub Actions 每月 2000 分钟免费额度足够。

**Q: 爬虫被封 IP 怎么办？**
A: 1) 增大 `DOWNLOAD_DELAY`；2) 配置 `PROXY_API_URL` 代理池；3) 减少并发。

**Q: 如何导出 CSV？**
A: 仪表盘右上角点击"导出 CSV"按钮，或用 pandas 转换。

**Q: 数据更新后网站多久生效？**
A: 推送后 1-2 分钟，可在 Actions 页面查看 `pages-build-deployment` 状态。

**Q: 可以部署到私有仓库吗？**
A: GitHub Pages 免费版需公开仓库。私有仓库可升级 Pro，或用 Vercel / Netlify / Cloudflare Pages（均支持私有仓库免费部署）。

---

## 📄 License

仅供学习和内部业务使用。使用者自行承担使用本项目产生的法律责任。
