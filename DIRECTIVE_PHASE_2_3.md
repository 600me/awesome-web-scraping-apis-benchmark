# 【刚性施工令｜无自由裁量执行工单：Phase 2 & Phase 3 全网部署与中继联动】

## 一、唯一物理目标与路径
- **目标**：将《反爬爬虫云 API 基建评测与决策中继》（`kais-scraping-apis-benchmark`）完成全网发布、域名点亮与中继路由扩充，包括：
  1. 生成独立部署密钥并在 GitHub（`600me`）创建开源公开仓库 `awesome-web-scraping-apis-benchmark`，关联远端并完成首次 `git push`；
  2. 编写轻量 GitHub Actions 自动化定时工作流 `.github/workflows/daily-benchmark.yml`；
  3. 为 `mybskm.top` 添加 DNS A 记录：`scrape` ➔ `96.9.225.9`（DNS-only / 灰云）；
  4. 在美西 VPS（`us-server`）初始化 `/var/www/kais-scraping-benchmark` 并同步静态产物，配置 Nginx 虚拟主机 `scrape.mybskm.top`；
  5. 在美西 VPS 执行非交互 Certbot 申请并配置 Let's Encrypt SSL 证书，全网点亮 `https://scrape.mybskm.top`（HTTP 200）；
  6. 在美西 VPS `go.272738.xyz` 扩充 4 大爬虫云中继路由桩（`zenrows`, `scrapingbee`, `scraperapi`, `crawlbase`），测试 `nginx -t` 并平滑 reload。
- **物理交付路径**：
  - 本地项目：`/Users/a600/project-workspaces(项目工作区)/kais-scraping-apis-benchmark/`
  - GitHub 远端：`git@github.com:600me/awesome-web-scraping-apis-benchmark.git`
  - GitHub Actions：`.github/workflows/daily-benchmark.yml`
  - 美西 VPS 站点目录：`us-server:/var/www/kais-scraping-benchmark/`
  - 美西 VPS Nginx 虚拟主机：`us-server:/etc/nginx/sites-available/kais-scraping-benchmark`
  - 美西 VPS 中继配置：`us-server:/etc/nginx/sites-available/kais-proxy-links`

---

## 二、执行硬红线（违反直接判不及格）
1. **平滑扩充与既有资产零破坏**：
   - 修改 `/etc/nginx/sites-available/kais-proxy-links` 前必须创建带时间戳的备份文件。
   - 只能在 `server_name go.272738.xyz;` 块内追加 4 个 location，严禁破坏既有的 Smartproxy, Bright Data, Apify, Oxylabs, RunPod, Vast.ai, Together, OpenRouter, DeepInfra, Doola, Firstbase, LemonSqueezy, Paddle, Wise 等中继！
   - 修改后必须 `ssh us-server 'nginx -t'` 验证通过方可 `systemctl reload nginx`。
2. **Certbot 自动化非交互**：
   - 必须使用标准非交互命令：
     `certbot --nginx -d scrape.mybskm.top --non-interactive --agree-tos -m 600megd@gmail.com --redirect`
   - 严禁出现交互式输入挂起。
3. **GitHub 独立部署公钥**：
   - GitHub 限制同一公钥不能用于多个仓库的 Deploy Key。必须生成独立的 `~/.ssh/id_ed25519_scraping_benchmark`，在仓库配置读写权限部署密钥，并在本地仓库配置：
     `git config core.sshCommand "ssh -i ~/.ssh/id_ed25519_scraping_benchmark -F /dev/null"`
   - 保证 `git push -u origin main` 顺畅成功。
4. **零等待人工假死锁**：
   - 只要客观指标（公网 HTTPS 200、curl 302 成功、git push 成功、Nginx 语法测试通过）全绿，直接宣告完成，严禁输出 `awaiting_human`。

---

## 三、具体实施任务

