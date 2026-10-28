import { useEffect, useState } from 'react'
import { api } from '../api'

export function HistoryPage() {
  const [runs, setRuns] = useState<any[]>([])
  const [selectedRun, setSelectedRun] = useState<string | null>(null)
  const [comparison, setComparison] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const data = await api.runs.list()
        setRuns(data.runs)
      } catch (err: any) {
        // ignore
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleCompare = async (runId: string) => {
    if (!selectedRun) {
      setSelectedRun(runId)
      return
    }
    if (runId === selectedRun) return
    try {
      const [a, b] = await Promise.all([
        api.runs.export(selectedRun),
        api.runs.export(runId),
      ])
      setComparison({ a, b, idA: selectedRun, idB: runId })
      setSelectedRun(null)
    } catch (err: any) {
      alert(err.message)
    }
  }

  if (loading) return <div className="loading">Loading history...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Run History & Diff</h1>
      </div>

      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: '280px 1fr' }}>
        <div className="card" style={{ height: 'fit-content' }}>
          <h2 className="card-title">Runs</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {runs.map((r: any) => (
              <button
                key={r.run_id}
                className={`btn btn-ghost btn-sm ${r.run_id === comparison?.idA || r.run_id === comparison?.idB ? 'btn-primary' : ''}`}
                style={{ justifyContent: 'flex-start', textAlign: 'left' }}
                onClick={() => handleCompare(r.run_id)}
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
                <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  <h3 style={{ marginBottom: '8px' }}>Select two runs to compare</h3>
                  <p>Click a run in the list to select the first, then click another to compare.</p>
                </div>
              </div>
            )}
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