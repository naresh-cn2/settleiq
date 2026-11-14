import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

interface RunSummary {
  run_id: string
  input_digest: string
  rule_version: string
  schema_version: string
  numerator: number
  denominator: number
  rate: number
  discrepancy_count: number
  status: string
  declared_window?: string
}

export function OverviewPage() {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [aggregates, setAggregates] = useState<{
    totalRuns: number
    totalTransactions: number
    totalMatched: number
    totalUnmatched: number
    matchRate: number
    totalDiscrepancies: number
    openDiscrepancies: number
    totalDiscrepancyAmount: number
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await api.runs.list()
        const runList: RunSummary[] = data.runs
        setRuns(runList)

        // Compute aggregate metrics across all runs.
        let totalTransactions = 0
        let totalMatched = 0
        let totalDiscrepancies = 0
        let openDiscrepancies = 0
        let totalDiscrepancyAmount = 0

        for (const run of runList) {
          totalTransactions += run.denominator
          totalMatched += run.numerator
          totalDiscrepancies += run.discrepancy_count || 0

          // Fetch each run's discrepancies to count open ones and sum amounts.
          try {
            const discs = await api.discrepancies.list({ run_id: run.run_id })
            for (const d of discs.discrepancies) {
              if (d.status !== 'RESOLVED') openDiscrepancies += 1
              // Parse the leading amount from the reason string when present.
              const m = String(d.reason || '').match(/([0-9]+(?:\.[0-9]+)?)\|/)
              if (m) totalDiscrepancyAmount += parseFloat(m[1])
            }
          } catch {
            // Best-effort: discrepancies may not be available for every run.
          }
        }

        const matchRate =
          totalTransactions > 0 ? totalMatched / totalTransactions : 0

        setAggregates({
          totalRuns: runList.length,
          totalTransactions,
          totalMatched,
          totalUnmatched: totalTransactions - totalMatched,
          matchRate,
          totalDiscrepancies,
          openDiscrepancies,
          totalDiscrepancyAmount,
        })
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleViewRun = (runId: string) => {
    navigate(`/discrepancies?run_id=${runId}`)
  }

  if (loading) return <div className="loading">Loading overview...</div>
  if (error) return <div className="error">Failed to load overview: {error}</div>
  if (!aggregates) return <div className="empty">No overview data available</div>

  const a = aggregates

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reconciliation Overview</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '4px' }}>
            Aggregate view across all reconciliation runs. Synthetic demonstration data only.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/')}
            data-testid="nav-runs"
          >
            Runs
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/discrepancies')}
            data-testid="nav-discrepancies"
          >
            Discrepancies
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
        <div className="card" style={{ borderTop: `3px solid var(--accent)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Transactions
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px' }}>
            {a.totalTransactions}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Eligible records across all runs
          </div>
        </div>
        <div className="card" style={{ borderTop: `3px solid var(--success)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Matched Transactions
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--success)', marginTop: '8px' }}>
            {a.totalMatched}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Deterministically matched
          </div>
        </div>
        <div className="card" style={{ borderTop: `3px solid var(--warning)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Match Rate
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px' }}>
            {(a.matchRate * 100).toFixed(1)}%
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            {a.totalMatched} / {a.totalTransactions}
          </div>
        </div>
        <div className="card" style={{ borderTop: `3px solid var(--danger)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Open Discrepancies
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--danger)', marginTop: '8px' }}>
            {a.openDiscrepancies}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            of {a.totalDiscrepancies} total breaks
          </div>
        </div>
      </div>

      {/* Financial Impact Row */}
      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
        <div className="card" style={{ borderTop: `3px solid var(--accent)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Discrepancy Amount
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px' }}>
            ${a.totalDiscrepancyAmount.toFixed(2)}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Sum of break amounts
          </div>
        </div>
        <div className="card" style={{ borderTop: `3px solid var(--success)` }}>
          <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Reconciliation Runs
          </div>
          <div className="mono" style={{ fontSize: '1.75rem', fontWeight: 700, marginTop: '8px' }}>
            {a.totalRuns}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
            Completed runs
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 className="card-title">Recent Reconciliation Runs</h2>
          {runs.length > 0 && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate('/runs')}
              data-testid="view-all-runs"
            >
              View All Runs
            </button>
          )}
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Window</th>
                <th>Status</th>
                <th>Transactions</th>
                <th>Matched</th>
                <th>Rate</th>
                <th>Discrepancies</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-muted" data-testid="runs-empty">
                    No reconciliation runs yet. Start with the public demo or import data.
                  </td>
                </tr>
              )}
              {runs.slice(0, 10).map((run) => (
                <tr key={run.run_id} data-testid="run-row" style={{ cursor: 'pointer' }} onClick={() => handleViewRun(run.run_id)}>
                  <td className="mono text-truncate">{run.run_id.slice(0, 16)}…</td>
                  <td className="mono text-muted">{run.declared_window || '—'}</td>
                  <td>
                    <span className={`badge ${run.status === 'COMPLETED' ? 'badge-low' : 'badge-neutral'}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="mono">{run.denominator}</td>
                  <td className="mono">{run.numerator}</td>
                  <td>{(run.rate * 100).toFixed(2)}%</td>
                  <td>{run.discrepancy_count || 0}</td>
                  <td>
                    <span className="mono text-muted" style={{ fontSize: '0.8125rem' }} data-testid={`run-view-${run.run_id.slice(0, 8)}`}>
                      View
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default OverviewPage
