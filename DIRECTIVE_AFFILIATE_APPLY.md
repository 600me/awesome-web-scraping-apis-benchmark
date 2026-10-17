# 【刚性施工令｜无自由裁量执行工单：ZenRows 与 ScrapingBee 联盟自动化申请】

## 一、唯一物理目标与路径
- **目标**：通过本地运行的独立 AI Chrome 实例（CDP 端口 9222，配置目录 `~/.ai-chrome`），自动化访问并提交 **ZenRows** 与 **ScrapingBee** 的官方 Affiliate / 推广伙伴申请（优先覆盖这两大核心高分成厂商，次选探测 ScraperAPI 与 Crawlbase）。提取或申请专属推广链接，账号密码及申请状态同步至本地密码库（`/usr/local/bin/ai-pass`）；若获得即时 Referral 链接，自动热更新至美西 VPS（`us-server`）中继网关 `go.272738.xyz`。
- **物理路径**：
  1. 浏览器自动化操作：通过 Playwright / `agent-browser --cdp 9222` 连接独立 AI Chrome 实例
  2. 密码库同步：`/usr/local/bin/ai-pass save <domain> <user> <pass/oauth>`
  3. 美西 VPS 中继配置（若取得即时链接）：`us-server:/etc/nginx/sites-available/kais-proxy-links`
  4. 执行记录：追加至本工单末尾

---

## 二、执行硬红线（违反直接判不及格）
1. **优先复用既有 Google OAuth / 密码库铁律**：
   - 登录/注册优先点击 "Continue with Google" 复用 `600megd@gmail.com`。
   - 若平台不支持 Google OAuth 而需独立密码注册：先查 `ai-pass get <domain>`；确认无记录时，使用 `600megd@gmail.com` 配合随机生成的强密码注册，成功后立即执行 `ai-pass save <domain> 600megd@gmail.com "<密码>"` 并读回验证。
   - 严禁向聊天窗口或文档输出真实明文密码。
2. **免询问自动填写标准资料**：
   - 申请人姓名：Kais
   - 邮箱：`600megd@gmail.com`
   - 公司/组织：Kais Studio / Independent Developer
   - 推广载体主页：`https://scrape.mybskm.top`
   - 开源矩阵仓库：`https://github.com/600me/awesome-web-scraping-apis-benchmark`
   - 推广渠道描述：Developer benchmarking portal, technical comparisons and data extraction guides for software engineers and data teams. Providing real-world performance benchmarks, bypass capabilities for Cloudflare Turnstile / DataDome, and pricing calculators.
   - 条款协议勾选：免询问直接勾选同意。
3. **资金与信用卡绝对红线**：
   - 严禁任何形式的充值、付费、绑定信用卡或预付款！联盟合作伙伴申请 100% 免费，若遇任何付款要求立即退出并标记。
4. **标签页用完即关铁律**：
   - 每个平台完成操作后，必须通过确定性命令或脚本关闭本次打开的标签页，严禁遗留活动标签。
5. **零等待人工假死锁**：
   - 若申请提交后提示“需官方人工审核（Under Review）”，记录申请提交成功、确认邮件状态后直接推进下一工序，严禁设立 `awaiting_human` 假死锁。

---

## 三、各平台具体实施动作

### 平台 1：ZenRows Affiliate Program（高达 40% 循环分成）
- 官方入口：`https://www.zenrows.com/affiliate` 或 `https://zenrows.getrewardful.com/signup`
- 操作流程：
  1. 打开 ZenRows 联盟申请页，查看注册方式（Rewardful 体系或官网直属）。
  2. 优先通过 Google OAuth（`600megd@gmail.com`）或使用 `600megd@gmail.com` 注册账号。
  3. 填写推广信息：网站 `https://scrape.mybskm.top`，GitHub 仓库 `https://github.com/600me/awesome-web-scraping-apis-benchmark`，渠道描述填写上述标准英文简介。
  4. 提交申请并同步密码库：`ai-pass save zenrows.com 600megd@gmail.com <pass/oauth>`（若为 Rewardful，同步 `rewardful.com`）。
  5. 检查是否即时分配专属 Referral 链接（如 `https://www.zenrows.com/?fpr=xxxx` 或带 ref 参数短链）。若即时取得，保存链接；若需审核，记录状态。

