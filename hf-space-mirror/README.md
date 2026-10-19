---
title: LLM & RAG Web Scraping Cost Calculator
emoji: 🕷️
colorFrom: blue
colorTo: blue
sdk: static
pinned: false
license: mit
short_description: Calculate true proxy & anti-bot TCO for RAG/LLM web scraping
---

# LLM & RAG Web Scraping Cost Calculator

A single-file, zero-dependency Static Space for answering the question that decides a RAG budget: **what does one clean Markdown page actually cost after Cloudflare, Turnstile, Chromium and residential-proxy billing?**

The page compares two operating models on the same denominator — 1,000 delivered, usable pages:

- **DIY Playwright + residential proxy:** per-GB proxy traffic, retry amplification, challenge-page bytes, Chromium compute and $75/hour maintenance.
- **Managed scraping API:** one credit for a standard request, five for JavaScript rendering, with only delivered `200 OK` pages billed in the model.

## What it computes

- **Retry multiplier:** `M_retry = 1 / (1 - block_rate)`.
- **Challenge bandwidth:** `effective_bw_factor = 1 + (block_rate / (1 - block_rate)) × 0.35`.
- **Payload per clean page:** `html_kb × ((1 - js_share) + js_share × 2.4) × effective_bw_factor`.
- **Real proxy traffic:** `pages × avg_kb_per_clean_page / 1,048,576`.
- **Effective proxy rate:** real proxy spend divided by the nominal clean-HTML GB, so the headline `$ / GB` cannot hide retries or asset bloat.
- **DIY total:** proxy bandwidth + `$18` per 100,000 Chromium renders + engineering hours at `$75/hour`.
- **Managed total:** standard requests at 1 credit and rendered requests at 5 credits, then the published tiers: `$49` up to 250k, `$149` up to 1M, `$299` up to 3M, and `$0.000095/credit` above 3M.
- **Outputs:** effective `$ / 1,000 clean pages`, monthly total, real GB, retry multiplier, managed credits and the lower-cost recommendation rule.

All six inputs synchronize to URL query parameters. The **Copy share link** button captures the exact scenario.

## Static by design

`sdk: static` means no container, no Python server and no cold start. `index.html` is the complete page: plain HTML, CSS and vanilla JavaScript, with no external scripts, stylesheets or tracking pixels.

## Links

All four calculators in this matrix are mirrored as zero-dependency Hugging Face Static Spaces:

1. GPU Fit & Cost Calculator: https://huggingface.co/spaces/600me/llm-gpu-cost-calculator
2. **This Space** — LLM & RAG web-scraping TCO: https://huggingface.co/spaces/600me/rag-web-scraping-cost-calculator
3. Residential proxy sticky-session & `cf_clearance` loss: https://huggingface.co/spaces/600me/residential-proxy-sticky-session-calculator
4. MoR vs US LLC + Stripe breakeven: https://huggingface.co/spaces/600me/ai-saas-stripe-vs-mor-tax-calculator

- Main-site calculator: https://scrape.mybskm.top/calculator/
- CLI audit — `check-proxy-tax`: https://github.com/600me/check-proxy-tax

## Scope and disclosure

This is a planning model, not a vendor quote, a service guarantee or a benchmark of any specific target. Managed pricing assumes failed retries consume no credits; verify current billing terms with the provider. Storage, embeddings, inference, taxes and minimum commitments are excluded.

The Smartproxy / Decodo and ScraperAPI buttons are affiliate links (`src=hf_space_scrape_diy` and `src=hf_space_scrape_api`). We may earn a commission at no additional cost to the visitor. The commission does not change the calculation or the recommendation rule.

The calculator core is cross-checked against an independent Python implementation by `test_scraping_calculator_math.py` in the main repository.
