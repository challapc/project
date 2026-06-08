# Sixth Street Coding Assessment – Solution Documentation


## steps to run the Proejct: 

# Setup & Validation Instructions

## Prerequisites

Ensure the following are installed:

* Python 3.11+
* Node.js 18+
* npm 9+
* Git

---

# Step 1 – Clone & Extract Project

```bash
git clone <repository_url>
cd coding-assignment
```

or extract the provided ZIP file and navigate to the project root.

---

# Step 2 – Create Python Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Step 3 – Install Python Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

Verify installation:

```bash
pip list
```

Expected core packages:

* pandas
* numpy
* openpyxl
* requests
* Flask
* Flask-CORS

---

# Step 4 – Run Portfolio Analytics Pipeline

From the project root:

```bash
python pipeline.py
```

Purpose:

* Load CSV data
* Load Excel data
* Fetch API data
* Clean and validate datasets
* Perform FX conversion
* Generate analytical outputs
* Create transformed datasets used by dashboard APIs

Expected Result:

* Pipeline completes successfully without errors.
* Analytical output files are generated.

---

# Step 5 – Start Mock API Server

Open a new terminal.

Activate the virtual environment.

Navigate to the dashboard source folder if required.

Run:

```bash
python src/mock_api_server.py
```

(or)

```bash
python mock_api_server.py
```

depending on project structure.

Expected Output:

```text
* Running on http://127.0.0.1:5000
```

API should now be available.

---

# Step 6 – Validate API Endpoints

Open a browser and verify:

### Fund Summary Endpoint

```text
http://localhost:5000/api/fund-summary
```

Expected:

JSON response containing fund-level metrics.

---

### Instrument Analytics Endpoint

```text
http://localhost:5000/api/instrument-analytics
```

Expected:

JSON response containing:

* Instrument details
* Unrealized P&L
* Concentration metrics
* Valuation information

---

# Step 7 – Start React Dashboard

Open another terminal.

Navigate to dashboard:

```bash
cd dashboard
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Expected Output:

```text
Local: http://localhost:3000
```

(or Vite may provide)

```text
Local: http://localhost:5173
```

Use the URL displayed in the terminal.

---

# Step 8 – Validate Dashboard

Open:

```text
http://localhost:3000
```

(or the Vite URL shown in terminal)


# Expected Execution Order

```text
1. pip install -r requirements.txt

2. python pipeline.py

3. python src/mock_api_server.py

4. cd dashboard

5. npm install

6. npm run dev

7. Open Dashboard URL

8. Validate API endpoints and dashboard output


## Overview

This solution implements the complete portfolio analytics workflow:

Data ingestion from CSV, Excel, and API sources
Data cleaning and normalization
Instrument-level data consolidation
FX conversion to USD
Portfolio analytics calculations
Mock API enhancements
React + AG Grid dashboard integration
Production architecture recommendations

---

# Part 1 – Data Ingestion & Cleaning

## Data Sources

### 1. Portfolio Investments

Source: `portfolio_investments.csv`

Contains:

* Instrument details
* Fund assignments
* Principal invested
* Coupon rates
* Strategy classifications

### 2. Fund Master Data

Source: `fund_master_data.xlsx`

Contains:

* Fund metadata
* Benchmark returns
* Fund attributes

### 3. Ledger / Valuation Data

Source: Mock API

Contains:

* Valuation history
* Interest accrued
* Currency information
* Entry dates

---

## Data Quality Issues Identified

### Issue 1 – Missing Values

Observed:

* Null coupon rates
* Missing accrued interest values

Resolution:

* Filled missing interest values with 0
* Preserved null coupon rates where appropriate
* Excluded null coupon values from weighted-average calculations

---

### Issue 2 – Duplicate Ledger Entries

Observed:

* Multiple ledger records for the same instrument

Resolution:

* Sorted by entry date
* Retained all records for historical analysis
* Selected the most recent entry per instrument for unified portfolio view

---

### Issue 3 – Inconsistent Date Formats

Observed:

* Different date formats across sources

Resolution:

* Converted all dates to standardized datetime format
* Normalized timestamps prior to joins and FX calculations

---

### Issue 4 – Currency Mismatches

Observed:

* Monetary values reported in multiple currencies

Resolution:

* Applied FX conversion using:

  * Exact matching FX date when available
  * Closest available FX date when exact date unavailable

All analytical outputs are reported in USD.

---

### Issue 5 – Join Key Validation

Observed:

* Potential mismatches between instrument identifiers

Resolution:

* Standardized identifier formatting
* Trimmed whitespace
* Validated uniqueness before joining datasets

---

## Unified Dataset Construction

The final instrument-level dataset was built by:

1. Loading all source datasets.
2. Cleaning and standardizing fields.
3. Selecting the most recent ledger entry for each instrument.
4. Joining:

   * Portfolio Investments
   * Fund Master Data
   * Latest Ledger Record
5. Converting all monetary values to USD.

Result:

One consolidated instrument-level analytical table containing:

* Fund information
* Instrument information
* Principal invested
* Current valuation
* Accrued interest
* Coupon rate
* Benchmark information
* Historical valuation metadata

---

# Part 2 – Analytical Calculations

## 1. Unrealized P&L per Instrument

Formula:

Unrealized P&L = Last Valuation (USD) − Principal Invested (USD)

Percentage:

Unrealized P&L % =
(Unrealized P&L / Principal Invested) × 100

Output fields:

* Instrument ID
* Fund
* Principal Invested USD
* Current Valuation USD
* Unrealized P&L USD
* Unrealized P&L %

---

## 2. Total Accrued Interest by Fund

Calculation:

Sum(Interest Accrued USD)

Grouped by:

* Fund

Output fields:

* Fund
* Total Accrued Interest USD

---

