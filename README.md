# NGX Financial Dashboard (Real Feed Pipeline)

This dashboard is now wired for **real upstream feeds** instead of synthetic generated values.

## Sources

- **TradingView**: market-wide and company latest fundamentals snapshot (market cap, revenue, P/E, P/B, assets, debt/equity).
- **AfricanFinancials**: audited/half-year/quarterly filing discovery and extraction (script scaffold included).

## Data files used by the dashboard

- `data/ngx-market.json` → market cards.
- `data/ngx-financials.json` → company search + peer comparables.
- `data/ngx-filings.json` → year/period filing trend charts and company filing metrics.

## Run locally

```bash
python -m http.server 8080
```

Open `http://localhost:8080`.

## Refresh feeds (server-side)

1. Fetch raw snapshots:

```bash
python scripts/fetch_real_feeds.py
```

2. Normalize TradingView snapshot into dashboard JSON:

```bash
python scripts/transform_feeds.py
```

3. Extend `data/ngx-filings.json` with AfricanFinancials extraction output for 2019–2025 annual/h1/quarterly filing rows.

## Notes

- In this environment, outbound network calls may be blocked. The app still runs and clearly shows `N/A` / no filing trend until fresh feed data is loaded.
- Use this schema for each filing row in `data/ngx-filings.json`:

```json
{
  "ticker": "DANGCEM",
  "year": 2024,
  "period": "annual",
  "revenue": 1234567890000,
  "netIncome": 345678900000,
  "operatingCashFlow": 456789000000,
  "totalAssets": 5678900000000,
  "totalDebt": 1234500000000,
  "totalEquity": 2345600000000
}
```