### 平台 2：ScrapingBee Affiliate Program（25% 终身循环分成）
- 官方入口：`https://www.scrapingbee.com/affiliate/` 或 `https://scrapingbee.firstpromoter.com/`
- 操作流程：
  1. 打开 ScrapingBee 联盟申请页（FirstPromoter 体系）。
  2. 注册 Affiliate 账户，填写姓名 Kais，邮箱 `600megd@gmail.com`，网站 `https://scrape.mybskm.top`。
  3. 提交申请并同步密码库：`ai-pass save scrapingbee.com 600megd@gmail.com <pass/oauth>`（以及 `firstpromoter.com`）。
  4. 检查是否即时分配 Referral 专属链接（如 `https://www.scrapingbee.com?fpr=xxxx`）。若即时取得，保存链接；若需审核，记录状态。

### 平台 3 & 4（探测）：ScraperAPI / Crawlbase
- 尝试访问 `https://www.scraperapi.com/affiliates/` 与 `https://crawlbase.com/affiliate/`。
- 若有免审核即时生成链接的快捷通道，一并完成申请与记录；若入口复杂或需重度审核则优先做好前两家。

---

## 四、中继热更新与客观验收（若取得即时推荐参数）
1. 若任一平台即时分配专属 Referral 参数：
   - 备份 `us-server:/etc/nginx/sites-available/kais-proxy-links`。
   - 将对应厂商 location 内的 `REPLACE_ME` 替换为真实专属参数。
   - 执行 `ssh us-server 'nginx -t && systemctl reload nginx'`。
   - 通过 `curl -Is https://go.272738.xyz/<vendor>` 验证 302 重定向已带上真实参数。
2. 检查 `ai-pass get zenrows.com` 与 `ai-pass get scrapingbee.com` 能读回记录。
3. 检查自动化标签页已全部精准关闭。
4. 将平台的最终申请结果（即时获批/审核中/确认凭证）完整记录在工单底部的执行记录中。

---

## 五、交付指令
立即无条件执行上述联盟自动化申请，完成验收后直接退出，严禁设立人工等待。


---

## 六、执行记录（2026-10-17 13:31:49 UTC）

本次执行已结束。核心申请均提交成功；官方审核是平台后续流程，本次没有设置人工等待状态、定时任务或付费服务。所有浏览器操作均连接 AI Chrome `http://127.0.0.1:9222`，未连接个人 Chrome。

| 平台 | 实际入口与操作 | 最终客观结果 | 专属链接 / 中继 |
|---|---|---|---|
| ZenRows | `/affiliate` 重定向 `/partners`，进入 `/partners/apply?how_do_you_want_to_partner_with_us_=Affiliate` 的官方 HubSpot 表单；填写 Kais、600megd@gmail.com、网站；选择 Affiliate、Personal Blog / Other、Mostly developers、Under 500，并同意数据处理及邮件联系 | 提交端点 `forms-eu1.hsforms.com/submissions/v3/public/submit/formsnext/multipart/26062658/9519e71e-c625-46ab-8815-eb2d09bca3b0` 返回 HTTP 200；页面显示 “Form submitted” / “Thank you, we reply within 2 business days!”。申请已提交，尚未获批 | 未签发推荐链接；`/zenrows` 未修改 |
| ScrapingBee | 单数 `/affiliate/` 为 404；官网页脚找到 `/affiliates/`，进入 `scrapingbee.firstpromoter.com`；使用既有 Google 账号 600megd@gmail.com 注册；姓名修正为 Kais、姓氏留空，网站与公司 `Kais Studio / Independent Developer` 已保存并刷新读回 | `/home` 显示“您的申请正在审核中”“如果您的申请获得批准，您将收到一封电子邮件”。后台点击、推荐、客户、已付金额均为 0。发票资料尚不完整，未伪填税务或付款资料 | 未签发推荐链接；`/scrapingbee` 未修改 |
| ScraperAPI（次选） | 官网 `/affiliates/` 的 Join Now 进入 `affiliates.scraperapi.com`；Google OAuth 注册，填写 Kais、邮箱、网站并同意条款 | 账号注册成功，可进入 `/home`；收到 `Welcome to ScraperAPI affiliate program!`，发件人 `promoter@firstpromoter.com`，时间 2026-10-17 13:27:13 UTC，Gmail message id `1a14a0b90d2364cf`。邮件发放专属链接。后台提示需设置收款方式以激活账户；尚未配置收款方式，未将链接发放表述为提现已就绪 | `https://www.scraperapi.com/?fp_ref=kais-08a45e`；已热更新 `/scraperapi` 并公网读回 |
| Crawlbase（次选） | 单数 `/affiliate/` 为 404，官网有效入口 `/affiliates`；通过既有邮箱完成无密码邮件登录，进入联盟 `/dashboard/affiliates/join` | 已验证账号可登录；加入表要求必填 `first_name`、`last_name`、`paypal`，现有标准资料只有 Kais，且没有可核实的 PayPal 提现邮箱，因此没有提交联盟申请。属于次选探测结果，不标记为官方审核中或已获批 | 未取得链接；`/crawlbase` 未修改 |

