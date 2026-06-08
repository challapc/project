import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_dirty_number(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if '.' in value and ',' in value:
        value = value.replace('.', '').replace(',', '.')
    else:
        value = value.replace(',', '')
    try:
        return float(value)
    except:
        return None

portfolio = pd.read_csv(DATA_DIR / 'portfolio_investments.csv')
funds = pd.read_excel(DATA_DIR / 'fund_master_data.xlsx', sheet_name='funds')
fx = pd.read_excel(DATA_DIR / 'fund_master_data.xlsx', sheet_name='fx_rates')
bench = pd.read_excel(DATA_DIR / 'fund_master_data.xlsx', sheet_name='benchmarks')

with open(DATA_DIR / 'mock_api_responses.json') as f:
    api_data = json.load(f)

ledger_rows = []
for instrument_id, payload in api_data.items():
    entries = payload.get('entries', [])
    for e in entries:
        ledger_rows.append({
            'instrument_id': instrument_id,
            'entry_date': e.get('entry_date'),
            'last_valuation': parse_dirty_number(e.get('last_valuation')),
            'interest_accrued': parse_dirty_number(e.get('interest_accrued')),
            'settlement_status': e.get('settlement_status')
        })

ledger = pd.DataFrame(ledger_rows)
ledger['entry_date'] = pd.to_datetime(ledger['entry_date'])
latest = ledger.sort_values('entry_date').groupby('instrument_id').tail(1)

fx['currency'] = fx['currency_pair'].str.split('/').str[0]
fx['rate_date'] = pd.to_datetime(fx['rate_date'])
latest['fx_date'] = latest['entry_date'].dt.date.astype(str)

fx_latest = fx.sort_values('rate_date').groupby('currency').tail(1)[['currency','rate']]

merged = portfolio.merge(latest, on='instrument_id', how='left')
merged = merged.merge(fx_latest, on='currency', how='left')
merged = merged.merge(bench[['strategy','q1_2025_return_pct']], on='strategy', how='left')

merged['rate'] = merged['rate'].fillna(1)
merged['principal_usd'] = merged['principal_invested'] * merged['rate']
merged['valuation_usd'] = merged['last_valuation'].fillna(0) * merged['rate']
merged['interest_usd'] = merged['interest_accrued'].fillna(0) * merged['rate']
merged['unrealized_pnl_usd'] = merged['valuation_usd'] - merged['principal_usd']
merged['unrealized_pnl_pct'] = (merged['unrealized_pnl_usd'] / merged['principal_usd']) * 100

fund_summary = merged.groupby(['fund_code','fund_name','strategy','q1_2025_return_pct']).agg(
    total_principal_usd=('principal_usd','sum'),
    total_valuation_usd=('valuation_usd','sum'),
    total_interest_usd=('interest_usd','sum'),
    active_positions=('position_status', lambda x: (x=='Active').sum())
).reset_index()

fund_summary['unrealized_pnl_usd'] = fund_summary['total_valuation_usd'] - fund_summary['total_principal_usd']
fund_summary['unrealized_pnl_pct'] = (
    fund_summary['unrealized_pnl_usd'] / fund_summary['total_principal_usd']
) * 100

fund_totals = merged.groupby('fund_code')['valuation_usd'].sum().reset_index(name='fund_total')
merged = merged.merge(fund_totals, on='fund_code', how='left')
merged['concentration_pct'] = (merged['valuation_usd'] / merged['fund_total']) * 100
merged['concentration_flag'] = merged['concentration_pct'] > 40

instrument_cols = [
    'fund_code','instrument_id','company_name','instrument_type',
    'principal_usd','valuation_usd','unrealized_pnl_usd',
    'unrealized_pnl_pct','interest_usd','settlement_status',
    'concentration_pct','concentration_flag'
]

fund_summary.to_json(OUTPUT_DIR / 'fund_summary.json', orient='records', indent=2)
merged[instrument_cols].to_json(OUTPUT_DIR / 'instrument_details.json', orient='records', indent=2)
merged.to_csv(OUTPUT_DIR / 'cleaned_dataset.csv', index=False)

print('Pipeline completed successfully.')
