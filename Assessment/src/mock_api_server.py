from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'outputs'

@app.route('/health')
def health():
    return {'status': 'ok'}

@app.route('/api/fund-summary')
def fund_summary():
    with open(OUT / 'fund_summary.json') as f:
        return jsonify(json.load(f))

@app.route('/api/instrument-details')
def instrument_details():
    with open(OUT / 'instrument_details.json') as f:
        return jsonify(json.load(f))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