## 3. Concentration Risk

Formula:

Instrument Weight =
Instrument Valuation /
Total Fund Valuation

Threshold:

Flag positions exceeding 40% of total fund valuation.

Output fields:

* Fund
* Instrument
* Current Valuation USD
* Fund Valuation USD
* Concentration %
* Concentration Flag

---

## 4. Weighted Average Coupon Rate by Strategy

Formula:

Weighted Coupon =
Σ(Coupon × Principal Invested)
/
Σ(Principal Invested)

Grouped by:

* Strategy

Output fields:

* Strategy
* Weighted Average Coupon Rate

---

## 5. Fund-Level Summary

Metrics produced:

### Total Principal Deployed

Sum(Principal Invested USD)

### Total Current Valuation

Sum(Current Valuation USD)

### Total Unrealized P&L

Current Valuation − Principal

### Total Unrealized P&L %

(Total P&L / Total Principal) × 100

### Active Positions

Count of instruments

### Benchmark Return

Retrieved from Fund Master workbook

Output fields:

* Fund
* Total Principal USD
* Total Valuation USD
* Unrealized P&L USD
* Unrealized P&L %
* Active Positions
* Benchmark Return

---

## 6. Month-over-Month Valuation Change

For instruments with multiple historical ledger entries:

Selected:

* Most recent valuation
* Second most recent valuation

Calculated:

### Absolute Change

Current Valuation − Previous Valuation

### Percentage Change

(Current − Previous) / Previous × 100

Output fields:

* Instrument
* Previous Valuation
* Current Valuation
* MoM Change USD
* MoM Change %

---

# Part 3 – Dashboard Implementation

## Mock API Enhancements

Added analytical endpoints to:

`src/mock_api_server.py`

Examples:

### Fund Summary Endpoint

GET /api/fund-summary

Returns:

* Fund-level summary metrics

### Instrument Analytics Endpoint

GET /api/instrument-analytics

Returns:

* Unrealized P&L
* Concentration risk
* Valuation details

---

## Dashboard Enhancements

### Fund Summary Grid

Replaced placeholder dataset with live analytical data.

Displayed:

* Fund
* Principal
* Valuation
* P&L
* Active Positions
* Benchmark Return

---

### Instrument Analytics Grid

Added second AG Grid displaying:

* Instrument
* Fund
* Valuation
* Unrealized P&L
* Concentration %
* Risk Flag

---

### UI Improvements

Implemented:

* Currency formatting
* Percentage formatting
* Conditional highlighting for concentration breaches
* Responsive grid layout

---

# Part 4 – Scaling & Architecture

## Question 1 – Scaling to 100,000+ Instruments

### Challenges

* Larger joins
* Increased API volume
* Longer processing times
* Memory constraints

### Recommended Changes

Move from pandas to:

* Polars
* Apache Spark

Storage:

* Parquet
* Delta Lake

Processing:

* Partitioned datasets
* Incremental processing
* Distributed computation

Infrastructure:

* Kubernetes
* Databricks
* AWS EMR

Benefits:

* Horizontal scalability
* Reduced memory usage
* Faster analytical workloads

---

## Question 2 – Daily Scheduling

### Recommended Orchestrator

Apache Airflow

### DAG Structure

1. Fetch Portfolio Data
2. Fetch Fund Data
3. Fetch API Data
4. Data Validation
5. FX Conversion
6. Dataset Consolidation
7. Analytics Calculation
8. API Refresh
9. Dashboard Availability Check

### Retry Strategy

* Exponential backoff
* Maximum 5 retries

### Alerting

* Slack notifications
* Email alerts
* PagerDuty integration

Triggered on:

* Task failures
* Data quality failures
* SLA breaches

---

## Question 3 – Automated Data Quality

### Frameworks

* Great Expectations
* Soda
* dbt tests

### Checks

Schema Validation:

* Required columns exist

Null Checks:

* Key identifiers not null

Uniqueness Checks:

* Instrument IDs unique

Range Checks:

* Coupon rates within valid bounds

Referential Integrity:

* Instruments mapped to valid funds

Freshness Checks:

* Ledger data delivered on schedule

### Production Pattern

Pipeline fails fast when critical validations fail.

---

## Question 4 – Production-Grade API Resilience

### Retry Logic

Use:

* Exponential backoff
* Jitter

Example:

1s → 2s → 4s → 8s

---

### Rate Limiting

Implement:

* Token bucket
* Request throttling

---

### Circuit Breaker

Open circuit when repeated failures occur.

Benefits:

* Prevents cascading failures
* Protects downstream systems

---

### Async Parallel Fetching

Use:

* asyncio
* aiohttp

Benefits:

* Faster API ingestion
* Better throughput

---

### Monitoring

Track:

* Latency
* Error rates
* Retry counts
* Success percentages

Tools:

* Prometheus
* Grafana
* Datadog

---

## Question 5 – Schema Evolution

### Defensive Parsing

Avoid hardcoded assumptions.

Use:

* Optional fields
* Default values
* Schema versioning

---

### Data Contracts

Establish:

* Producer/Consumer agreements
* Backward compatibility guarantees

---

### Schema Validation Layer

Validate incoming payloads using:

* Pydantic
* Marshmallow

---

### Versioned APIs

Examples:

/v1/portfolio

/v2/portfolio

Allows gradual migration without breaking consumers.

---

### Monitoring for Drift

Detect:

* New columns
* Missing columns
* Type changes

Automatically generate alerts when schema changes are detected.

---

# Deliverables

Included in Submission:

Source code
Dashboard modifications
Mock API enhancements
Analytical calculations
Documentation (this file)
Executable project package

The solution produces a complete end-to-end portfolio analytics workflow, exposing cleaned and enriched analytical data through API endpoints and an interactive React dashboard.