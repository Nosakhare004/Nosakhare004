const YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025];
const PERIODS = [
  { key: 'annual', label: 'Year-End Audited' },
  { key: 'h1', label: 'Half Year' },
  { key: 'quarterly', label: 'Quarterly' }
];

const state = {
  year: 2025,
  period: 'annual',
  activeCompanyTicker: null,
  companies: [],
  market: null,
  filings: []
};

const formatMoney = (value) => (value == null ? 'N/A' : `₦${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })}`);
const formatBN = (value) => (value == null ? 'N/A' : `₦${(Number(value) / 1_000_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })}bn`);
const formatNum = (value, suffix = '') => (value == null ? 'N/A' : `${Number(value).toFixed(2)}${suffix}`);

const yearSelect = document.getElementById('yearSelect');
const periodTabs = document.getElementById('periodTabs');
const companySearch = document.getElementById('companySearch');
const searchResults = document.getElementById('searchResults');

async function loadData() {
  const [financialsResponse, marketResponse, filingsResponse] = await Promise.all([
    fetch('data/ngx-financials.json'),
    fetch('data/ngx-market.json'),
    fetch('data/ngx-filings.json').catch(() => null)
  ]);

  const financials = await financialsResponse.json();
  const market = await marketResponse.json();
  const filings = filingsResponse ? await filingsResponse.json() : { filings: [] };

  state.companies = financials.companies || [];
  state.market = market;
  state.filings = filings.filings || [];
  state.activeCompanyTicker = state.companies[0]?.ticker || null;
}

function initControls() {
  YEARS.forEach((year) => {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    option.selected = year === state.year;
    yearSelect.append(option);
  });

  PERIODS.forEach((period) => {
    const button = document.createElement('button');
    button.textContent = period.label;
    button.dataset.period = period.key;
    if (period.key === state.period) button.classList.add('active');
    button.onclick = () => {
      state.period = period.key;
      [...periodTabs.children].forEach((child) => child.classList.remove('active'));
      button.classList.add('active');
      render();
    };
    periodTabs.append(button);
  });

  yearSelect.addEventListener('change', () => {
    state.year = Number(yearSelect.value);
    render();
  });

  companySearch.addEventListener('input', () => {
    const query = companySearch.value.trim().toLowerCase();
    if (!query) {
      searchResults.style.display = 'none';
      return;
    }

    const matches = state.companies
      .filter((entry) => entry.name?.toLowerCase().includes(query) || entry.ticker?.toLowerCase().includes(query) || entry.sector?.toLowerCase().includes(query))
      .slice(0, 12);

    searchResults.innerHTML = '';
    for (const item of matches) {
      const row = document.createElement('button');
      row.innerHTML = `<strong>${item.name || item.ticker}</strong><br><small>${item.ticker} · ${item.sector || 'Unknown'}</small>`;
      row.onclick = () => {
        state.activeCompanyTicker = item.ticker;
        companySearch.value = item.name || item.ticker;
        searchResults.style.display = 'none';
        render();
      };
      searchResults.append(row);
    }
    searchResults.style.display = matches.length ? 'block' : 'none';
  });

  document.getElementById('themeToggle').onclick = () => document.body.classList.toggle('dark');
}

function getActiveCompany() {
  return state.companies.find((x) => x.ticker === state.activeCompanyTicker);
}

function getFilingsForTicker(ticker) {
  return state.filings.filter((f) => f.ticker === ticker);
}

function currentFiling(ticker) {
  return state.filings.find((f) => f.ticker === ticker && f.year === state.year && f.period === state.period);
}

function renderMarket() {
  const m = state.market || {};
  const cards = [
    ['Market Capitalization', formatBN(m.marketCap)],
    ['Total Listed Revenue', formatBN(m.totalRevenue)],
    ['NGX Valuation (P/E)', formatNum(m.impliedPE, 'x')],
    ['All Share Index (ASI)', m.allShareIndex ? Number(m.allShareIndex).toLocaleString() : 'N/A'],
    ['Listed Companies Tracked', String(m.companyCount || state.companies.length || 0)],
    ['Total Asset Base', formatBN(m.totalAssets)]
  ];

  document.getElementById('marketCards').innerHTML = cards.map(([label, value]) =>
    `<article class="metric-card"><p>${label}</p><h3>${value}</h3></article>`
  ).join('');
}

