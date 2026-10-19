---
license: mit
task_categories:
  - tabular-classification
language:
  - en
tags:
  - web-scraping
  - anti-bot
  - cloudflare
  - scraperapi
  - zenrows
  - bright-data
  - tco
  - cost-engineering
  - benchmark
  - rag
size_categories:
  - n<1K
pretty_name: "Web Scraping & Anti-Bot API True TCO Benchmark (2026)"
---

# Web Scraping & Anti-Bot API True TCO Benchmark (2026)

Managed scraping APIs quote credits per request. Your pipeline is paid in **clean pages**. This dataset
converts credit multipliers, JS rendering surcharges and the retry amplification caused by blocked
attempts into one comparable number: **USD per 1,000 clean pages**.

## Files

| File | Rows | Description |
|---|---|---|
| `data/scraping_api_tco_2026.csv` | 14 | One row per vendor/pricing model |
| `data/scraping_api_tco_2026.jsonl` | 14 | Same records as newline-delimited JSON |

## Schema

| Column | Type | Meaning |
|---|---|---|
| `vendor` | string | ScraperAPI, ZenRows, ScrapingBee, Crawlbase, Bright Data, Smartproxy residential, self-hosted Playwright |
| `scenario` | string | `measured` or `hard_target_plus8pp` stress case |
| `pricing_model` | string | `credits`, `requests` or `bandwidth` |
| `plan_usd_month` | float | Entry plan used for unit economics |
| `included_units` | int | Credits / requests / GB in that plan |
| `unit_cost_usd` | float | USD per credit, request or GB |
| `js_render_multiplier` | int | Credit multiplier for JS rendering |
| `premium_proxy_multiplier` | int | Credit multiplier for premium/residential egress |
| `credits_per_attempt_js_premium` | int | Credits burned per hard-page attempt |
| `block_rate_pct` | float | Share of attempts that return a challenge/403 |
| `attempts_per_clean_page` | float | `1 / (1 - block_rate)` |
| `cost_per_1k_clean_usd` | float | **Comparable metric** |
| `cost_per_100k_clean_usd` | float | Scale check |

## Method

```
attempts_per_clean_page = 1 / (1 - block_rate)
credits_cost            = unit_cost * credits_per_attempt * attempts_per_clean_page
bandwidth_cost          = price_per_gb * 0.180MB/1024 * attempts_per_clean_page
self_hosted_cost        = monthly_vps / monthly_page_capacity * attempts_per_clean_page
```

Block rates are the published benchmark's measured success rates (`success = 100 - block`) for the
same target set; the hard-target 15% block rate applies to raw residential bandwidth and self-hosted
Playwright, where no managed unblocker sits in front of the request.

## Summary table

| Vendor | Scenario | Credits/attempt (JS+premium) | Block % | $/1k clean | $/100k clean |
|---|---|---|---|---|---|
| ZenRows | measured | 50 | 1.5% | $9.95 | $995 |
| ZenRows | hard_target_plus8pp | 50 | 9.5% | $10.83 | $1083 |
| ScrapingBee | measured | 50 | 2.2% | $16.72 | $1672 |
| ScrapingBee | hard_target_plus8pp | 50 | 10.2% | $18.21 | $1821 |
| ScraperAPI | measured | 50 | 3.5% | $25.39 | $2539 |
| ScraperAPI | hard_target_plus8pp | 50 | 11.5% | $27.68 | $2768 |
| Crawlbase | measured | 5 | 4.8% | $7.62 | $762 |
| Crawlbase | hard_target_plus8pp | 5 | 12.8% | $8.31 | $831 |
| Bright Data | measured | 1 | 0.5% | $1.51 | $151 |
| Bright Data | hard_target_plus8pp | 1 | 8.5% | $1.64 | $164 |
| Smartproxy (Decodo) Residential | measured | 0 | 15.0% | $0.72 | $72 |
| Smartproxy (Decodo) Residential | hard_target_plus8pp | 0 | 23.0% | $0.80 | $80 |
| Self-Hosted Playwright (4 vCPU VPS) | measured | 0 | 15.0% | $0.47 | $47 |
| Self-Hosted Playwright (4 vCPU VPS) | hard_target_plus8pp | 0 | 23.0% | $0.52 | $52 |

Note the ordering inversion: the vendor with the lowest credit burn is not the vendor with the lowest
cost per clean page once retries are priced.

## Use the calculators, CLI and mirror

- [Interactive calculator](https://scrape.mybskm.top/calculator/?utm_source=hf_dataset_scrape)
- [Benchmark site](https://scrape.mybskm.top/?utm_source=hf_dataset_scrape)
- [HuggingFace Space](https://huggingface.co/spaces/600me/rag-web-scraping-cost-calculator)
- [check-proxy-tax CLI](https://github.com/600me/check-proxy-tax)

**Deep dives**
- [The 403 Tax](https://scrape.mybskm.top/blog/403-tax.html)
- [The $0.49 proxy illusion: 200 lines of CLI](https://scrape.mybskm.top/blog/proxy-cost-audit.html)


## The 4-calculator / 4-Space / 4-Dataset matrix

**Online calculators**
- [GPU cloud true TCO](https://gpu.mybskm.top/calculator/?utm_source=hf_dataset_matrix)
- [Scraping / anti-bot TCO](https://scrape.mybskm.top/calculator/?utm_source=hf_dataset_matrix)
- [Residential proxy sticky-session loss](https://proxy.mybskm.top/calculator/?utm_source=hf_dataset_matrix)
- [MoR vs US LLC breakeven](https://pay.mybskm.top/?utm_source=hf_dataset_matrix)

**HuggingFace Static Spaces**
- [gpu-cloud-h100-a100-pricing-benchmark](https://huggingface.co/spaces/600me/llm-gpu-cost-calculator)
- [web-scraping-anti-bot-api-benchmark](https://huggingface.co/spaces/600me/rag-web-scraping-cost-calculator)
- [residential-proxy-commercial-policy-matrix](https://huggingface.co/spaces/600me/residential-proxy-sticky-session-calculator)
- [global-saas-mor-vs-us-llc-fee-matrix](https://huggingface.co/spaces/600me/ai-saas-stripe-vs-mor-tax-calculator)

**HuggingFace Datasets**
- [gpu-cloud-h100-a100-pricing-benchmark](https://huggingface.co/datasets/600me/gpu-cloud-h100-a100-pricing-benchmark)
- [residential-proxy-commercial-policy-matrix](https://huggingface.co/datasets/600me/residential-proxy-commercial-policy-matrix)
- [global-saas-mor-vs-us-llc-fee-matrix](https://huggingface.co/datasets/600me/global-saas-mor-vs-us-llc-fee-matrix)


## Transparency & FTC affiliate disclosure

This dataset is published by the independent cost-research project at mybskm.top. Some outbound vendor links are affiliate links: if you open one and later buy, we may earn a commission at no extra cost to you. Commissions never change the measured numbers, the formula, or which vendor wins a scenario, and the free open-source baseline is included on purpose because it pays us nothing. Every price is a vendor-published list rate captured on the `observed_at` date; prices, trials, KYC rules and refund terms change without notice. Nothing here is a quote, a guarantee of eligibility, tax or legal advice, or a promise of results. Verify current pricing and terms with the vendor before purchasing.
