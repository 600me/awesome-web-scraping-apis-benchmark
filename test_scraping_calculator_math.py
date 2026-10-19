#!/usr/bin/env python3
"""Offline math and packaging checks for the RAG web-scraping TCO calculator.

The Python model below is independent of the browser code.  A second pass
extracts the shipped `calc-core` script and runs the same cases through Node,
so the published page cannot drift from the arithmetic certified here.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CALC = ROOT / "calculator" / "index.html"
MIRROR_INDEX = ROOT / "hf-space-mirror" / "index.html"
MIRROR_README = ROOT / "hf-space-mirror" / "README.md"
SITEMAP = ROOT / "sitemap.xml"

KB_PER_GB = 1024 * 1024
CHALLENGE_BYTES_SHARE = 0.35
JS_PAYLOAD_MULTIPLIER = 2.4
COMPUTE_USD_PER_100K_RENDERS = 18.0
ENGINEER_USD_PER_HOUR = 75.0
MANAGED_CREDIT_MULTIPLIER = 5
MANAGED_LINEAR_USD = 0.000095

DEFAULTS = {
    "pages": 500000,
    "html_kb": 450,
    "block_rate": 28,
    "js_share": 40,
    "proxy_gb_price": 3.5,
    "eng_hours": 8,
}

RANGES = {
    "pages": (10000, 10000000),
    "html_kb": (50, 5000),
    "block_rate": (0, 80),
    "js_share": (0, 100),
    "proxy_gb_price": (0.5, 12),
    "eng_hours": (0, 1000),
}

MANAGED_TIERS = ((250000, 49.0, "≤250k"), (1000000, 149.0, "≤1M"), (3000000, 299.0, "≤3M"))

_PASSED = 0


def check(condition: bool, message: str) -> None:
    global _PASSED
    if not condition:
        raise AssertionError(message)
    _PASSED += 1
    print(f"PASS  {message}")


def close(actual: float, expected: float, rel: float = 1e-9) -> bool:
    return abs(float(actual) - float(expected)) <= max(1.0, abs(float(expected))) * rel


def clamp(key: str, value: float) -> float:
    low, high = RANGES[key]
    value = max(low, min(high, float(value)))
    return float(round(value)) if key == "pages" else value


def compute(**overrides: float) -> dict:
    p = dict(DEFAULTS)
    p.update(overrides)
    p = {key: clamp(key, value) for key, value in p.items()}

    block = p["block_rate"] / 100.0
    js = p["js_share"] / 100.0
    retry_multiplier = 1.0 / (1.0 - block)
    effective_bw_factor = 1.0 + (block / (1.0 - block)) * CHALLENGE_BYTES_SHARE
    js_multiplier = (1.0 - js) * 1.0 + js * JS_PAYLOAD_MULTIPLIER
    avg_kb = p["html_kb"] * js_multiplier * effective_bw_factor
    real_gb = p["pages"] * avg_kb / KB_PER_GB
    clean_gb = p["pages"] * p["html_kb"] / KB_PER_GB
    real_after_js = p["pages"] * p["html_kb"] * js_multiplier / KB_PER_GB
    retry_gb = real_gb - real_after_js
    js_gb = real_after_js - clean_gb
    effective_proxy_gb = (real_gb * p["proxy_gb_price"]) / clean_gb
    proxy_cost = real_gb * p["proxy_gb_price"]
    compute_cost = (p["pages"] * js / 100000.0) * COMPUTE_USD_PER_100K_RENDERS
    eng_cost = p["eng_hours"] * ENGINEER_USD_PER_HOUR
    diy_total = proxy_cost + compute_cost + eng_cost
    credits = p["pages"] * ((1.0 - js) * 1.0 + js * MANAGED_CREDIT_MULTIPLIER)

    tier_label = ">3M linear"
    managed_cost = credits * MANAGED_LINEAR_USD
    for max_credits, price, label in MANAGED_TIERS:
        if credits <= max_credits:
            managed_cost = price
            tier_label = label
            break

    diy_per_1k = diy_total / p["pages"] * 1000.0
    managed_per_1k = managed_cost / p["pages"] * 1000.0
    winner = "diy" if diy_total <= managed_cost else "managed"
    high, low = max(diy_total, managed_cost), min(diy_total, managed_cost)
    return {
        "inputs": p,
        "retryMultiplier": retry_multiplier,
        "effectiveBwFactor": effective_bw_factor,
        "jsPayloadMultiplier": js_multiplier,
        "avgKbPerCleanPage": avg_kb,
        "realGb": real_gb,
        "cleanHtmlGb": clean_gb,
        "retryChallengeGb": retry_gb,
        "jsAssetGb": js_gb,
        "effectiveProxyPerGb": effective_proxy_gb,
        "proxyCost": proxy_cost,
        "computeCost": compute_cost,
        "engCost": eng_cost,
        "diyTotal": diy_total,
        "diyPer1k": diy_per_1k,
        "totalCredits": credits,
        "managedTier": tier_label,
        "managedCost": managed_cost,
        "managedPer1k": managed_per_1k,
        "attempts": p["pages"] * retry_multiplier,
        "failedAttempts": p["pages"] * retry_multiplier - p["pages"],
        "winner": winner,
        "ratio": high / low if low else None,
    }


NODE_HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const html = fs.readFileSync(process.argv[1], 'utf8');
const match = html.match(/<script id="calc-core">([\s\S]*?)<\/script>/);
if (!match) { console.error('missing calc-core script'); process.exit(2); }
const context = {console};
vm.createContext(context);
vm.runInContext(match[1], context);
const C = context.SCRAPE_CALC;
if (!C) { console.error('SCRAPE_CALC not exported'); process.exit(3); }
const cases = JSON.parse(process.argv[2]);
const out = cases.map(function (item) {
  const r = C.compute(item);
  return {
    inputs: r.inputs,
    retryMultiplier: r.retryMultiplier,
    effectiveBwFactor: r.effectiveBwFactor,
    jsPayloadMultiplier: r.jsPayloadMultiplier,
    avgKbPerCleanPage: r.avgKbPerCleanPage,
    realGb: r.realGb,
    cleanHtmlGb: r.cleanHtmlGb,
    retryChallengeGb: r.retryChallengeGb,
    jsAssetGb: r.jsAssetGb,
    effectiveProxyPerGb: r.effectiveProxyPerGb,
    proxyCost: r.proxyCost,
    computeCost: r.computeCost,
    engCost: r.engCost,
    diyTotal: r.diyTotal,
    diyPer1k: r.diyPer1k,
    totalCredits: r.totalCredits,
    managedTier: r.managedTier,
    managedCost: r.managedCost,
    managedPer1k: r.managedPer1k,
    attempts: r.attempts,
    failedAttempts: r.failedAttempts,
    winner: r.winner,
    ratio: r.ratio
  };
});
process.stdout.write(JSON.stringify(out));
"""


