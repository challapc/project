# Analytics Engineer — Take-Home Case Study

You are an analytics engineer at a alternative investment firm. Your team manages multiple funds that invest across a range of private-credit instruments. Internal portfolio data lives in flat files, fund metadata is maintained in an Excel workbook, and a third-party ledger system exposes valuation and accrued-interest data through a REST API.

Your job is to **build a reproducible Python pipeline** that ingests all three sources, cleans and joins them, performs a set of analytical calculations, and produces executive-ready output.

---

## Project Structure
```
├── data/
│   ├── portfolio_investments.csv   # internal portfolio and instrument-level investment data
│   ├── fund_master_data.xlsx       # fund metadata workbook (multiple sheets)
│   └── mock_api_responses.json     # backing data for the local mock API
├── src/
│   └── mock_api_server.py          # local Flask server that simulates a third-party ledger API
├── dashboard/                       # pre-scaffolded React + AG Grid dashboard
│   ├── src/
│   │   ├── App.jsx                  # main component with a placeholder AG Grid table
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── pyproject.toml
├── poetry.lock
└── README.md (this file)
```

---

## Setup
1. Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already.
2. Install dependencies:
   ```
   poetry install
   ```
3. Start the mock API server:
   ```
   poetry run python src/mock_api_server.py
   ```
4. The API runs at `http://localhost:5000`.

### Authentication
All `/v1/*` endpoints require an API key passed via the `X-API-Key` header:
```
X-API-Key: test-api-key-2026
```
Requests without a valid key will receive a `401` or `403` response.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `GET` | `/status` | Service version, uptime, instrument count (no auth) |
| `GET` | `/v1/instruments` | List all instrument IDs (supports `?page=&page_size=`) |
| `GET` | `/v1/instruments/<id>` | Instrument metadata (entry count, date range) |
| `GET` | `/v1/instruments/<id>/ledger-entries` | Ledger entries for an instrument (supports `?page=&page_size=&as_of=`) |
| `GET` | `/v1/settlements/summary` | Aggregated settlement status counts across all instruments |
| `POST` | `/v1/instruments/batch-entries` | Fetch ledger entries for up to 20 instruments in one request |

### Example requests
```bash
# Health check
curl http://localhost:5000/health

# List instruments (paginated)
curl -H "X-API-Key: test-api-key-2026" "http://localhost:5000/v1/instruments?page=1&page_size=10"

# Get ledger entries for a single instrument
curl -H "X-API-Key: test-api-key-2026" "http://localhost:5000/v1/instruments/ALDBT-2026-TL/ledger-entries"

# Filter entries by date
curl -H "X-API-Key: test-api-key-2026" "http://localhost:5000/v1/instruments/ALDBT-2026-TL/ledger-entries?as_of=2025-02-28"

# Batch request (POST)
curl -X POST -H "X-API-Key: test-api-key-2026" -H "Content-Type: application/json" \
  -d '{"instrument_ids": ["ALDBT-2026-TL", "CRSMD-2030-TL"]}' \
  http://localhost:5000/v1/instruments/batch-entries
```

---

## Data Sources

### 1. `portfolio_investments.csv`
Internal portfolio data with one row per instrument position. Key fields include `fund_code`, `instrument_id`, `instrument_type`, `principal_invested`, `currency`, `coupon_rate`, `maturity_date`, `internal_price`, and `position_status`.

### 2. `fund_master_data.xlsx`
Excel workbook with multiple sheets:
- **funds** — fund-level metadata (code, name, strategy, PM, status, vintage, base currency, target AUM)
- **fx_rates** — historical FX rates by date (currency pair → USD)
- **benchmarks** — Q1 2025 benchmark returns by strategy
- **notes** — contextual notes about the workbook

### 3. Mock Ledger API
A local Flask server simulating a third-party valuation and ledger system. Provides multiple REST resources for instruments, ledger entries, and settlement statuses.

**API behaviors to handle:**
- **Authentication** — all `/v1/*` endpoints require an `X-API-Key` header.
- **Transient errors** — some instruments return 500 or 503 on initial requests. Your code should implement retries with backoff.
- **Rate limiting** — passing `?rate_limit=true` simulates a 429 response.
- **Pagination** — list and entry endpoints support `?page=&page_size=` for paginated responses.
- **Date filtering** — the ledger entries endpoint supports `?as_of=YYYY-MM-DD` to filter historical entries.
- **Batch endpoint** — `POST /v1/instruments/batch-entries` accepts up to 20 instrument IDs and returns partial results (some may be errors).
- **Dirty data** — some numeric values are returned as locale-formatted strings (e.g., `"27.621.000,50"` for European formatting, `"10,120,000"` for US comma-separated).
- **Orphan records** — at least one instrument in the CSV will **not** exist in the API.
- **Null values** — at least one API instrument may return `null` for valuation fields.

