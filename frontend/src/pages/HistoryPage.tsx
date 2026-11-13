import { useEffect, useState } from 'react'
import { api } from '../api'

interface HistoryEntry {
  sequence: number
  run_id: string
  event: string
  timestamp: string
  actor: string
  detail: string
  discrepancy_id?: string
}

export function HistoryPage() {
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [comparison, setComparison] = useState<any | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadHistory = async (runId: string) => {
    try {
      setHistoryLoading(true)
      const data = await api.runs.history(runId)
      setHistory(data.entries)
    } catch (err: any) {
      setError(err.message)
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await api.runs.list()
        setRuns(data.runs)
        const first = data.runs[0]
        if (first) {
          setSelectedRun(first.run_id)
          await loadHistory(first.run_id)
        }
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleCompare = async (runId: string) => {
    setSelectedRun(runId)
    await loadHistory(runId)
    if (!selectedRun || runId === selectedRun) {
      return
    }
    try {
      setError(null)
      const [a, b] = await Promise.all([
        api.runs.export(selectedRun),
        api.runs.export(runId),
      ])
      setComparison({ a, b, idA: selectedRun, idB: runId })
    } catch (err: any) {
      setError(err.message)
    }
  }

  if (loading) return <div className="loading">Loading history...</div>

  return (
    <div className="page" data-testid="history-page">
      <div className="page-header">
        <h1 className="page-title">Run History & Diff</h1>
      </div>

      {error && <div className="error" style={{ marginBottom: '16px' }}>{error}</div>}

      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: '280px 1fr' }}>
        <div className="card" style={{ height: 'fit-content' }}>
          <h2 className="card-title">Runs</h2>
          {runs.length === 0 && (
            <p className="text-muted" data-testid="history-empty">
              No runs recorded yet.
            </p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {runs.map((r: any) => (
              <button
                key={r.run_id}
                className={`btn btn-ghost btn-sm ${r.run_id === comparison?.idA || r.run_id === comparison?.idB ? 'btn-primary' : ''}`}
                style={{ justifyContent: 'flex-start', textAlign: 'left' }}
                onClick={() => handleCompare(r.run_id)}
                data-testid="history-run"
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span className="mono">{r.run_id.slice(0, 16)}…</span>
                  <span className="text-muted" style={{ fontSize: '0.6875rem' }}>
                    {r.numerator}/{r.denominator} ({(r.rate * 100).toFixed(1)}%)
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {comparison ? (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Comparison</h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className="badge badge-primary">{comparison.idA.slice(0, 12)}…</span>
                  <span className="text-muted" style={{ alignSelf: 'center' }}>vs</span>
                  <span className="badge badge-primary">{comparison.idB.slice(0, 12)}…</span>
                </div>
              </div>
              <pre className="diff" style={{ maxHeight: '500px', overflow: 'auto' }}>
{formatDiff(comparison.a, comparison.b)}
</pre>
              </div>
            ) : (
              <div className="card">
                <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  <h3 style={{ marginBottom: '8px' }}>Select two runs to compare</h3>
                  <p>Click a different run in the list to compare it with the selected run.</p>
                </div>
              </div>
            )}

          <div className="card" data-testid="history-timeline">
            <div className="card-header">
              <h2 className="card-title">Audit Timeline</h2>
              {selectedRun && (
                <span className="badge badge-neutral mono">{selectedRun.slice(0, 12)}…</span>
              )}
            </div>
            {historyLoading ? (
              <p className="text-muted">Loading history...</p>
            ) : history.length === 0 ? (
              <p className="text-muted">No history entries recorded for this run.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {history.map(entry => (
                  <div
                    key={`${entry.sequence}-${entry.event}`}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '32px 1fr',
                      gap: '12px',
                      alignItems: 'start',
                    }}
                    data-testid="history-entry"
                  >
                    <div className="mono text-muted" style={{ fontSize: '0.75rem' }}>
                      #{entry.sequence}
                    </div>
                    <div>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <strong className="mono" style={{ fontSize: '0.8125rem' }}>{entry.event}</strong>
                        <span className="badge badge-neutral">{entry.actor}</span>
                        {entry.timestamp && (
                          <span className="text-muted" style={{ fontSize: '0.6875rem' }}>{entry.timestamp}</span>
                        )}
                      </div>
                      <p className="text-muted" style={{ fontSize: '0.8125rem', marginTop: '2px' }}>
                        {entry.detail}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function formatDiff(a: any, b: any): string {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)])
  const diffs: string[] = []
  for (const key of keys) {
    const av = JSON.stringify(a[key])
    const bv = JSON.stringify(b[key])
    if (av !== bv) {
      diffs.push(`${key}:\n  - ${av}\n  + ${bv}`)
    }
  }
  return diffs.length ? diffs.join('\n\n') : 'No differences'
}

export default HistoryPage