def run_js_cases(cases: list[dict]) -> list[dict]:
    try:
        proc = subprocess.run(
            ["node", "-e", NODE_HARNESS, str(CALC), json.dumps(cases)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise AssertionError("Node.js is required for the JS/Python cross-check") from exc
    check(proc.returncode == 0, f"calculator JS core evaluates cleanly (node exit {proc.returncode})")
    if proc.returncode != 0:
        raise AssertionError(proc.stderr.strip())
    return json.loads(proc.stdout)


def compare_case(reference: dict, shipped: dict, label: str) -> None:
    numeric = (
        "retryMultiplier", "effectiveBwFactor", "jsPayloadMultiplier",
        "avgKbPerCleanPage", "realGb", "cleanHtmlGb", "retryChallengeGb",
        "jsAssetGb", "effectiveProxyPerGb", "proxyCost", "computeCost",
        "engCost", "diyTotal", "diyPer1k", "totalCredits", "managedCost",
        "managedPer1k", "attempts", "failedAttempts", "ratio",
    )
    for key in numeric:
        expected = reference[key]
        actual = shipped[key]
        if expected is None:
            check(actual is None, f"{label}: JS {key} is null like Python")
        else:
            check(close(actual, expected, 1e-8), f"{label}: JS {key} matches Python ({expected:.8g})")
    for key in ("pages", "html_kb", "block_rate", "js_share", "proxy_gb_price", "eng_hours"):
        check(
            close(shipped["inputs"][key], reference["inputs"][key], 1e-12),
            f"{label}: JS normalizes {key} identically",
        )
    check(shipped["winner"] == reference["winner"], f"{label}: JS winner is {reference['winner']}")
    check(shipped["managedTier"] == reference["managedTier"], f"{label}: JS managed tier is {reference['managedTier']}")


def extract_core_digest() -> str:
    html = CALC.read_text(encoding="utf-8")
    match = re.search(r'<script id="calc-core">([\s\S]*?)</script>', html)
    if not match:
        raise AssertionError("calc-core script missing")
    return hashlib.sha256(match.group(1).encode("utf-8")).hexdigest()


def main() -> int:
    print("== RAG web-scraping TCO calculator: offline math & packaging assertions ==")
    check(CALC.is_file(), f"calculator page exists: {CALC}")
    html = CALC.read_text(encoding="utf-8")
    check(len(html) > 40000, f"calculator page is a substantive single file ({len(html):,} bytes)")

    # ---- defaults -------------------------------------------------------
    d = compute()
    check(close(d["retryMultiplier"], 1 / 0.72, 1e-12),
          f"default retry multiplier = 1/(1-0.28) = {d['retryMultiplier']:.6f}")
    check(abs(d["retryMultiplier"] - 1.3889) < 0.0001,
          "default retry multiplier rounds to the mandated 1.3889")
    check(close(d["effectiveBwFactor"], 1 + (0.28 / 0.72) * 0.35, 1e-12),
          f"default bandwidth factor = {d['effectiveBwFactor']:.6f}")
    check(close(d["avgKbPerCleanPage"], 797.55, 1e-9),
          f"default avg KB per clean page = {d['avgKbPerCleanPage']:.2f} KB")
    check(close(d["realGb"], 500000 * 797.55 / KB_PER_GB, 1e-9),
          f"default real proxy traffic = {d['realGb']:.4f} GB")
    check(close(d["effectiveProxyPerGb"], 6.203166666666666, 1e-9),
          f"default effective proxy rate = ${d['effectiveProxyPerGb']:.4f}/clean GB")
    check(close(d["proxyCost"], 1331.0551643371582, 1e-9),
          f"default proxy cost = ${d['proxyCost']:.2f}")
    check(close(d["computeCost"], 36.0), "default Chromium compute = 2 × $18 = $36")
    check(close(d["engCost"], 600.0), "default engineering = 8 hrs × $75 = $600")
    check(close(d["diyTotal"], 1967.0551643371582, 1e-9),
          f"default DIY total = ${d['diyTotal']:.2f}")
    check(close(d["totalCredits"], 1300000.0), "default managed credits = 1,300,000")
    check(close(d["managedCost"], 299.0), "default managed cost uses the ≤3M tier at $299")
    check(close(d["diyPer1k"], 3.9341103286743164, 1e-9),
          f"default DIY cost / 1k = ${d['diyPer1k']:.4f}")
    check(close(d["managedPer1k"], 0.598, 1e-12),
          f"default managed cost / 1k = ${d['managedPer1k']:.4f}")
    check(d["winner"] == "managed", "default scenario recommends the managed API")
    check(abs(d["ratio"] - 6.5788) < 0.0001, "default monthly ratio is about 6.58×")

    # ---- zero-block, zero-JS, zero-maintenance --------------------------
    z = compute(pages=100000, html_kb=200, block_rate=0, js_share=0, proxy_gb_price=2.0, eng_hours=0)
    check(close(z["retryMultiplier"], 1.0), "0% blocked gives a 1.0× retry multiplier")
    check(close(z["effectiveBwFactor"], 1.0), "0% blocked gives no challenge bandwidth")
    check(close(z["avgKbPerCleanPage"], 200.0), "0% JS leaves the raw HTML payload unchanged")
    check(close(z["proxyCost"], 100000 * 200 / KB_PER_GB * 2.0, 1e-9),
          "0% JS proxy cost is exactly pages × KB × $/GB")
    check(close(z["computeCost"], 0.0), "0% JS produces zero Chromium compute")
    check(close(z["engCost"], 0.0), "0 maintenance hours produce zero labour cost")
    check(close(z["diyTotal"], z["proxyCost"]), "0% JS DIY total is proxy-only")
    check(close(z["managedCost"], 49.0), "100k credits land in the $49 tier")
    check(z["winner"] == "diy", "100k low-payload pages can favour the DIY stack when proxy traffic is cheap")
    z_managed = compute(pages=100000)
    check(close(z_managed["managedCost"], 149.0), "100k default-propensity pages (260k credits) land in the $149 tier")
    check(z_managed["winner"] == "managed", "100k pages at the default payload still favours the $149 managed API")

    # ---- hostile target --------------------------------------------------
    h = compute(pages=10000000, html_kb=1800, block_rate=80, js_share=100, proxy_gb_price=12, eng_hours=0)
    check(close(h["retryMultiplier"], 5.0, 1e-12), "80% blocked gives the mandated 5× retry multiplier")
    check(close(h["effectiveBwFactor"], 2.4, 1e-12), "80% blocked gives a 2.4× challenge bandwidth factor")
    check(close(h["avgKbPerCleanPage"], 10368.0, 1e-9),
          "80% blocked + 100% JS yields 10,368 KB per clean page")
    check(close(h["realGb"], 98876.953125, 1e-7),
          f"10M hostile pages consume {h['realGb']:.1f} GB of proxy traffic")
    check(close(h["totalCredits"], 50000000.0), "10M fully rendered pages consume 50M credits")
    check(close(h["managedCost"], 4750.0, 1e-9),
          ">3M credits use the $0.000095 linear rate: $4,750")
    check(h["winner"] == "managed", "at the model's rates the managed API still wins the hostile case")

    # ---- tier cliffs and boundaries -------------------------------------
    t250 = compute(pages=250000, js_share=0)
    t250p1 = compute(pages=250001, js_share=0)
    t1m = compute(pages=1000000, js_share=0)
    t1mp1 = compute(pages=1000001, js_share=0)
    t3m = compute(pages=3000000, js_share=0)
    t3mp1 = compute(pages=3000001, js_share=0)
    check(close(t250["managedCost"], 49.0), "exactly 250,000 credits costs $49")
    check(close(t250p1["managedCost"], 149.0), "250,001 credits jumps to the $149 tier")
    check(close(t1m["managedCost"], 149.0), "exactly 1,000,000 credits costs $149")
    check(close(t1mp1["managedCost"], 299.0), "1,000,001 credits jumps to the $299 tier")
    check(close(t3m["managedCost"], 299.0), "exactly 3,000,000 credits costs $299")
    check(close(t3mp1["managedCost"], 3000001 * MANAGED_LINEAR_USD, 1e-12),
          "3,000,001 credits uses the linear >3M rate (the documented tier cliff)")
    check(t3mp1["managedCost"] < t3m["managedCost"],
          "linear >3M pricing can undercut the $299 tier just above the boundary")
    check(close(compute(pages=10000, js_share=100)["managedCost"], 49.0),
          "10k fully rendered pages (50k credits) still costs $49")

    # ---- JS vs Python ----------------------------------------------------
    cases = [
        {},
        dict(pages=100000, html_kb=200, block_rate=0, js_share=0, proxy_gb_price=2.0, eng_hours=0),
        dict(pages=10000000, html_kb=1800, block_rate=80, js_share=100, proxy_gb_price=12, eng_hours=0),
        dict(pages=250000, js_share=0),
        dict(pages=250001, js_share=0),
        dict(pages=1000000, js_share=0),
        dict(pages=1000001, js_share=0),
        dict(pages=3000000, js_share=0),
        dict(pages=3000001, js_share=0),
        dict(pages=10000, html_kb=50, block_rate=73, js_share=100, proxy_gb_price=0.5, eng_hours=1),
        dict(pages=777777, html_kb=1800, block_rate=61, js_share=87, proxy_gb_price=7.35, eng_hours=24),
        dict(pages=1, html_kb=99999, block_rate=99, js_share=101, proxy_gb_price=99, eng_hours=9999),
    ]
    js_cases = run_js_cases(cases)
    check(len(js_cases) == len(cases), "Node returned exactly one result per case")
    for index, (case, shipped) in enumerate(zip(cases, js_cases)):
        compare_case(compute(**case), shipped, f"case {index + 1}")

    # ---- main page packaging --------------------------------------------
    check('<link rel="canonical" href="https://scrape.mybskm.top/calculator/">' in html,
          "calculator declares its self-referencing canonical URL")
    check('"@type": "WebApplication"' in html,
          "calculator ships WebApplication JSON-LD")
    check('https://go.272738.xyz/scraperapi?src=scrape_calc_api' in html,
          "managed-API CTA carries src=scrape_calc_api")
    check('https://go.272738.xyz/smartproxy?src=scrape_calc_diy' in html,
          "DIY proxy CTA carries src=scrape_calc_diy")
    check(html.count('rel="sponsored noopener noreferrer"') >= 2,
          "both affiliate CTAs are marked sponsored noopener")
    check('id="calc-core"' in html and 'id="calc-app"' in html,
          "page separates the pure model from the DOM app")
    check('searchParams.set' in html and 'history.replaceState' in html,
          "inputs synchronize to URL query parameters via replaceState")
    check('navigator.clipboard.writeText' in html and 'Copy share link' in html,
          "page includes a one-click share-link copy control")
    check('npx --yes degit 600me/check-proxy-tax' in html,
          "page includes the npx CLI checkout command")
    check('git clone https://github.com/600me/check-proxy-tax.git' in html,
          "page includes the git clone CLI command")
    check('https://gpu.mybskm.top/calculator/' in html,
          "page cross-links the GPU calculator")
    for field, minimum, maximum, default in (
        ("pages", "10000", "10000000", "500000"),
        ("html_kb", "50", "5000", "450"),
        ("block_rate", "0", "80", "28"),
        ("js_share", "0", "100", "40"),
        ("proxy_gb_price", "0.5", "12", "3.5"),
        ("eng_hours", "0", "1000", "8"),
    ):
        pattern = (
            rf'id="{field}"[^>]*type="number"[^>]*min="{re.escape(minimum)}"'
            rf'[^>]*max="{re.escape(maximum)}"[^>]*value="{re.escape(default)}"'
        )
        check(re.search(pattern, html) is not None,
              f"input {field} has the mandated min/max/default ({minimum}/{maximum}/{default})")
    check('<script src=' not in html.lower(), "calculator loads no external JavaScript")
    check('<link rel="stylesheet"' not in html.lower(), "calculator loads no external CSS")
    check('@import' not in html.lower(), "calculator has no CSS @import")
    for phrase in ("M_retry", "effective_bw_factor", "avg_kb_per_clean_page", "real_gb", "proxy_cost", "diy_total", "total_credits"):
        check(phrase in html, f"formula symbol {phrase} is documented on the page")

    # ---- mirror + README -------------------------------------------------
    check(MIRROR_INDEX.is_file(), f"Hugging Face mirror exists: {MIRROR_INDEX}")
    check(MIRROR_README.is_file(), f"Hugging Face README exists: {MIRROR_README}")
    mirror = MIRROR_INDEX.read_text(encoding="utf-8")
    readme = MIRROR_README.read_text(encoding="utf-8")
    check('src=hf_space_scrape_diy' in mirror,
          "mirror uses src=hf_space_scrape_diy")
    check('src=hf_space_scrape_api' in mirror,
          "mirror uses src=hf_space_scrape_api")
    check('src=scrape_calc_diy' not in mirror and 'src=scrape_calc_api' not in mirror,
          "mirror replaces both main-site affiliate sources")
    check('https://huggingface.co/spaces/600me/llm-gpu-cost-calculator' in mirror,
          "mirror links the first Hugging Face Space")
    check('https://scrape.mybskm.top/calculator/' in mirror,
          "mirror links the main-site calculator")
    check(extract_core_digest() == hashlib.sha256(
        re.search(r'<script id="calc-core">([\s\S]*?)</script>', mirror).group(1).encode("utf-8")
    ).hexdigest(), "mirror ships the byte-identical calculator core")

    frontmatter = [
        "---",
        "title: LLM & RAG Web Scraping Cost Calculator",
        "emoji: 🕷️",
        "colorFrom: blue",  # Hugging Face rejects cyan; blue is the nearest valid enum
        "colorTo: blue",
        "sdk: static",
        "pinned: false",
        "license: mit",
        "short_description: Calculate true proxy & anti-bot TCO for RAG/LLM web scraping",
        "---",
    ]
    check("\n".join(frontmatter) in readme,
          "README contains the exact Hugging Face Static Space YAML frontmatter")
    check("index.html" in readme, "README documents the static entry file")

    # ---- navigation + sitemap -------------------------------------------
    sitemap = SITEMAP.read_text(encoding="utf-8")
    check("https://scrape.mybskm.top/calculator/" in sitemap,
          "sitemap includes the calculator URL")
    for page in ("index.html", "blog/index.html", "blog/403-tax.html", "blog/proxy-cost-audit.html"):
        text = (ROOT / page).read_text(encoding="utf-8")
        check("/calculator/" in text, f"{page} links to /calculator/")

    # ---- no secret leakage ----------------------------------------------
    for path in (CALC, MIRROR_INDEX):
        text = path.read_text(encoding="utf-8")
        check("HF_TOKEN" not in text, f"{path.name} does not expose the HF token variable")
        check("Bearer " not in text, f"{path.name} contains no authorization header")
    check("HF_TOKEN" not in readme and "Bearer " not in readme,
          "mirror README contains no token variable or authorization header")

    print(f"\nAll {_PASSED} assertions passed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"\nFAIL  {exc}", file=sys.stderr)
        sys.exit(1)
