#!/usr/bin/env python3
"""Collect public metadata and build the Phase 1 comparison, without API keys."""

import copy
import hashlib
import html
import json
import math
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent
TIMEOUT = 60
SUITE = [
    ("Residential Proxies", "https://proxy.mybskm.top"),
    ("GPU Cloud", "https://gpu.mybskm.top"),
    ("Global Payments", "https://pay.mybskm.top"),
    ("Scraping APIs", "https://scrape.mybskm.top"),
]
BASELINES = [
    dict(id="zenrows", name="ZenRows", success_rate_pct=98.5, latency_seconds=1.8,
         monthly_price_usd=49, included_credits=250000, cost_10k_estimate_usd=1.96,
         free_trial_units=5000, free_trial_unit="credits", free_trial_terms="No card required (supplied baseline)",
         positioning="Cloudflare Turnstile, DataDome and Akamai; premium residential IPs and CSS/XPath extraction",
         features=["Automatic anti-bot handling", "JavaScript rendering", "Residential proxies", "CSS/XPath extraction"],
         strengths="A focused shortlist option for difficult anti-bot targets and extraction in one API.",
         limitations="Premium proxies and rendering can multiply credit usage; validate each protected target.",
         pricing_url="https://www.zenrows.com/pricing"),
    dict(id="scrapingbee", name="ScrapingBee", success_rate_pct=97.8, latency_seconds=2.4,
         monthly_price_usd=49, included_credits=150000, cost_10k_estimate_usd=3.26,
         free_trial_units=1000, free_trial_unit="credits", free_trial_terms="No card required (supplied baseline)",
         positioning="Headless browser rendering, rotating proxies and stealth workflows for Instagram, Amazon and LinkedIn",
         features=["Headless browser rendering", "Proxy rotation", "JavaScript scenarios", "Extraction rules"],
         strengths="A useful starting point when browser interaction and JavaScript dominate the workload.",
         limitations="Browser and premium modes need a separate credit budget; social targets require target-level checks.",
         pricing_url="https://www.scrapingbee.com/pricing/"),
    dict(id="scraperapi", name="ScraperAPI", success_rate_pct=96.5, latency_seconds=2.1,
         monthly_price_usd=49, included_credits=100000, cost_10k_estimate_usd=4.90,
         free_trial_units=5000, free_trial_unit="credits", free_trial_terms="7-day trial (supplied baseline)",
         positioning="50M+ proxy pool, CAPTCHA handling and geotargeting with standard and premium request modes",
         features=["Rotating proxy pool", "CAPTCHA handling", "Geotargeting", "Standard and premium modes"],
         strengths="A practical shortlist option for broad proxy-backed collection and familiar HTTP integration.",
         limitations="Country access and premium features depend on the plan; rendering changes request economics.",
         pricing_url="https://www.scraperapi.com/pricing/"),
    dict(id="crawlbase", name="Crawlbase", success_rate_pct=95.2, latency_seconds=1.9,
         monthly_price_usd=29, included_credits=None, cost_10k_estimate_usd=2.90,
         free_trial_units=5000, free_trial_unit="requests", free_trial_terms="Free calls (supplied baseline)",
         positioning="Formerly ProxyCrawl; AI structured scraping, crawler storage and concurrent crawling infrastructure",
         features=["Structured scraping", "Crawler storage", "Concurrent crawling", "JavaScript crawling"],
         strengths="Consider it when collection, storage and crawler operations belong in the same workflow.",
         limitations="The supplied baseline does not specify included paid requests; request-level pricing needs checking.",
         pricing_url="https://crawlbase.com/pricing/"),
]
for _vendor in BASELINES:
    _vendor["relay_url"] = "https://go.272738.xyz/" + _vendor["id"]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class PublicPage(HTMLParser):
    """Extract public text only; scripts and style never become page metadata."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.parts, self.description = [], [], ""
        self.in_title = False
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.in_title:
                self.title.append(data)


def fetch_metadata(vendor):
    """A pricing-page probe is not an authenticated scraping performance test."""
    started = time.monotonic()
    status = None
    try:
        with requests.get(vendor["pricing_url"], timeout=TIMEOUT,
                          headers={"User-Agent": "ScrapingAPIComparison/1.0 (public pricing metadata)",
                                   "Accept": "text/html, text/markdown;q=0.9"}) as response:
            status = response.status_code
            response.raise_for_status()
            parser = PublicPage()
            parser.feed(response.text)
            text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
            if not text or re.search(r"just a moment|verify you are human|access denied", " ".join(parser.title), re.I):
                raise ValueError("Empty page or challenge page")
            excerpts = []
            for match in re.finditer(r"\$\s*\d[\d,.]*", text):
                excerpt = text[max(0, match.start() - 35):match.end() + 65].strip()
                if excerpt not in excerpts:
                    excerpts.append(excerpt)
                if len(excerpts) == 4:
                    break
            return {"ok": True, "checked_at": utc_now(), "http_status": status,
                    "metadata": {"source_url": response.url, "observed_at": utc_now(),
                                 "title": re.sub(r"\s+", " ", " ".join(parser.title)).strip()[:300] or text[:150],
                                 "description": parser.description[:600], "price_excerpts": excerpts,
                                 "content_sha256": hashlib.sha256(response.content).hexdigest(),
                                 "http_status": status,
                                 "page_fetch_seconds": round(time.monotonic() - started, 3)}}
    except Exception as exc:
        # Each vendor fails independently, including transport, HTTP and parse errors.
        return {"ok": False, "checked_at": utc_now(), "http_status": status,
                "error": type(exc).__name__ + ": " + str(exc)[:240]}


def load_cache():
    try:
        data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("vendors"), list):
            return {}
        return {v["id"]: v for v in data["vendors"] if isinstance(v, dict) and isinstance(v.get("id"), str)}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def valid_value(key, value):
    if key in {"success_rate_pct", "latency_seconds", "monthly_price_usd", "included_credits",
               "cost_10k_estimate_usd", "free_trial_units"}:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
        if key in {"included_credits", "free_trial_units"}:
            valid = valid and value > 0 and int(value) == value
        return valid and (key != "success_rate_pct" or value <= 100)
    if key == "features":
        return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v for v in value)
    return isinstance(value, str) and bool(value.strip()) and value != "N/A"


def rounded(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def merge_vendor(baseline, cached, live):
    vendor, sources = {}, {}
    fixed = {"id", "name", "relay_url", "pricing_url"}
    for key, default in baseline.items():
        if key in fixed:
            vendor[key] = default
            continue
        # Public-page metadata supplies no verified performance or normalized plan fields.
        # If a public API later supplies such fields, they take the first slot here.
        candidates = [("live", live.get("fields", {}).get(key)), ("cache", cached.get(key)), ("baseline", default)]
        tier, value = next(((tier, value) for tier, value in candidates if valid_value(key, value)), ("N/A", None))
        vendor[key] = copy.deepcopy(value)
        old_source = cached.get("field_sources", {}).get(key, {}) if isinstance(cached.get("field_sources"), dict) else {}
        sources[key] = {"selected_from": tier,
                        "origin": old_source.get("origin", "unverified_cache") if tier == "cache" and isinstance(old_source, dict)
                        else "directive_baseline" if tier == "baseline" else tier}
    metadata = live.get("metadata") if live["ok"] else cached.get("public_metadata")
    if (not isinstance(metadata, dict) or not isinstance(metadata.get("title"), str)
            or not isinstance(metadata.get("observed_at"), str) or not metadata["observed_at"]):
        metadata = None
    vendor["public_metadata"] = metadata
    vendor["metadata_source"] = "live" if live["ok"] else "cache" if metadata else "N/A"
    vendor["probe"] = {k: v for k, v in live.items() if k != "metadata"}
    vendor["field_sources"] = sources
    vendor["metrics_basis"] = "Supplied Phase 1 baseline; no authenticated target benchmark performed"
    vendor["performance_measured"] = False
    price, credits, trial = vendor["monthly_price_usd"], vendor["included_credits"], vendor["free_trial_units"]
    unit_cost = Decimal(str(price)) / Decimal(str(credits)) if price is not None and credits else None
    vendor["unit_cost_usd"] = float(unit_cost) if unit_cost is not None else None
    vendor["normalized_cost_per_10k_credits_usd"] = rounded(unit_cost * 10000) if unit_cost is not None else None
    vendor["billing_tiers"] = [{"name": "Supplied starting-plan baseline", "monthly_price_usd": price,
                               "included_credits": credits, "currency": "USD", "billing_period": "month",
                               "source": "DIRECTIVE_PHASE_1.md", "verified_current_plan": False}]
    vendor["cost_scenarios"] = [
        {"credits_per_request_assumption": multiplier, "requests": 10000,
         "allocated_cost_usd": rounded(unit_cost * 10000 * multiplier) if unit_cost is not None else None,
         "trial_request_capacity": int(trial // multiplier) if trial and vendor["free_trial_unit"] == "credits" else None}
        for multiplier in (1, 5, 25)
    ]
    vendor["cost_note"] = ("Supplied 10k estimate is retained separately. Normalized costs allocate plan credits, "
                           "not a separately purchasable 10k batch. JS/premium multipliers are illustrative assumptions, "
                           "not verified vendor rates. Crawlbase's paid included volume is unspecified; conversions are N/A.")
    return vendor


def atomic_write(name, content):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=ROOT,
                                         prefix="." + name + ".", suffix=".tmp", delete=False) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, ROOT / name)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def display(value, suffix=""):
    return "N/A" if value is None else f"{value:,}{suffix}"


def money(value):
    return "N/A" if value is None else f"${value:,.2f}"


def render_readme(data):
    rows, analyses, sources, scenarios = [], [], [], []
    for v in data["vendors"]:
        rows.append(f'| [{v["name"]}]({v["relay_url"]}) | {display(v["success_rate_pct"], "%")} | '
                    f'{display(v["latency_seconds"], "s")} | {money(v["monthly_price_usd"])} | '
                    f'{display(v["included_credits"])} | ~{money(v["cost_10k_estimate_usd"])} | '
                    f'{display(v["free_trial_units"])} {v["free_trial_unit"]} | [Start free trial]({v["relay_url"]}) |')
        analyses.append(f'### {v["name"]}\n\n{v["positioning"]}.\n\n'
                        f'**Strengths:** {v["strengths"]}\n\n**Trade-offs:** {v["limitations"]}\n\n'
                        f'**Trial:** {display(v["free_trial_units"])} {v["free_trial_unit"]}; {v["free_trial_terms"]}. '
                        f'[Try {v["name"]} free]({v["relay_url"]}).')
        meta = v["public_metadata"]
        observed = f'last observed {meta["observed_at"]}' if meta else "no successful public-page observation"
        sources.append(f'- [{v["name"]} official pricing source]({v["pricing_url"]}): '
                       f'{v["metadata_source"]}; {observed}. Latest attempt HTTP {v["probe"].get("http_status") or "N/A"}.')
        costs = " | ".join(money(s["allocated_cost_usd"]) for s in v["cost_scenarios"])
        trial = " / ".join(display(s["trial_request_capacity"]) for s in v["cost_scenarios"])
        scenarios.append(f'| {v["name"]} | {costs} | {trial} |')
    repositories = ("awesome-residential-proxies-benchmark", "awesome-gpu-cloud-pricing-benchmark",
                    "awesome-indie-global-payments-matrix", "awesome-web-scraping-apis-benchmark")
    matrix = "\n".join(f"| {name} | [{url}]({url}) | [GitHub repository](https://github.com/600me/{repo}) |"
                       for (name, url), repo in zip(SUITE, repositories))
    return f'''# Best Scraping API for Cloudflare: ZenRows vs ScrapingBee vs ScraperAPI vs Crawlbase

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Providers](https://img.shields.io/badge/providers-4-22c55e)
![Build](https://img.shields.io/badge/build-single_script-8b5cf6)
![Data](https://img.shields.io/badge/metrics-planning_baseline-f59e0b)

```text
  SCRAPING APIs  /  SHIP DATA. SKIP THE PROXY FIREFIGHTING.
  Cloudflare · DataDome · JavaScript · Residential IPs
```

Cloudflare Turnstile and DataDome blocks can interrupt price monitoring, lead research and data pipelines. For a team budgeting **$5,000+ per month** for crawler engineering, proxy maintenance and incident response, a managed API deserves a focused trial. That budget is a planning scenario, not an industry salary survey: 80 engineering hours at $65/hour already totals **$5,200/month**.

Compare the supplied starting-plan baselines of **$29–$49/month**, free-trial allowances, and 10,000-request cost examples below. [Start with ZenRows]({data["vendors"][0]["relay_url"]}) or use the trial links in the comparison to test the pages that matter to your business.

**Snapshot:** {data["generated_at"]}. **All success rates, API response latencies, feature descriptions and plan/trial figures below are the supplied Phase 1 planning baseline. They are not independent measurements or verified current vendor quotes.** The probe refreshes public pricing-page metadata only. Its HTTP status and page-fetch duration do not measure Cloudflare or DataDome bypass performance. Official pricing can differ from this preserved baseline.

## Scraping API comparison: cost, baseline success and free trials

| Provider / trial | Baseline success | Baseline API latency | Baseline monthly | Included credits | Supplied 10k estimate* | Baseline free trial | Action |
|---|---:|---:|---:|---:|---:|---|---|
{chr(10).join(rows)}

*The directive supplies ~$1.96 / ~$3.26 / ~$4.90 / ~$2.90 for 10k high-protection/JS requests. These are retained as **unverified supplied estimates**. They do not establish actual protected-request prices. At one credit per request, $49 / 250,000 × 10,000 = **$1.96**; $49 / 150,000 × 10,000 rounds to **$3.27**, not the supplied $3.26. A 25-credit request makes the first example **$49.00 per 10k**, allocated from the plan. The minimum monthly bill still applies, and taxes/overages are excluded.

## Budget 10,000 JS or protected requests before you buy

Formula: `monthly plan price / included credits × request count × credits per request`.

| Provider | 1 credit/request | 5 credits/request | 25 credits/request | Trial request capacity at 1 / 5 / 25 credits |
|---|---:|---:|---:|---|
{chr(10).join(scenarios)}

The 1/5/25 multipliers are **illustrative budget inputs**, not vendor billing rules. Rendering, premium residential routing, target domain and plan access determine the actual charge. Crawlbase's supplied $29 baseline does not specify included paid requests, so its normalized costs are N/A; its supplied trial is 5,000 requests and is not silently converted into credits. Do not divide a credit trial by one and assume all protected pages cost one credit.

## ZenRows vs ScrapingBee: choose by workload

For **zenrows vs scrapingbee**, begin with the pages that fail today. The supplied ZenRows baseline emphasizes Cloudflare Turnstile, DataDome and Akamai handling; the ScrapingBee baseline emphasizes browser rendering and interaction. Try the same URLs with equivalent proxy and JavaScript settings, then compare usable records and billed credits. A returned challenge page is a failed business result even when its HTTP response is 200.

{chr(10).join(analyses)}

## Best scraping API for Cloudflare and bypass DataDome scraping API workflows

The best scraping API for Cloudflare depends on the target, protection configuration and required output. For a bypass DataDome scraping API shortlist, use the free trials to check product pages, pagination and dynamic fields. Separate HTML delivery from usable structured data; check required fields and block-page markers before accepting a response. The displayed **98.5%, 97.8%, 96.5% and 95.2%** are supplied baseline figures, not target-specific promises.

## Need a ScraperAPI alternative? A practical decision flow

1. **Anti-bot failures dominate:** trial ZenRows first, then compare the same target set elsewhere.
2. **Browser interaction dominates:** trial ScrapingBee with the necessary JavaScript workflow.
3. **Proxy-backed collection dominates:** include ScraperAPI and check plan-specific country support.
4. **Crawling and storage dominate:** evaluate Crawlbase alongside your existing queue and storage.
5. Record usable outputs, end-to-end completion time and billed credits; choose the lowest cost per usable record for your workload.

## Python requests example: get a page through a scraping API

The examples are integration templates, not probe execution logs. Use your own API key and a target you are authorized to collect. Get trial access through the provider links above. Authentication belongs in environment variables.

```python
import os
import requests

response = requests.get(
    "https://api.zenrows.com/v1/",
    params={{"apikey": os.environ["ZENROWS_API_KEY"],
            "url": "https://example.com/", "js_render": "true"}},
    timeout=60,
)
response.raise_for_status()
print(response.text[:500])
```

```sh
curl --get 'https://app.scrapingbee.com/api/v1/' \\
  --max-time 60 \\
  --data-urlencode "api_key=$SCRAPINGBEE_API_KEY" \\
  --data-urlencode 'url=https://example.com/' \\
  --data-urlencode 'render_js=true'
```

## Refresh this comparison locally

```sh
python3 -m pip install -r requirements.txt
python3 probe_scraping_apis.py
```

One script fetches four public pricing pages concurrently with a **60-second timeout per vendor request**. Field selection follows **live data → existing data.json cache → built-in baseline → N/A**. Missing plan/performance measurements stay identified as baseline or N/A. A failed vendor does not interrupt the other three. The script writes `data.json`, `README.md` and `index.html` through same-directory temporary files and `os.replace`. It creates no background jobs and requires no API credentials. The HTML dashboard works as a standalone file with local CSS and JavaScript, search and sorting.

## Public metadata sources

{chr(10).join(sources)}

Fetched price text is preserved in `data.json` as unstructured `price_excerpts`, with original observation timestamps and a content hash. Fetching a page does not validate a pricing interpretation. Cached observations retain their original age. Product CTAs use fixed relay URLs; source links above identify reference material. Relay destinations and affiliate arrangements are not verified by this metadata probe.

## Developer Infrastructure Suite

| Infrastructure | Explore | Repository |
|---|---|---|
{matrix}

Build the smallest stack that fits your workload: proxy access, GPU compute, payments and scraping APIs, connected through one developer infrastructure suite.
'''


def render_html(data):
    escape = html.escape
    navigation = "".join('<a href="' + url + '"' + (' aria-current="page"' if name == "Scraping APIs" else '')
                         + '>' + name + '</a>' for name, url in SUITE)
    rows, cards = [], []
    for rank, v in enumerate(data["vendors"], 1):
        name, relay = escape(v["name"]), v["relay_url"]
        rows.append(f'''<tr data-search="{escape((v['name'] + ' ' + v['positioning'] + ' ' + ' '.join(v['features'])).lower(), quote=True)}" data-success="{v['success_rate_pct'] if v['success_rate_pct'] is not None else ''}" data-latency="{v['latency_seconds'] if v['latency_seconds'] is not None else ''}" data-price="{v['monthly_price_usd'] if v['monthly_price_usd'] is not None else ''}">
<td><span class="rank">0{rank}</span> <strong>{name}</strong></td><td class="green">{display(v['success_rate_pct'], '%')}</td><td>{display(v['latency_seconds'], 's')}</td><td>{money(v['monthly_price_usd'])}<small>/month</small></td><td>~{money(v['cost_10k_estimate_usd'])}<small>supplied estimate</small></td><td>{display(v['free_trial_units'])}<small>{escape(v['free_trial_unit'])}</small></td><td><a class="cta" href="{relay}">Start free trial ↗<span class="sr-only"> — {name}</span></a></td></tr>''')
        costs = " · ".join(money(s["allocated_cost_usd"]) for s in v["cost_scenarios"])
        meta = v["public_metadata"]
        observation = f'Observed {escape(meta["observed_at"])}' if meta else "Public metadata N/A"
        cards.append(f'''<article class="card"><div class="eyebrow">PROVIDER 0{rank} / BASELINE</div><h3>{name}</h3><p>{escape(v['positioning'])}.</p><ul>{''.join('<li>' + escape(feature) + '</li>' for feature in v['features'])}</ul><p><strong>Best fit.</strong> {escape(v['strengths'])}</p><p class="muted"><strong>Budget check.</strong> {escape(v['limitations'])}</p><div class="budget">10k at 1 / 5 / 25 credits:<br><strong>{costs}</strong><small>Illustrative multipliers; allocated plan cost.</small></div><p class="muted">{escape(v['free_trial_terms'])}</p><a class="cta wide" href="{relay}">Try {name} free ↗</a><small class="source"><a href="{v['pricing_url']}">Official pricing reference</a> · {escape(v['metadata_source'])}<br>{observation}</small></article>''')
    return r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Best Scraping API for Cloudflare | ZenRows vs ScrapingBee</title>
<meta name="description" content="Compare ZenRows, ScrapingBee, ScraperAPI and Crawlbase: planning baselines, free trials and 10,000-request budgets for Cloudflare and DataDome workloads.">
<link rel="canonical" href="https://scrape.mybskm.top">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Web Scraping APIs Benchmark","url":"https://scrape.mybskm.top/"}</script>
<style>
:root{color-scheme:dark;--bg:#090c12;--panel:#111722;--line:#263142;--ink:#e9eff9;--muted:#a0afc2;--green:#88f5bd;--blue:#9bbdff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 80% 0,#12353188,transparent 42%),var(--bg);color:var(--ink);font:15px/1.65 system-ui,-apple-system,sans-serif}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--green);outline-offset:4px}.wrap{max-width:1240px;margin:auto;padding:0 28px}header{border-bottom:1px solid var(--line);background:#090c12dd}.top{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:84px}.brand{font:700 17px ui-monospace,monospace;color:var(--ink)}.brand b{color:var(--green)}nav{display:flex;gap:24px;flex-wrap:wrap}nav a{font-size:13px;color:var(--muted)}nav a[aria-current]{color:var(--green)}.hero{padding:78px 0 40px;max-width:900px}.eyebrow{font:12px ui-monospace,monospace;color:var(--green);letter-spacing:1.7px}h1{font-size:clamp(36px,5.5vw,70px);line-height:1.08;letter-spacing:-2.5px;margin:22px 0}h1 span{color:var(--green)}.lead{font-size:18px;color:var(--muted);max-width:760px}.hero .cta{margin:12px 12px 0 0}.cta{display:inline-block;background:var(--green);color:#082318;padding:10px 15px;border-radius:7px;font-size:13px;font-weight:750;white-space:nowrap}.cta:hover{background:#b5ffdb;text-decoration:none}.secondary{background:#202c3c;color:var(--ink)}.signals{display:flex;gap:40px;flex-wrap:wrap;margin:30px 0}.signals strong{display:block;font:600 25px ui-monospace,monospace}.signals span{font-size:12px;color:var(--muted)}.notice{padding:18px 22px;border:1px solid #796239;border-radius:10px;background:#dba6430b;color:#e1c991;font-size:13px}.section-title{display:flex;justify-content:space-between;align-items:end;gap:24px;margin:44px 0 20px}h2{margin:0;font-size:25px;letter-spacing:-.7px}.muted,small{color:var(--muted)}small{display:block;font-size:11px}.controls{display:flex;gap:14px;flex-wrap:wrap;margin:20px 0}.controls label{font-size:12px;color:var(--muted)}input,select{display:block;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:12px 14px;min-width:215px;margin-top:5px}input{min-width:320px}.table-shell{position:relative;overflow-x:auto;border:1px solid var(--line);border-radius:12px}table{border-collapse:collapse;width:100%;white-space:nowrap;text-align:left}th{font:11px ui-monospace,monospace;text-transform:uppercase;color:var(--muted);background:#131c28;letter-spacing:.7px}th,td{padding:22px 18px;border-bottom:1px solid var(--line)}tbody tr:last-child td{border-bottom:0}tbody tr:hover{background:#88f5bd05}.rank{font:12px ui-monospace,monospace;color:#7e8c9e;margin-right:10px}.green{color:var(--green);font-family:ui-monospace,monospace}.table-note{color:var(--muted);font-size:12px;margin:14px 0}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin:22px 0 50px}.card{padding:28px;background:linear-gradient(130deg,#14202c,#10151e);border:1px solid var(--line);border-radius:12px}h3{font-size:26px;margin:14px 0 10px}.card p{color:#b6c3d4;font-size:14px}.card li{color:#c7d4e5;font-size:13px;margin:5px 0}.card ul{padding-left:18px}.budget{padding:14px;border:1px solid var(--line);border-radius:7px;font-size:12px;margin-top:20px}.budget strong{font:600 17px/2 ui-monospace,monospace}.wide{display:block;text-align:center}.source{margin-top:14px}.playbook{padding:28px;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:28px 0 56px}.playbook p,.playbook li{color:var(--muted)}.playbook code{color:var(--green)}footer{border-top:1px solid var(--line);padding:32px 0 40px}footer .wrap{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap}footer small{margin-top:10px}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}#empty{padding:20px;color:var(--muted)}.skip{position:absolute;left:-9999px}.skip:focus{left:20px;top:10px;z-index:3;background:var(--bg);padding:10px}@media(max-width:720px){.wrap{padding:0 18px}.top{align-items:start;flex-direction:column;padding-top:20px;padding-bottom:20px;gap:12px}nav{gap:12px}.hero{padding-top:45px}h1{letter-spacing:-1.4px}.cards{grid-template-columns:1fr}.section-title{align-items:start;flex-direction:column;gap:8px}input{min-width:0;width:100%}.controls label{flex:1;min-width:200px}.signals{gap:24px}th,td{padding:18px 14px}.card{padding:22px}}
</style></head><body><a class="skip" href="#main">Skip to comparison</a>
<header><div class="wrap top"><a class="brand" href="https://scrape.mybskm.top"><b>▧</b> SCRAPE / STACK</a><nav aria-label="Developer infrastructure">__NAV__</nav></div></header>
<main id="main" class="wrap"><section class="hero"><div class="eyebrow">THE DEVELOPER INFRASTRUCTURE SUITE / 04</div><h1>Ship the data.<br><span>Skip the anti-bot firefight.</span></h1><p class="lead">Cloudflare Turnstile. DataDome. Another broken price feed. If your team budgets <strong>$5,000+ a month</strong> to maintain crawlers, compare managed scraping APIs before the next rebuild.</p><p class="muted">A concrete scenario: 80 engineering hours × $65/hour = $5,200/month. Start with a free trial and price the pages your pipeline actually needs.</p><a class="cta" href="https://go.272738.xyz/zenrows">Explore ZenRows free trial ↗</a><a class="cta secondary" href="#comparison">Compare all four ↓</a><div class="signals"><div><strong>04</strong><span>PROVIDERS COMPARED</span></div><div><strong>$29–49</strong><span>BASELINE STARTING MONTHLY</span></div><div><strong>10,000</strong><span>REQUEST BUDGET EXAMPLES</span></div></div></section>
<aside class="notice"><strong>Phase 1 planning baseline.</strong> Success rates, API latencies, features, prices and trial allowances are supplied baseline values, not authenticated target measurements or verified current quotes. Public pricing-page metadata is refreshed separately. HTTP 200 is not proof of bypass success. Snapshot: __DATE__.</aside>
<section id="comparison"><div class="section-title"><div><div class="eyebrow">COMPARE / SELECT / BUILD</div><h2>Find your scraping API.</h2></div><span class="muted" id="count" aria-live="polite">4 providers</span></div><div class="controls"><label for="search">Search providers and capabilities<input id="search" type="search" placeholder="Try clodflare, browser, storage…" autocomplete="off"></label><label for="sort">Sort baseline comparison<select id="sort"><option value="success">Success rate: high to low</option><option value="latency">Latency: low to high</option><option value="price">Monthly price: low to high</option></select></label></div><div class="table-shell"><table><caption class="sr-only">Four scraping API providers with supplied planning baseline metrics and free trial links</caption><thead><tr><th scope="col">Provider</th><th scope="col">Success*</th><th scope="col">API latency*</th><th scope="col">Plan*</th><th scope="col">10k estimate*</th><th scope="col">Free trial*</th><th scope="col">Get started</th></tr></thead><tbody id="vendors">__ROWS__</tbody></table><p id="empty" hidden>No matching providers. Try a shorter search.</p></div><p class="table-note">*Supplied baseline, not live benchmark results. 10k protected/JS estimates are unverified. Actual premium and rendering credit multipliers can raise costs; minimum plan billing applies. $49 / 150,000 × 10,000 rounds to $3.27; the supplied ScrapingBee estimate is preserved as $3.26.</p><noscript><p>All provider information and trial links are available below. Enable JavaScript for search and sorting.</p></noscript></section>
<section aria-labelledby="providers-heading"><div class="section-title"><h2 id="providers-heading">Choose the fit. Test your targets.</h2></div><div class="cards">__CARDS__</div></section>
<section class="playbook"><div class="eyebrow">A PRACTICAL BUYING GUIDE</div><h2>ZenRows vs ScrapingBee. Or a ScraperAPI alternative?</h2><p>The best scraping API for Cloudflare depends on usable records, target coverage and cost. For a bypass DataDome scraping API workflow, test identical URLs and required fields across trials.</p><ol><li>Shortlist ZenRows for difficult anti-bot targets and ScrapingBee for browser interaction.</li><li>Compare ScraperAPI for proxy-backed collection and Crawlbase for crawling plus storage.</li><li>Budget with <code>plan price ÷ credits × requests × credits/request</code>. At $49 per 250k credits, 10k one-credit requests allocate $1.96; at 25 credits each, they allocate $49.</li><li>Check the actual billed credits and usable output before choosing a plan. The displayed 98.5%, 97.8%, 96.5% and 95.2% are baseline inputs.</li></ol><p>The cards use illustrative 1 / 5 / 25 credit multipliers, not verified vendor rates. Crawlbase's included paid volume is unspecified, so normalized prices are N/A. Free-trial access and eligibility are subject to current vendor terms.</p><a href="data.json">Download the data snapshot ↗</a> · <a href="README.md">Read the comparison and Python / curl examples ↗</a></section></main>
<footer><div class="wrap"><div><span class="brand">DEVELOPER INFRASTRUCTURE SUITE</span><small>Public metadata + explicit planning baselines. Relay destinations are not tested by this probe.</small></div><nav aria-label="Footer infrastructure">__NAV__</nav></div></footer>
<script>
const body=document.getElementById('vendors'),rows=Array.from(body.rows),search=document.getElementById('search'),sort=document.getElementById('sort');
function distance(a,b){let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){let next=[i];for(let j=1;j<=b.length;j++)next[j]=Math.min(next[j-1]+1,row[j]+1,row[j-1]+(a[i-1]===b[j-1]?0:1));row=next}return row[b.length]}
function matches(text,query){return query.split(/\s+/).every(term=>text.includes(term)||(term.length>3&&text.split(/[^a-z0-9]+/).some(word=>Math.abs(word.length-term.length)<=1&&distance(word,term)<=1)))}
function update(){const query=search.value.toLowerCase().trim().slice(0,160),key=sort.value;rows.sort((a,b)=>{const x=a.dataset[key]===''?null:Number(a.dataset[key]),y=b.dataset[key]===''?null:Number(b.dataset[key]);return x===null?(y===null?0:1):y===null?-1:key==='success'?y-x:x-y});let shown=0;for(const row of rows){row.hidden=!matches(row.dataset.search,query);if(!row.hidden)shown++;body.appendChild(row)}document.getElementById('count').textContent=shown+' provider'+(shown===1?'':'s');document.getElementById('empty').hidden=shown!==0}
search.addEventListener('input',update);sort.addEventListener('change',update);update();
</script></body></html>
'''.replace("__NAV__", navigation).replace("__DATE__", escape(data["generated_at"])).replace("__ROWS__", "\n".join(rows)).replace("__CARDS__", "\n".join(cards))


def main():
    cache = load_cache()
    with ThreadPoolExecutor(max_workers=4) as pool:
        observations = list(pool.map(fetch_metadata, BASELINES))
    data = {"schema_version": 1, "generated_at": utc_now(), "currency": "USD",
            "methodology": {"fallback_order": ["live", "cache", "baseline", "N/A"],
                            "request_timeout_seconds": TIMEOUT, "live_collection": "Public pricing-page metadata only",
                            "performance_tested": False, "baseline_source": "DIRECTIVE_PHASE_1.md",
                            "baseline_year_label": 2026, "cost_scenario_multipliers": [1, 5, 25]},
            "infrastructure_suite": [{"name": name, "url": url} for name, url in SUITE],
            "vendors": [merge_vendor(v, cache.get(v["id"], {}), observation)
                        for v, observation in zip(BASELINES, observations)]}
    # Render everything before replacing any output; each replacement is atomic.
    outputs = {"data.json": json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
               "README.md": render_readme(data), "index.html": render_html(data)}
    for filename, content in outputs.items():
        atomic_write(filename, content)
    for vendor in data["vendors"]:
        print(f'{vendor["name"]}: metadata={vendor["metadata_source"]}; '
              f'HTTP={vendor["probe"].get("http_status") or "N/A"}; performance=baseline')
    print("Generated data.json, README.md and index.html (4 vendors).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
