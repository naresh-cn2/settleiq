import { useEffect, useState } from 'react'
import { api } from '../api'

export function MetricsPage() {
  const [metrics, setMetrics] = useState<any | null>(null)
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [runsData, metricsData] = await Promise.all([
          api.runs.list(),
          Promise.resolve(null),
        ])
        setRuns(runsData.runs)
        setMetrics(metricsData)
      } catch (err: any) {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleRunChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const runId = e.target.value
    setSelectedRun(runId)
    try {
      const m = await api.runs.metrics(runId)
      setMetrics(m)
    } catch (err: any) {
      // eslint-disable-next-line no-alert
      alert(err.message)
    }
  }

  if (loading) return <div className="loading">Loading metrics...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Metrics</h1>
      </div>

      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: '280px 1fr' }}>
        <div className="card" style={{ height: 'fit-content' }}>
          <h2 className="card-title">Runs</h2>
          <select
            className="input"
            value={selectedRun || ''}
            onChange={handleRunChange}
            style={{ width: '100%', marginBottom: '16px' }}
          >
            <option value="">Select a run</option>
            {runs.map((r: any) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id.slice(0, 16)}… — {r.numerator}/{r.denominator} ({(r.rate * 100).toFixed(1)}%)
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Auto-Match Rate</h2>
              <span className="badge badge-neutral">v{metrics?.methodology_version || '—'}</span>
            </div>
            <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--accent)', fontFamily: 'var(--font-mono)', marginTop: '8px' }}>
              {metrics ? (metrics.rate * 100).toFixed(2) + '%' : '—'}
            </div>
            <div className="text-muted" style={{ marginTop: '8px', fontSize: '0.8125rem' }}>
              {metrics?.numerator || 0} / {metrics?.denominator || 0} eligible records
            </div>
            <div style={{ marginTop: '16px', fontSize: '0.8125rem' }}>
              <div style={{ marginBottom: '4px' }}>
                <strong>Numerator:</strong> <span className="mono">{metrics?.numerator || 0}</span> deterministic matches
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Denominator:</strong> <span className="mono">{metrics?.denominator || 0}</span> eligible records
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Ambiguous:</strong> <span className="mono">{metrics?.ambiguous || 0}</span>
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Rule conflicts:</strong> <span className="mono">{metrics?.conflict || 0}</span>
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Insufficient evidence:</strong> <span className="mono">{metrics?.insufficient || 0}</span>
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Human-confirmed:</strong> <span className="mono">{metrics?.human_confirmed || 0}</span>
              </div>
              <div style={{ marginBottom: '4px' }}>
                <strong>Quarantined:</strong> <span className="mono">{metrics?.quarantined || 0}</span>
              </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
              <h3 style={{ marginBottom: '12px' }}>Methodology</h3>
              <div style={{ fontSize: '0.8125rem', lineHeight: '1.6' }}>
                <div><strong>Numerator:</strong> Deterministic matches — records for which exactly one candidate survived a declared rule, or two or more rules resolved to the same candidate.</div>
                <div style={{ marginTop: '8px' }}><strong>Denominator:</strong> Eligible records — every charge and payout constituent presented to the matching engine, plus every bank deposit and processor-side record that produced a presence/absence break. A record quarantined at ingestion is excluded from the denominator and reported separately.</div>
                <div style={{ marginTop: '8px' }}><strong>Human confirmations:</strong> Counted separately from deterministic matches, never silently merged into the rate.</div>
                <div style={{ marginTop: '8px' }}><strong>Window:</strong> A declared input recorded in the run digest, never sampled from ambient time.</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MetricsPage