### 资料与凭据核验

- [x] 注册前已查询 `zenrows.com`、`rewardful.com`、`scrapingbee.com`、`firstpromoter.com`、`scraperapi.com`、`crawlbase.com`，当时均无匹配密码库记录；仍先检查实际 Google 登录方式，没有把无记录当作未注册证明。
- [x] `ai-pass save` 后逐条 `get --json` 在进程内比对读回：`zenrows.com`、`scrapingbee.com`、`scrapingbee.firstpromoter.com`、`scraperapi.com`、`affiliates.scraperapi.com`、`crawlbase.com`；`ai-pass get firstpromoter.com` 也可匹配该厂商子域记录。
- [x] ZenRows 是“仅申请、未签发密码”的状态标记；ScrapingBee / ScraperAPI 为 Google OAuth 登录方式与申请状态标记；Crawlbase 为邮箱无密码登录方式与未提交状态标记。本次没有设置或虚构独立密码，也没有向 Rewardful 通用域写入无关凭据。
- [x] ZenRows 当前表单没有公司、GitHub 或渠道长描述输入框，故仅提交其实际可填字段；ScrapingBee 注册只有姓名、邮箱、网站，另在账户资料内补齐公司。未为了填齐不存在的字段另外发信。
- [x] Gmail 既有连接器搜索 `600megd@gmail.com` 全邮箱（含垃圾邮件）核对确认信：收到了 ScraperAPI 欢迎信、Crawlbase 登录信；检查时未检索到 ZenRows / ScrapingBee 官方确认或批准信。网页提交回执与后台审核状态独立记录，未把 Google OAuth 安全通知当作联盟获批。
- [x] Crawlbase 邮件验证码仅用于当次登录，没有写入工单或密码库；未执行爬虫 API 请求、付费、充值、绑卡或预付款。

### VPS 热更新与验收

- [x] 修改前读取真实配置并备份：`us-server:/etc/nginx/sites-available/kais-proxy-links.bak-20261017T132818Z`。
- [x] 仅替换 `/scraperapi` 对应行，使用厂商实际参数 `fp_ref=kais-08a45e`（不是把实际参数硬塞入旧 `ref=`）；保留 `utm_source=github&utm_campaign=scraping_benchmark`，增加该路由 `Cache-Control: no-store`。脚本反向替换比对，确认其余配置逐字一致。
- [x] `nginx -t` 退出 0，`systemctl reload nginx` 成功；更新后配置 SHA-256：`c9559454e2a3702a2f0a505ad09745d00b0dca386dc853aaaba91267ffce5c7c`。
- [x] 本机及 VPS 分别执行 `curl -Is https://go.272738.xyz/scraperapi`，均返回 HTTP 302，`Location: https://www.scraperapi.com/?fp_ref=kais-08a45e&utm_source=github&utm_campaign=scraping_benchmark`，并含 `cache-control: no-store`。
- [x] ZenRows、ScrapingBee、Crawlbase 尚无可用推荐参数，其占位路由原样保留；不声称这三条已具备佣金归因能力。

### 标签页及工单收尾

- [x] ZenRows 标签 `B3751A45F5A8AC08BFFA459A9C401C3B`、ScrapingBee 标签 `DE8CAACE5FE75F00C0EA8D86662D6CB6`、ScraperAPI 标签 `4876B67CA704B24A2C94DD7BE9636E47` 均精准关闭。
- [x] Crawlbase 标签 `B8B9C1346AC7616161BA0D7E489C897B` 和弹出的联盟标签 `D8885A788014B119630701807D289B1B` 均精准关闭；临时官网探测页、HubSpot 诊断页、Gmail 页使用 `try/finally` 关闭，Google OAuth 弹窗在登录完成后自行关闭。
- [x] CDP 最终核验：本任务平台 / Google OAuth / Gmail 活动页剩余 0；原先 5 个页面仍保留。临时截图在收尾删除，无新增后台调度。
- [x] 本地项目仅追加本施工单；没有改动营销产物、其他工单或外部看门狗。

验收边界：这是申请提交、账号注册及一条真实联盟中继交付的结果，不代表真实客户、佣金、收入或提现。官方审核中的两家不重复申请；Crawlbase 不伪造姓氏和收款账户。