### 任务 1：编写 `.github/workflows/daily-benchmark.yml`
在本地工程创建 `.github/workflows/daily-benchmark.yml`：
- 定时调度：`cron: '47 13 * * *'`（每日一次 UTC 13:47，对应美东上午流量高峰）及 `workflow_dispatch` 手动触发；
- 步骤：
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` (Python 3.11)
  3. `pip install -r requirements.txt`
  4. `python3 probe_scraping_apis.py`
  5. 检查 `data.json`、`README.md`、`index.html` 是否有变更，若有则使用 `github-actions[bot]` 自动 commit 并 push。

### 任务 2：添加 Cloudflare DNS A 记录
- 为 `mybskm.top` 添加 A 记录：`scrape` ➔ `96.9.225.9` (DNS-only / 灰云，TTL 60 或自动)。
- 验证解析：`dig +short scrape.mybskm.top @8.8.8.8` 返回 `96.9.225.9`。

### 任务 3：美西 VPS 部署站点与配置 HTTPS
- SSH 到 `us-server`：
  - 创建目录 `/var/www/kais-scraping-benchmark`；
  - 同步本地 `index.html`、`data.json`、`README.md` 到 `/var/www/kais-scraping-benchmark/`；
  - 写入 `/etc/nginx/sites-available/kais-scraping-benchmark`：
    ```nginx
    server {
        server_name scrape.mybskm.top;
        root /var/www/kais-scraping-benchmark;
        index index.html;
        charset utf-8;
        add_header X-Content-Type-Options nosniff always;
        location / { try_files $uri $uri/ =404; }
        listen 80;
    }
    ```
  - 软链到 `/etc/nginx/sites-enabled/`，运行 `nginx -t` 并 `systemctl reload nginx`；
  - 运行非交互 Certbot：
    `certbot --nginx -d scrape.mybskm.top --non-interactive --agree-tos -m 600megd@gmail.com --redirect`
  - 验证 `nginx -t` 并 `systemctl reload nginx`。

### 任务 4：美西 VPS `go.272738.xyz` 扩充 4 大爬虫云中继
- 备份 `/etc/nginx/sites-available/kais-proxy-links`；
- 在 `server_name go.272738.xyz;` 443 块内追加：
  ```nginx
    location = /zenrows { return 302 "https://www.zenrows.com/?ref=REPLACE_ME&utm_source=github&utm_campaign=scraping_benchmark"; }
    location = /scrapingbee { return 302 "https://www.scrapingbee.com/?ref=REPLACE_ME&utm_source=github&utm_campaign=scraping_benchmark"; }
    location = /scraperapi { return 302 "https://www.scraperapi.com/?ref=REPLACE_ME&utm_source=github&utm_campaign=scraping_benchmark"; }
    location = /crawlbase { return 302 "https://crawlbase.com/?ref=REPLACE_ME&utm_source=github&utm_campaign=scraping_benchmark"; }
  ```
- 执行 `nginx -t && systemctl reload nginx`。

### 任务 5：GitHub 仓库关联与远端推送
- 生成 `~/.ssh/id_ed25519_scraping_benchmark`；
- 在 GitHub `600me` 账户下创建公开仓库 `awesome-web-scraping-apis-benchmark`；
- 添加 Deploy Key（Allow write access）；
- 配置本地 git 仓库 remote origin 并 push `main` 分支。

---

## 四、客观验收指令（必须全部通过）
1. `ssh us-server 'nginx -t'`：退出码为 0。
2. `dig +short scrape.mybskm.top @8.8.8.8`：返回 `96.9.225.9`。
3. `curl -Is https://scrape.mybskm.top | grep -E "HTTP/|location:"`：返回 `HTTP/2 200` 或 `HTTP/1.1 200`。
4. 验证 4 大爬虫云中继跳转：
   - `curl -Is https://go.272738.xyz/zenrows | grep -E "HTTP/|location:"` 返回 302 且指向 zenrows.com
   - `curl -Is https://go.272738.xyz/scrapingbee | grep -E "HTTP/|location:"` 返回 302 且指向 scrapingbee.com
   - `curl -Is https://go.272738.xyz/scraperapi | grep -E "HTTP/|location:"` 返回 302 且指向 scraperapi.com
   - `curl -Is https://go.272738.xyz/crawlbase | grep -E "HTTP/|location:"` 返回 302 且指向 crawlbase.com
5. 验证既有中继不受影响：
   - `curl -Is https://go.272738.xyz/runpod` 返回 302
   - `curl -Is https://go.272738.xyz/firstbase` 返回 302
6. `curl -Is https://github.com/600me/awesome-web-scraping-apis-benchmark | head -n 5`：返回 HTTP 200。

---

## 五、交付指令
立即无条件执行上述全部动作，完成验收后退出，严禁设立人工等待。
