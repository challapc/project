"""Mock Ledger API Server

Simulates a third-party valuation and ledger system.
Provides versioned REST endpoints for instruments, ledger entries,
and settlement statuses. Requires API-key authentication.

Usage:
    poetry run python src/mock_api_server.py
"""
from collections import defaultdict
from datetime import datetime, timezone
from functools import wraps
import json
import logging
import os

from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
START_TIME = datetime.now(timezone.utc)
VERSION = "1.4.0"

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
with open(os.path.join(DATA_DIR, "mock_api_responses.json"), "r", encoding="utf-8") as f:
    DATA = json.load(f)

# Valid API keys (candidates receive the key in the README)
VALID_API_KEYS = {"test-api-key-2026"}

DEFAULT_PAGE_SIZE = 5
request_counts = defaultdict(int)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_response(message, status_code, error_code=None):
    """Consistent error envelope."""
    body = {
        "error": {
            "code": error_code or f"HTTP_{status_code}",
            "message": message,
        }
    }
    return jsonify(body), status_code


def require_api_key(f):
    """Decorator that enforces API-key authentication via X-API-Key header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return _error_response("Missing X-API-Key header", 401, "UNAUTHORIZED")
        if api_key not in VALID_API_KEYS:
            return _error_response("Invalid API key", 403, "FORBIDDEN")
        return f(*args, **kwargs)
    return decorated


def _paginate(items, page, page_size):
    """Apply pagination to a list and return (page_items, pagination_meta)."""
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], {
        "page": page,
        "page_size": page_size,
        "total_records": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }


# ---------------------------------------------------------------------------
# Health & status (no auth required)
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Health check — used to verify the server is reachable."""
    return jsonify({"status": "ok"}), 200


@app.route("/status", methods=["GET"])
def status():
    """Returns service metadata and uptime."""
    uptime = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    return jsonify({
        "service": "mock-ledger-api",
        "version": VERSION,
        "uptime_seconds": round(uptime, 1),
        "instrument_count": len(DATA),
    })


# ---------------------------------------------------------------------------
# Instruments resource
# ---------------------------------------------------------------------------

@app.route("/v1/instruments", methods=["GET"])
@require_api_key
def list_instruments():
    """List all available instrument IDs with optional pagination.

    Query params:
        page (int): page number (default: returns all)
        page_size (int): items per page (default: 25)
    """
    instruments = sorted(DATA.keys())

    page = request.args.get("page", type=int)
    if page is not None:
        page_size = request.args.get("page_size", default=25, type=int)
        page_items, meta = _paginate(instruments, page, page_size)
        return jsonify({"instruments": page_items, "pagination": meta})

    return jsonify({"instruments": instruments, "total": len(instruments)})


@app.route("/v1/instruments/<instrument_id>", methods=["GET"])
@require_api_key
def get_instrument_detail(instrument_id):
    """Return summary metadata for a single instrument.

    Includes the number of ledger entries and the date range covered.
    """
    if instrument_id not in DATA:
        return _error_response(f"Instrument '{instrument_id}' not found", 404, "NOT_FOUND")

    instrument = DATA[instrument_id]
    entries = instrument["entries"]
    dates = [e["entry_date"] for e in entries if e.get("entry_date")]

    return jsonify({
        "instrument_id": instrument_id,
        "entry_count": len(entries),
        "date_range": {
            "earliest": min(dates) if dates else None,
            "latest": max(dates) if dates else None,
        },
    })


# ---------------------------------------------------------------------------
# Ledger entries resource
# ---------------------------------------------------------------------------

