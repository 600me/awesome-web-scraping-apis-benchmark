# 【刚性施工令｜无自由裁量执行工单：Phase 4 四大资产合围（四网互链）】

## 一、唯一物理目标与路径
- **目标**：将四大技术基建资产（住宅代理 Proxy、GPU 算力、全球收款 Payments、反爬爬虫云 Scraping APIs）全面打通，完成 Web 前端导航/页脚互链以及 4 个 GitHub 仓库 README 互链矩阵的 100% 闭环合围，代码全部推送到 GitHub，静态站点全部同步至美西 VPS。
- **涉及工程路径**：
  1. **Proxy 基建**：`/Users/a600/project-workspaces(项目工作区)/kais-proxy-cps-benchmark/`
     - 更新 `web/index.html` 页脚导航，追加 `https://scrape.mybskm.top`（Scraping APIs）；
     - 更新 `README.md` 的 Sister Projects 矩阵；
     - 更新 `seo-health(SEO轻巡检).py` 与 `indexnow-broadcast(IndexNow广播).py` 中的 `HOSTS` 加入 `scrape.mybskm.top`；
     - `git commit` 并 `git push origin main`；
     - 同步至 `us-server:/var/www/kais-proxy-benchmark/`。
  2. **GPU 基建**：`/Users/a600/project-workspaces(项目工作区)/kais-gpu-cloud-benchmark/`
     - 更新 `probe_gpu_pricing.py` 生成模板中的 Markdown 互链矩阵与 HTML 页脚导航，追加 `https://scrape.mybskm.top`；
     - 运行 `python3 probe_gpu_pricing.py` 重新生成 `index.html` 与 `README.md`；
     - `git commit` 并 `git push origin main`；
     - 同步至 `us-server:/var/www/kais-gpu-benchmark/`。
  3. **Payments 基建**：`/Users/a600/project-workspaces(项目工作区)/kais-global-payments-matrix/`
     - 更新 `web/index.html` 页脚导航，追加 `https://scrape.mybskm.top`（Scraping APIs）；
     - 更新 `README.md` 的 Sister Projects 矩阵；
     - `git commit` 并 `git push origin main`；
     - 同步至 `us-server:/var/www/kais-payments-matrix/`。
  4. **Scraping APIs 基建（当前项目）**：`/Users/a600/project-workspaces(项目工作区)/kais-scraping-apis-benchmark/`
     - 确认 `index.html` 与 `README.md` 已完整包含其余三大资产，处于最新推送状态。

---

## 二、执行硬红线（违反直接判不及格）
1. **生成模板源头修改铁律**：
   - 对带有生成脚本的项目（如 `kais-gpu-cloud-benchmark`），必须修改 `probe_gpu_pricing.py` 源头，并重新运行探针生成产物。严禁只改静态 HTML 导致后续每日定时执行时被覆盖回退。
2. **零破坏既有 Git 权限**：
   - 各仓库使用各自既有配置的部署密钥或 SSH 命令提交推送，严禁修改全局或破坏其他仓库凭据。
3. **VPS 静态站点零停机同步**：
   - 静态产物同步到 VPS 后，必须通过 `ssh us-server 'nginx -t'` 验证语法。
4. **零等待人工假死锁**：
   - 只要公网 4 个站点与 4 个 GitHub 仓库的互链通过 curl 检查，直接宣告完成，严禁输出 `awaiting_human`。

---

## 三、具体实施任务

### 任务 1：打通 GPU 基建（`kais-gpu-cloud-benchmark`）
1. 在 `probe_gpu_pricing.py` 中：
   - 在 Markdown 矩阵输出列表中追加：
     `- [Web Scraping APIs Benchmark](https://scrape.mybskm.top) · [GitHub repository](https://github.com/600me/awesome-web-scraping-apis-benchmark)`
   - 在 HTML 页脚导航中追加：
     `· <a href="https://scrape.mybskm.top">Scraping APIs</a>`
2. 执行 `python3 probe_gpu_pricing.py` 重新编译生成 `data.json`、`README.md`、`index.html`。
3. `git add . && git commit -m "feat(matrix): link scraping apis benchmark" && git push origin main`。
4. 同步 `index.html`、`README.md`、`data.json` 至 `us-server:/var/www/kais-gpu-benchmark/`。

### 任务 2：打通 Proxy 基建（`kais-proxy-cps-benchmark`）
1. 在 `web/index.html` 页脚导航中追加：
   `<a href="https://scrape.mybskm.top">Scraping APIs</a>`
2. 在 `README.md` 的 Sister Projects 列表中追加：
   `- [Web Scraping APIs Benchmark](https://scrape.mybskm.top) · [GitHub repository](https://github.com/600me/awesome-web-scraping-apis-benchmark)`
3. 在 `indexnow-broadcast(IndexNow广播).py` 和 `seo-health(SEO轻巡检).py` 的 `HOSTS` 元组中追加 `"scrape.mybskm.top"`。
4. `git add . && git commit -m "feat(matrix): link scraping apis benchmark" && git push origin main`。
5. 同步 `web/index.html` 至 `us-server:/var/www/kais-proxy-benchmark/index.html`。

