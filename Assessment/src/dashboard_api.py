from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"


@app.route("/api/fund-summary")
def fund_summary():
    with open(OUTPUT_DIR / "fund_summary.json", "r") as f:
        return jsonify(json.load(f))


@app.route("/api/instrument-details")
def instrument_details():
    with open(OUTPUT_DIR / "instrument_details.json", "r") as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)