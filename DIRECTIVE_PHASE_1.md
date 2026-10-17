# 【刚性施工令｜无自由裁量执行工单：Phase 1 本地工程初始化与探针开发】

## 一、唯一物理目标与路径
- **目标**：在 `/Users/a600/project-workspaces(项目工作区)/kais-scraping-apis-benchmark/` 内单次物理闭环完成 Phase 1 全部落地代码与首版产物生成，并通过本地客观工程验收（退出码 0）。
- **物理交付路径**（严格收敛在以下最简文件，严禁新增其他模块或多层目录）：
  1. `requirements.txt`：仅 `requests`
  2. `.gitignore`：包含 `__pycache__/`, `*.pyc`, `.env`, `.venv/` 等
  3. `probe_scraping_apis.py`：单脚本完成公共数据拉取、内置 Baseline 合并、破盾率与延迟指标整理、单价与免费额度换算、Markdown 与 HTML 模板原子生成
  4. `data.json`：由探针自动生成的格式化数据快照（既是公开产物，又是下次降级缓存）
  5. `README.md`：由探针自动生成的高权重 SEO 英文评测仓库正文
  6. `index.html`：由探针自动生成的暗黑极客风格独立单文件 Web 看板

---

## 二、执行硬红线（违反直接判不及格）
1. **架构严禁过度工程**：所有业务逻辑严格在 `probe_scraping_apis.py` 单文件内闭环。严禁新建 `src/`、`adapters/`、`services/` 等抽象层；严禁引入 SQLite、Redis、Celery 或任何常驻后台守护进程。
2. **零等待人工假死锁**：严禁创建任何 `awaiting_human` 标志或等待人工确认的假死锁。脚本执行完成必须 Exit Code 0。
3. **稳健四级降级链**：
   $$\text{实时 API/公共元数据采集} \longrightarrow \text{本地已有 data.json 缓存} \longrightarrow \text{脚本内置 baseline} \longrightarrow \text{标为 N/A}$$
   每个厂商网络请求超时设为 60 秒，任何单家失败在函数内 catch 并降级，绝对禁止中断整体运行。
4. **商业中继桩 1:1 锚定（严禁擅改）**：
   README.md 与 index.html 内的所有产品落地链接，必须严格使用以下解耦中继桩：
   - ZenRows: `https://go.272738.xyz/zenrows`
   - ScrapingBee: `https://go.272738.xyz/scrapingbee`
   - ScraperAPI: `https://go.272738.xyz/scraperapi`
   - Crawlbase: `https://go.272738.xyz/crawlbase`
5. **四大金刚资产互链（统一导航）**：
   在 `index.html`（顶部导航栏与页脚）和 `README.md`（底部矩阵表格）中必须无缝嵌入四大基建互链：
   - Residential Proxies: `https://proxy.mybskm.top`
   - GPU Cloud: `https://gpu.mybskm.top`
   - Global Payments: `https://pay.mybskm.top`
   - Scraping APIs: `https://scrape.mybskm.top` (当前站点)
6. **面向商业客户常识三要素**：
   README.md 与 index.html 必须面向全球 B2B 开发者与商业团队（全英文），直击痛点三要素：【Cloudflare Turnstile / DataDome 封锁与自建爬虫团队月耗 $5000+ 的痛点】+【起步月费、万次请求算例与突破率具体数字】+【直达各厂商免费试用与一键中继出口】。严禁搞学术化置信区间或自贬无意义报告。

---

## 三、四大厂商核心参数与 Baseline 规范（内置于探针脚本）

探针内置 2026 年各主流防爬云 API 的基准参数与官方规格：

| 厂商 | 核心定位与破盾特性 | 破盾成功率 | 平均响应延迟 | 起步月费 / 包含额度 | 1万次高防/JS请求估算成本 | 免费试用额度 | 落地中继链接 |
|---|---|---|---|---|---|---|---|
| **ZenRows** | 顶级 Cloudflare Turnstile, DataDome, Akamai 自动突破，内置高级住宅 IP，自动 CSS/XPath 抽取 | 98.5% | 1.8s | $49/mo (250,000 credits) | ~$1.96 | 5,000 credits (免绑卡试用) | `https://go.272738.xyz/zenrows` |
| **ScrapingBee** | 全功能无头浏览器渲染，智能代理轮换，隐身模式，专精 Instagram / 亚马逊 / 领英 | 97.8% | 2.4s | $49/mo (150,000 credits) | ~$3.26 | 1,000 credits (免绑卡试用) | `https://go.272738.xyz/scrapingbee` |
| **ScraperAPI** | 50M+ 代理池，智能验证码解析，全地域 Geotargeting，支持普通/高防请求按需配置 | 96.5% | 2.1s | $49/mo (100,000 credits) | ~$4.90 | 5,000 credits (7天免费) | `https://go.272738.xyz/scraperapi` |
| **Crawlbase** | 原 ProxyCrawl，AI 结构化抓取，海量爬虫存储，高并发网络爬虫基础设施 | 95.2% | 1.9s | $29/mo (基础请求) | ~$2.90 | 5,000 requests (免费调用) | `https://go.272738.xyz/crawlbase` |

---

## 四、探针脚本 `probe_scraping_apis.py` 必须实现的核心功能

1. **原子写入（Atomic Write）**：
   - 必须使用临时文件写入后通过 `os.replace` 覆盖目标文件，确保 `data.json`、`README.md` 与 `index.html` 写入过程原子化，绝不产生残缺半份文件。
2. **`data.json` 数据规格**：
   - 包含 `schema_version: 1`、`generated_at`（ISO 8601 UTC 时间戳）、`vendors` 数组（各厂商详细规格、基准指标、中继链接、计费阶梯）。
3. **`index.html` 看板设计**：
   - 单文件独立 HTML，采用 Tailwind CSS CDN 或自包含现代 CSS；
   - 现代化暗黑极客主题（Dark Theme），具备科技感与高级感；
   - 顶部与底部带有【四大基建矩阵】导航（Proxies, GPU Cloud, Global Payments, Scraping APIs）；
   - 核心排行榜表格支持实时模糊搜索、按成功率/延迟/价格排序；
   - 每一个厂商卡片与表格行均有清晰的高亮 CTA 按钮直达对应 `go.272738.xyz/<vendor>` 中继。
4. **`README.md` 开源仓库正文**：
   - 全英文，面向 GitHub 高权重 SEO 优化，针对 `best scraping api for cloudflare`, `zenrows vs scrapingbee`, `bypass datadome scraping api`, `scraperapi alternative` 等关键词深度优化；
   - 包含精美 ASCII / 徽标徽章（Badges）；
   - 包含详尽对比表格、各家优缺点分析、代码抓取范例（Python requests / curl）、决策选择流程建议；
   - 底部嵌入 Developer Infrastructure Suite 互链矩阵。

---

## 五、客观工程验收指令
在项目目录执行：
```sh
python3 probe_scraping_apis.py
```
**达标判定标准**：
1. 退出码必须为 0（`$? == 0`）。
2. `requirements.txt`、`.gitignore` 存在且非空。
3. `data.json`、`README.md`、`index.html` 文件大小均 > 2KB。
4. 用 Python 测试解析 `data.json` 格式合法且包含 4 家厂商的完整字段。
5. `index.html` 与 `README.md` 包含所有 4 家厂商的 `go.272738.xyz` 中继，以及 `proxy.mybskm.top`、`gpu.mybskm.top`、`pay.mybskm.top` 互链。

---

## 六、交付动作
立即执行上述所有工程实现，完成代码编写与首次运行验证。验收全部通过后直接正常退出，严禁设立人工等待。