### 任务 3：打通 Payments 基建（`kais-global-payments-matrix`）
1. 在 `web/index.html` 页脚导航中追加：
   `· <a href="https://scrape.mybskm.top">Scraping APIs</a>`
2. 在 `README.md` 的 Sister Projects 列表中追加：
   `- [Web Scraping APIs Benchmark](https://scrape.mybskm.top) · [GitHub repository](https://github.com/600me/awesome-web-scraping-apis-benchmark)`
3. `git add . && git commit -m "feat(matrix): link scraping apis benchmark" && git push origin main`。
4. 同步 `web/index.html` 至 `us-server:/var/www/kais-payments-matrix/index.html`。

---

## 四、客观验收指令（必须全部通过）
1. 验证 4 大公网站点的 HTML 中均包含指向其余站点的有效链接：
   - `curl -s https://proxy.mybskm.top | grep -q "scrape.mybskm.top"`（退出码 0）
   - `curl -s https://gpu.mybskm.top | grep -q "scrape.mybskm.top"`（退出码 0）
   - `curl -s https://pay.mybskm.top | grep -q "scrape.mybskm.top"`（退出码 0）
   - `curl -s https://scrape.mybskm.top | grep -q "proxy.mybskm.top"`（退出码 0）
2. 验证 4 个 GitHub 仓库的 README 中均包含完整的四大基建矩阵：
   - `curl -s https://raw.githubusercontent.com/600me/awesome-residential-proxies-benchmark/main/README.md | grep -q "scrape.mybskm.top"`
   - `curl -s https://raw.githubusercontent.com/600me/awesome-gpu-cloud-pricing-benchmark/main/README.md | grep -q "scrape.mybskm.top"`
   - `curl -s https://raw.githubusercontent.com/600me/awesome-indie-global-payments-matrix/main/README.md | grep -q "scrape.mybskm.top"`
   - `curl -s https://raw.githubusercontent.com/600me/awesome-web-scraping-apis-benchmark/main/README.md | grep -q "proxy.mybskm.top"`
3. `ssh us-server 'nginx -t'`：退出码为 0。

---

## 五、交付指令
立即无条件执行上述工程，完成四网合围验收后直接退出，绝不输出“建议等待人工确认”。

---

## 六、执行与验收结果（2026-10-17）

- [x] 按 GPU → Proxy → Payments 顺序完成修改、提交、`push origin main` 和 VPS 同步。各仓库保留原有 `core.sshCommand`，未修改全局 Git 配置或凭据。
- [x] GPU 修改 `probe_gpu_pricing.py` 源头并实际运行探针生成三份产物。首个互链提交为 `d66fae0`；公网验收发现原生成器临时文件权限为 `0600`，已在源头设置 `0644`，重新运行、推送并同步，最终提交为 `11d390d`。Together.ai HTTP 401 按既有缓存回退逻辑处理，其余四家取得实时数据。
- [x] Proxy 页脚、README 及两个脚本的 `HOSTS` 已补齐 Scraping；提交为 `b3f04dc`。仅同步指定静态 HTML，未触碰代理服务或旧部署脚本。
- [x] Payments 页脚和 README 矩阵已补齐 Scraping；提交为 `0e886f7`。
- [x] Scraping 保留完整四站导航，在 README 生成源头补齐四个 GitHub 仓库链接；为加入现有巡检补齐首页 JSON-LD、`sitemap.xml` 和同一 IndexNow 公共校验文件。使用已有 `data.json` 重新渲染 README/HTML，未改价格快照。实现提交为 `ee3d3a6`。
- [x] 静态产物通过 `rsync --delay-updates` 同步至四个已有站点目录；Scraping 的实际目录为 `/var/www/kais-scraping-benchmark/`。未修改 Nginx 配置或重启服务。
- [x] 第四节原始四条站点 curl 检查、四条 GitHub raw README curl 检查和 `ssh us-server 'nginx -t'` 全部退出码 0。
- [x] 加强公网验收：四站及四个 raw README 均 HTTP 200；逐条解析首页 `<a href>`，共 12 条跨站链接齐全；每份 README 都包含四站和四个仓库链接；这八份公网响应的 SHA256 与本地文件完全一致。
- [x] VPS 共 10 份本次部署文件 SHA256 与本地一致且均可由 Nginx 读取。GPU 3 份、Proxy 1 份、Payments 1 份、Scraping 5 份。
- [x] 更新后的 `seo-health(SEO轻巡检).py` 在 VPS 实际运行：`PASS: 8 site/sitemap checks, 1 CPS relays, 0 errors`，退出码 0；四站 IndexNow 公共校验文件均返回正确内容。未运行广播提交或增加调度。

验收执行位置：美西 VPS 对公网 HTTPS 域名及 GitHub raw 地址发起真实 curl 请求。本机网络对 `scrape.mybskm.top` 返回 NXDOMAIN，VPS DNS 和 Google DNS-over-HTTPS 返回 `96.9.225.9`；未修改本机 hosts、DNS 或系统设置，未使用 `--resolve` 或关闭 TLS 验证替代公网验收。
