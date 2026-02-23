#!/usr/bin/env python3
"""Fetch NGX market and company feeds from TradingView and AfricanFinancials.

This script is designed to run server-side (not in the browser) and writes raw
JSON/HTML snapshots into data/raw for normalization.
"""
from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; NGXDashboardBot/1.0; +https://example.local)"
SSL_CTX = ssl.create_default_context()


@dataclass
class FetchResult:
    source: str
    ok: bool
    path: str | None = None
    message: str = ""


def fetch_json(url: str, payload: dict | None = None) -> dict:
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        request.add_header("content-type", "application/json")
    else:
        request = urllib.request.Request(url)

    request.add_header("user-agent", UA)
    with urllib.request.urlopen(request, timeout=45, context=SSL_CTX) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url)
    request.add_header("user-agent", UA)
    with urllib.request.urlopen(request, timeout=45, context=SSL_CTX) as response:
        return response.read().decode("utf-8", errors="replace")


def save_json(name: str, data: dict) -> str:
    path = RAW_DIR / name
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path.relative_to(ROOT))


def save_text(name: str, data: str) -> str:
    path = RAW_DIR / name
    path.write_text(data, encoding="utf-8")
    return str(path.relative_to(ROOT))


def fetch_tradingview_market_snapshot() -> FetchResult:
    # TradingView scanner endpoint for NGX symbols.
    url = "https://scanner.tradingview.com/nigeria/scan"
    payload = {
        "symbols": {"tickers": [], "query": {"types": []}},
        "columns": [
            "name",
            "description",
            "sector",
            "market_cap_basic",
            "total_revenue",
            "price_earnings_ttm",
            "price_book_fq",
            "total_assets_fq",
            "debt_to_equity",
            "typespecs",
        ],
    }
    try:
        response = fetch_json(url, payload)
        path = save_json("tradingview-ngeria-scan.json", response)
        return FetchResult("tradingview_scan", True, path, "ok")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return FetchResult("tradingview_scan", False, message=str(exc))


def fetch_africanfinancials_index() -> FetchResult:
    # AfricanFinancials companies page for NGX filings discovery.
    url = "https://africanfinancials.com/ngx"
    try:
        html = fetch_text(url)
        path = save_text("africanfinancials-ngx.html", html)
        return FetchResult("africanfinancials_ngx", True, path, "ok")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        return FetchResult("africanfinancials_ngx", False, message=str(exc))


def main() -> None:
    results = [
        fetch_tradingview_market_snapshot(),
        fetch_africanfinancials_index(),
    ]
    print(json.dumps([result.__dict__ for result in results], indent=2))


if __name__ == "__main__":
    main()
