import { useEffect, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'

ModuleRegistry.registerModules([AllCommunityModule])

import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'

export default function App() {
  const [funds, setFunds] = useState([])
  const [instruments, setInstruments] = useState([])

  useEffect(() => {
    fetch('http://localhost:5000/api/fund-summary')
      .then(r => r.json())
      .then(setFunds)

    fetch('http://localhost:5000/api/instrument-details')
      .then(r => r.json())
      .then(setInstruments)
  }, [])

  const totalValuation =
    funds.reduce(
      (sum, item) => sum + Number(item.total_valuation_usd || 0),
      0
    )

  const totalPnL =
    funds.reduce(
      (sum, item) => sum + Number(item.unrealized_pnl_usd || 0),
      0
    )

  const totalPositions =
    funds.reduce(
      (sum, item) => sum + Number(item.active_positions || 0),
      0
    )

  const totalInterest =
    funds.reduce(
      (sum, item) => sum + Number(item.total_interest_usd || 0),
      0
    )

  const currencyFormatter = params => {
    const value = Number(params.value || 0)

    if (Math.abs(value) >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`
    }

    return `$${value.toLocaleString()}`
  }

  const percentFormatter = params =>
    `${Number(params.value || 0).toFixed(2)}%`

  const defaultColDef = {
    sortable: true,
    filter: true,
    floatingFilter: true,
    resizable: true
  }

  return (
    <div className='page'>
      <div className='header'>
        <h1>Sixth Street Investment Analytics Dashboard</h1>
        <p>
          Portfolio Valuation, Exposure, Risk & Performance Overview
        </p>
      </div>

      <div className='kpi-container'>
        <div className='kpi-card'>
          <div className='kpi-label'>Funds</div>
          <div className='kpi-value'>{funds.length}</div>
        </div>

        <div className='kpi-card'>
          <div className='kpi-label'>Portfolio Valuation</div>
          <div className='kpi-value'>
            ${(totalValuation / 1000000).toFixed(1)}M
          </div>
        </div>

        <div className='kpi-card'>
          <div className='kpi-label'>Unrealized P&L</div>
          <div
            className={
              totalPnL >= 0
                ? 'kpi-value positive'
                : 'kpi-value negative'
            }
          >
            ${(totalPnL / 1000000).toFixed(1)}M
          </div>
        </div>

        <div className='kpi-card'>
          <div className='kpi-label'>Active Positions</div>
          <div className='kpi-value'>{totalPositions}</div>
        </div>

        <div className='kpi-card'>
          <div className='kpi-label'>Accrued Interest</div>
          <div className='kpi-value'>
            ${(totalInterest / 1000000).toFixed(1)}M
          </div>
        </div>
      </div>

      <div className='section-title'>
        Fund Summary
      </div>

      <div className='ag-theme-quartz grid'>
        <AgGridReact
          rowData={funds}
          defaultColDef={defaultColDef}
          columnDefs={[
            {
              field: 'fund_code'
            },
            {
              field: 'fund_name'
            },
            {
              field: 'strategy'
            },
            {
              field: 'total_principal_usd',
              headerName: 'Principal',
              valueFormatter: currencyFormatter
            },
            {
              field: 'total_valuation_usd',
              headerName: 'Valuation',
              valueFormatter: currencyFormatter
            },
            {
              field: 'total_interest_usd',
              headerName: 'Accrued Interest',
              valueFormatter: currencyFormatter
            },
            {
              field: 'unrealized_pnl_usd',
              headerName: 'P&L',
              valueFormatter: currencyFormatter,
              cellStyle: params => ({
                color:
                  params.value >= 0
                    ? '#16a34a'
                    : '#dc2626',
                fontWeight: 'bold'
              })
            },
            {
              field: 'unrealized_pnl_pct',
              headerName: 'P&L %',
              valueFormatter: percentFormatter
            },
            {
              field: 'q1_2025_return_pct',
              headerName: 'Benchmark Return',
              valueFormatter: percentFormatter
            },
            {
              field: 'active_positions'
            }
          ]}
        />
      </div>

      <div className='section-title'>
        Instrument Detail
      </div>

      <div className='ag-theme-quartz grid'>
        <AgGridReact
          rowData={instruments}
          defaultColDef={defaultColDef}
          columnDefs={[
            {
              field: 'fund_code'
            },
            {
              field: 'instrument_id'
            },
            {
              field: 'company_name'
            },
            {
              field: 'valuation_usd',
              headerName: 'Valuation',
              valueFormatter: currencyFormatter
            },
            {
              field: 'unrealized_pnl_usd',
              headerName: 'P&L',
              valueFormatter: currencyFormatter,
              cellStyle: params => ({
                color:
                  params.value >= 0
                    ? '#16a34a'
                    : '#dc2626',
                fontWeight: 'bold'
              })
            },
            {
              field: 'concentration_pct',
              headerName: 'Concentration',
              valueFormatter: percentFormatter,
              cellStyle: params => {
                if (params.value > 25) {
                  return {
                    backgroundColor: '#fef2f2',
                    color: '#dc2626',
                    fontWeight: 'bold'
                  }
                }
                return null
              }
            },
            {
              field: 'concentration_flag'
            }
          ]}
        />
      </div>
    </div>
  )
}