@app.route("/v1/instruments/<instrument_id>/ledger-entries", methods=["GET"])
@require_api_key
def get_ledger_entries(instrument_id):
    """Return ledger entries for a given instrument.

    Query params:
        page (int): page number (default: returns all entries)
        page_size (int): entries per page (default: 5)
        as_of (str): optional date filter — return entries on or before this date (YYYY-MM-DD)

    Simulated failure modes:
        - Transient 500 on GNTPW-2027-BRL (first request only)
        - Transient 503 on HRZNS-2031-TL (first two requests)
        - 429 if ?rate_limit=true is passed
    """
    request_counts[instrument_id] += 1

    # Simulate intermittent 500 for one instrument on first request
    if instrument_id == "GNTPW-2027-BRL" and request_counts[instrument_id] == 1:
        return _error_response("Temporary upstream failure", 500, "UPSTREAM_ERROR")

    # Simulate intermittent 503 for another instrument on first two requests
    if instrument_id == "HRZNS-2031-TL" and request_counts[instrument_id] <= 2:
        return _error_response("Service temporarily unavailable", 503, "SERVICE_UNAVAILABLE")

    # Simulate rate limiting
    if request.args.get("rate_limit") == "true":
        resp = _error_response("Rate limit exceeded — retry after 2s", 429, "RATE_LIMITED")
        return resp

    if instrument_id not in DATA:
        return _error_response(f"Instrument '{instrument_id}' not found", 404, "NOT_FOUND")

    instrument_data = DATA[instrument_id]
    entries = list(instrument_data["entries"])

    # Optional date filter
    as_of = request.args.get("as_of")
    if as_of:
        entries = [e for e in entries if e.get("entry_date", "") <= as_of]

    # Pagination
    page = request.args.get("page", type=int)
    page_size = request.args.get("page_size", default=DEFAULT_PAGE_SIZE, type=int)

    if page is not None:
        page_items, meta = _paginate(entries, page, page_size)
        return jsonify({
            "instrument_id": instrument_id,
            "entries": page_items,
            "pagination": meta,
        })

    return jsonify({
        "instrument_id": instrument_id,
        "entries": entries,
    })


# ---------------------------------------------------------------------------
# Settlements resource (aggregated view)
# ---------------------------------------------------------------------------

@app.route("/v1/settlements/summary", methods=["GET"])
@require_api_key
def settlement_summary():
    """Return a summary of settlement statuses across all instruments.

    Groups the most recent entry per instrument by settlement_status.
    """
    status_counts = defaultdict(int)
    by_status = defaultdict(list)

    for inst_id, inst in DATA.items():
        entries = inst.get("entries", [])
        if not entries:
            continue
        # Most recent entry (first in list — sorted newest-first in data)
        latest = entries[0]
        s = latest.get("settlement_status", "Unknown")
        status_counts[s] += 1
        by_status[s].append(inst_id)

    return jsonify({
        "as_of": "2025-03-31",
        "status_counts": dict(status_counts),
        "instruments_by_status": {k: sorted(v) for k, v in by_status.items()},
    })


# ---------------------------------------------------------------------------
# Batch endpoint (POST)
# ---------------------------------------------------------------------------

@app.route("/v1/instruments/batch-entries", methods=["POST"])
@require_api_key
def batch_ledger_entries():
    """Fetch ledger entries for multiple instruments in a single request.

    Request body (JSON):
        {
            "instrument_ids": ["ID1", "ID2", ...],
            "as_of": "2025-03-31"          // optional
        }

    Returns a dict of instrument_id → entries (or error per instrument).
    Simulates a partial failure: if an instrument is unknown, its entry is
    returned with an error message instead of entries.
    """
    body = request.get_json(silent=True)
    if not body or "instrument_ids" not in body:
        return _error_response("Request body must include 'instrument_ids' array", 400, "BAD_REQUEST")

    instrument_ids = body["instrument_ids"]
    if not isinstance(instrument_ids, list) or len(instrument_ids) == 0:
        return _error_response("'instrument_ids' must be a non-empty array", 400, "BAD_REQUEST")

    if len(instrument_ids) > 20:
        return _error_response("Batch size limited to 20 instruments per request", 400, "BATCH_TOO_LARGE")

    as_of = body.get("as_of")
    results = {}

    for inst_id in instrument_ids:
        if inst_id not in DATA:
            results[inst_id] = {"error": {"code": "NOT_FOUND", "message": f"Instrument '{inst_id}' not found"}}
            continue

        entries = list(DATA[inst_id]["entries"])
        if as_of:
            entries = [e for e in entries if e.get("entry_date", "") <= as_of]

        results[inst_id] = {"instrument_id": inst_id, "entries": entries}

    return jsonify({
        "results": results,
        "requested": len(instrument_ids),
        "found": sum(1 for v in results.values() if "entries" in v),
        "errors": sum(1 for v in results.values() if "error" in v),
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting mock ledger API v%s on port 5000", VERSION)
    app.run(host="0.0.0.0", port=5000, debug=False)
