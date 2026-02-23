#!/usr/bin/env python3
"""Normalize raw feed snapshots to dashboard-ready JSON.

Inputs:
- data/raw/tradingview-ngeria-scan.json

Outputs:
- data/ngx-financials.json
- data/ngx-market.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "tradingview-ngeria-scan.json"
OUT_FIN = ROOT / "data" / "ngx-financials.json"
OUT_MKT = ROOT / "data" / "ngx-market.json"


def safe_num(value):
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    if not RAW.exists():
        raise SystemExit("Missing raw tradingview snapshot. Run scripts/fetch_real_feeds.py first.")

    payload = json.loads(RAW.read_text(encoding="utf-8"))
    rows = payload.get("data", [])

    companies = []
    market_cap = 0.0
    revenue = 0.0
    earnings = 0.0
    assets = 0.0

    for row in rows:
        symbol = row.get("s", "")
        values = row.get("d", [])
        if len(values) < 9:
            continue

        entry = {
            "ticker": symbol.split(":")[-1],
            "name": values[1] or values[0] or symbol,
            "sector": values[2] or "Unknown",
            "marketCap": safe_num(values[3]),
            "revenue": safe_num(values[4]),
            "pe": safe_num(values[5]),
            "pb": safe_num(values[6]),
            "assets": safe_num(values[7]),
            "debtToEquity": safe_num(values[8]),
            "source": "TradingView",
        }

        if entry["marketCap"]:
            market_cap += entry["marketCap"]
        if entry["revenue"]:
            revenue += entry["revenue"]
        if entry["assets"]:
            assets += entry["assets"]

        if entry["marketCap"] and entry["pe"] and entry["pe"] > 0:
            earnings += entry["marketCap"] / entry["pe"]

        companies.append(entry)

    timestamp = datetime.now(timezone.utc).isoformat()
    OUT_FIN.write_text(json.dumps({"asOf": timestamp, "companies": companies}, indent=2), encoding="utf-8")
    OUT_MKT.write_text(
        json.dumps(
            {
                "asOf": timestamp,
                "marketCap": market_cap,
                "totalRevenue": revenue,
                "totalAssets": assets,
                "impliedPE": (market_cap / earnings) if earnings else None,
                "companyCount": len(companies),
                "source": "TradingView aggregate",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {OUT_FIN.relative_to(ROOT)} and {OUT_MKT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