function renderCompany() {
  const company = getActiveCompany();
  if (!company) {
    document.getElementById('companyTitle').textContent = 'Company Focus';
    document.getElementById('companyStats').innerHTML = '<p>No company data loaded. Run feed ingestion scripts.</p>';
    return;
  }

  document.getElementById('companyTitle').textContent = `Company Focus · ${company.name} (${company.ticker})`;
  const filing = currentFiling(company.ticker);

  const stats = [
    ['Sector', company.sector || 'Unknown'],
    ['Market Cap', formatBN(company.marketCap)],
    ['Revenue (TTM/latest)', formatBN(company.revenue)],
    ['Total Assets (latest)', formatBN(company.assets)],
    ['P/E', formatNum(company.pe, 'x')],
    ['P/B', formatNum(company.pb, 'x')],
    ['Debt/Equity', formatNum(company.debtToEquity, 'x')],
    ['Filing Snapshot', filing ? `${filing.period.toUpperCase()} ${filing.year}` : 'Not loaded']
  ];

  if (filing) {
    stats.push(['Filing Revenue', formatBN(filing.revenue)]);
    stats.push(['Filing Net Income', formatBN(filing.netIncome)]);
    stats.push(['Filing Op. Cash Flow', formatBN(filing.operatingCashFlow)]);
    stats.push(['Filing Total Equity', formatBN(filing.totalEquity)]);
  }

  document.getElementById('companyStats').innerHTML = stats.map(([k, v]) =>
    `<article class="metric-card"><p>${k}</p><h3>${v}</h3></article>`
  ).join('');

  const trends = YEARS.map((year) => state.filings.find((f) => f.ticker === company.ticker && f.year === year && f.period === state.period)).filter(Boolean);
  drawLineChart('revenueChart', trends, [{ key: 'revenue', color: '#005bff' }]);
  drawLineChart('profitChart', trends, [
    { key: 'netIncome', color: '#19a974' },
    { key: 'operatingCashFlow', color: '#ff8c00' }
  ]);
}

function renderPeers() {
  const active = getActiveCompany();
  if (!active) return;

  const peers = state.companies
    .filter((entry) => entry.sector === active.sector)
    .sort((a, b) => (b.revenue || 0) - (a.revenue || 0))
    .slice(0, 12);

  document.getElementById('peerContext').textContent =
    `${active.name} benchmarked against ${active.sector} peers using latest feed snapshot (${state.market?.asOf || 'unknown date'}).`;

  document.getElementById('peerTable').innerHTML = peers.map((p) => `
    <tr>
      <td>${p.name || p.ticker}</td>
      <td>${p.revenue == null ? 'N/A' : (p.revenue / 1_000_000_000).toFixed(2)}</td>
      <td>${p.ebitdaMargin == null ? 'N/A' : (p.ebitdaMargin * 100).toFixed(1) + '%'}</td>
      <td>${p.pe == null ? 'N/A' : p.pe.toFixed(1) + 'x'}</td>
      <td>${p.pb == null ? 'N/A' : p.pb.toFixed(2) + 'x'}</td>
      <td>${p.assets == null ? 'N/A' : (p.assets / 1_000_000_000).toFixed(2)}</td>
      <td>${p.debtToEquity == null ? 'N/A' : p.debtToEquity.toFixed(2) + 'x'}</td>
      <td>${p.leverageRatio == null ? 'N/A' : p.leverageRatio.toFixed(2) + 'x'}</td>
    </tr>
  `).join('');
}

function drawLineChart(canvasId, rows, series) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  if (!rows.length) {
    ctx.fillStyle = '#7c8ea8';
    ctx.fillText('No filing trend loaded for this company/period.', 20, 30);
    return;
  }

  const maxVal = Math.max(...rows.flatMap((row) => series.map((s) => row[s.key] || 0)), 1);
  const minX = 40;
  const maxX = width - 20;
  const minY = 20;
  const maxY = height - 30;

  ctx.strokeStyle = '#8fa5c0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(minX, minY);
  ctx.lineTo(minX, maxY);
  ctx.lineTo(maxX, maxY);
  ctx.stroke();

  rows.forEach((row, i) => {
    const x = minX + (i * (maxX - minX)) / Math.max(rows.length - 1, 1);
    ctx.fillStyle = '#789';
    ctx.fillText(String(row.year), x - 10, maxY + 16);
  });

  for (const s of series) {
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    rows.forEach((row, i) => {
      const x = minX + (i * (maxX - minX)) / Math.max(rows.length - 1, 1);
      const y = maxY - ((row[s.key] || 0) / maxVal) * (maxY - minY);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
}

function render() {
  renderMarket();
  renderCompany();
  renderPeers();
}

(async function boot() {
  initControls();
  await loadData();
  render();
})();
