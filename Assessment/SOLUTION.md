# Sixth Street Coding Assessment – Solution Documentation

## Overview

This solution implements an end-to-end portfolio analytics workflow that consumes data from the provided Mock Ledger API, performs portfolio analytics calculations, generates analytical datasets, and presents the results through an interactive React dashboard.

The solution was designed to preserve the original Mock Ledger API service and consume data exclusively through the provided API endpoints.

---

# Architecture

The final architecture consists of four components:

1. Mock Ledger API (provided service)
2. Analytics Pipeline
3. Dashboard Analytics API
4. React Dashboard

```text
Mock Ledger API
(mock_api_server.py)
          │
          ▼
Analytics Pipeline
(pipeline.py)
          │
          ▼
Generated Outputs
fund_summary.json
instrument_details.json
settlement_summary.json
cleaned_dataset.csv
          │
          ▼
Dashboard Analytics API
(dashboard_api.py)
          │
          ▼
React Dashboard
(Vite + React + AG Grid)
```

Important:

The original `mock_api_server.py` remains unchanged.
The analytics pipeline does not directly read `mock_api_responses.json`.
Ledger and valuation data are fetched exclusively through the provided REST API endpoints.

---

# Setup & Validation Instructions

## Prerequisites

Python 3.11+
Node.js 18+
npm 9+
Git

---

## Step 1 – Create Virtual Environment

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## Step 2 – Install Dependencies

```bash
pip install -r requirements.txt
```

Verify:

```bash
pip list
```

Expected packages include:

pandas
numpy
openpyxl
requests
flask
flask-cors

---

## Step 3 – Start Mock Ledger API

From the project root:

```bash
python src/mock_api_server.py
```

Expected:

```text
Running on http://localhost:5000
```

Verify:

```text
http://localhost:5000/health
```

Expected:

```json
{
  "status": "ok"
}
```

---

## Step 4 – Run Analytics Pipeline

Open a second terminal.

```bash
python src/pipeline.py
```

Pipeline Responsibilities:

Load portfolio datasets
Load fund master data
Call Mock Ledger API endpoints
Clean and normalize data
Apply FX conversions
Calculate portfolio analytics
Generate dashboard output files

Generated Files:

```text
outputs/
├── fund_summary.json
├── instrument_details.json
├── settlement_summary.json
├── cleaned_dataset.csv
```

---

## Step 5 – Start Dashboard Analytics API

Open a third terminal.

```bash
python src/dashboard_api.py
```

Expected:

```text
Running on http://localhost:5001
```

Available Endpoints:

```text
GET /api/fund-summary
GET /api/instrument-details
```

---

## Step 6 – Start React Dashboard

Open a fourth terminal.

```bash
cd dashboard
npm install
npm run dev
```

Expected:

```text
Local: http://localhost:5173
```

Open:

```text
http://localhost:5173
```

---

## Expected Execution Order

```text
1. pip install -r requirements.txt

2. python src/mock_api_server.py

3. python src/pipeline.py

4. python src/dashboard_api.py

5. cd dashboard

6. npm install

7. npm run dev

8. Open dashboard in browser
```

---

# Mock Ledger API Consumption

The analytics pipeline consumes data through the provided API endpoints:

```text
GET /v1/instruments

GET /v1/instruments/{instrument_id}/ledger-entries

GET /v1/settlements/summary
```

The pipeline includes:

API authentication using X-API-Key
Retry logic
Exponential backoff
Handling of simulated 429, 500, and 503 responses

No direct access to `mock_api_responses.json` is performed by the analytics layer.

---

# Dashboard Features

## Fund Summary

Displays:

Fund Code
Fund Name
Strategy
Principal
Valuation
Accrued Interest
Unrealized P&L
Benchmark Return
Active Positions

## Instrument Detail

Displays:

Fund Code
Instrument ID
Company Name
Current Valuation
Unrealized P&L
Concentration %
Concentration Risk Flag

## KPI Cards

Displays:

Number of Funds
Portfolio Valuation
Unrealized P&L
Active Positions
Accrued Interest

## User Experience

Implemented:

AG Grid filtering
Sorting
Floating filters
Currency formatting
Percentage formatting
Conditional risk highlighting
Responsive layout

---

# Deliverables

Included in Submission:

Original Mock Ledger API
Analytics Pipeline
Dashboard Analytics API
React Dashboard
Generated Analytics Outputs
Documentation

The solution provides a complete portfolio analytics workflow while preserving the provided Mock Ledger API and consuming ledger data exclusively through the supplied API endpoints.