---

## Assignment Tasks

### Part 1 — Data Ingestion & Cleaning
1. Load all three data sources into dataframes (pandas or polars).
2. Identify and handle all data quality issues you encounter. Document each issue and your resolution.
3. Join the datasets into a single unified table at the instrument level, using the **most recent** ledger entry per instrument.
4. Convert all monetary values to **USD** using the FX rates provided (use the rate matching the entry date, or the closest available date).

### Part 2 — Analytical Calculations
Using the cleaned, joined dataset, compute the following:

1. **Unrealized P&L per instrument** — `last_valuation (USD) - principal_invested (USD)`. Include both absolute and percentage.
2. **Total accrued interest by fund** — sum of `interest_accrued` (USD-converted) grouped by fund.
3. **Concentration risk** — for each fund, what percentage of total fund valuation does each instrument represent? Flag any instrument that exceeds 40% of its fund's total valuation.
4. **Weighted average coupon rate by strategy** — weighted by `principal_invested`.
5. **Fund-level summary** — for each fund, produce: total principal deployed (USD), total current valuation (USD), total unrealized P&L (USD & %), number of active positions, and the fund's benchmark return from the workbook.
6. **Month-over-month valuation change** — for instruments with multiple ledger entries, compute the absolute and percentage change between the two most recent entries.

### Part 3 — Dashboard
A pre-scaffolded React + AG Grid application is provided in `dashboard/`. You will modify the mock API server to add new endpoints that return your cleaned/transformed analytical results, and update the dashboard to fetch and display data from those endpoints.

**Setup:**
```bash
cd dashboard
npm install
npm run dev
```
The dashboard runs at `http://localhost:3000`.

**Requirements:**
1. Add one or more endpoints to the mock API server (`src/mock_api_server.py`) that return your analytical output (e.g., fund-level summary, instrument-level detail).
2. Update the dashboard to fetch from your new endpoint(s) and display the **fund-level summary** (Part 2, #5) in the provided AG Grid table — replace the placeholder data.
3. Add at least **one additional grid** showing instrument-level detail (e.g., unrealized P&L, concentration risk).
4. You may add charts, tabs, formatting, or any other UI enhancements you see fit.

The scaffold includes a working AG Grid table with dummy data as a starting point.

### Part 4 — Scaling & Architecture (Written Responses)
Answer the following questions in your README or a separate markdown file:

1. **Volume** — If the portfolio grew to 100,000+ instruments across 50 funds, what changes would you make to your pipeline? What tooling or frameworks would you reach for?
2. **Scheduling** — How would you orchestrate this pipeline to run daily? What would your DAG look like? What retry and alerting strategies would you implement?
3. **Data quality** — How would you build automated data quality checks into a production pipeline? What frameworks or patterns would you use?
4. **API resilience** — The mock API simulates transient failures and rate limiting. How would you design a production-grade API client to handle these at scale? Consider: retries, backoff, circuit breakers, async/parallel fetching.
5. **Schema evolution** — If the API started returning new fields or changed its response structure, how would you make your pipeline resilient to schema changes?

---

## Deliverables
Please provide:
- [ ] All source code (clean, modular, well-structured)
- [ ] A `README.md` describing your approach, assumptions, data quality issues found, and answers to Part 4
- [ ] Output files: cleaned dataset (CSV or Parquet)
- [ ] Dashboard wired with your analytical output
- [ ] Any tests you write (encouraged but not required)

**Submission:**
Zip the entire project directory, **including the `.git` folder**, so we can review your commit history. Please ensure `node_modules/` is excluded from the zip (it will be regenerated via `npm install`).

**Time expectation:** ~1-2 days (a weekend project). Focus on quality and clarity over completeness — it's fine to note what you would do differently with more time.


---

## Technical Notes
- Use Python 3.12+.
- You may use any dataframe tooling — we're interested in your comfort with dataframe operations.
- The mock API server must be running locally for your pipeline to fetch ledger data.
- Don't make any assumptions about correctness of the provided code.
- All data quality issues are **intentional** — finding and documenting them is part of the evaluation.
- You are permitted to use AI for the coding assignment. However, please note that AI is strictly prohibited during the live tech round, and you must be prepared to fully explain any code you submit, regardless of how it was generated.