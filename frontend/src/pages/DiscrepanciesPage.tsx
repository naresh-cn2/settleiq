import { useEffect, useState } from 'react'
import { api } from '../api'

export function DiscrepanciesPage() {
  const [discrepancies, setDiscrepancies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterType, setFilterType] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')

  const fetchDiscrepancies = async () => {
    try {
      setLoading(true)
      const data = await api.discrepancies.list({ type: filterType || undefined, severity: filterSeverity || undefined })
      setDiscrepancies(data.discrepancies)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDiscrepancies()
  }, [filterType, filterSeverity])

  const severityColors: Record<string, string> = {
    HIGH: 'badge-high',
    MEDIUM: 'badge-medium',
    LOW: 'badge-low',
    UNKNOWN: 'badge-neutral',
  }

  if (loading) return <div className="loading">Loading discrepancies...</div>
  if (error) return <div className="error">Failed to load discrepancies: {error}</div>

  const types = [...new Set(discrepancies.map(d => d.type))].sort()
  const severities = ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Discrepancies</h1>
      </div>

      <div className="card" style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              className="input"
              style={{ width: 'auto', minWidth: '180px' }}
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
            >
              <option value="">All Types</option>
              {types.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select
              className="input"
              style={{ width: 'auto', minWidth: '140px' }}
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              {severities.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <span className="text-muted">{discrepancies.length} discrepancies</span>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Constituent</th>
                <th>Age (days)</th>
                <th>Status</th>
                <th>Reason</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {discrepancies.map((d: any) => (
                <tr key={d.discrepancy_id}>
                  <td className="mono text-truncate">{d.discrepancy_id}</td>
                  <td><span className="badge">{d.type}</span></td>
                  <td><span className={`badge ${severityColors[d.severity] || 'badge-neutral'}`}>{d.severity}</span></td>
                  <td className="mono text-truncate">{d.constituent_kind}:{d.constituent_id}</td>
                  <td>{d.age_days}</td>
                  <td><span className={`badge ${d.status === 'RESOLVED' ? 'badge-low' : 'badge-neutral'}`}>{d.status}</span></td>
                  <td className="text-truncate" style={{ maxWidth: '300px' }} title={d.reason}>{d.reason}</td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => window.location.href = `/discrepancies/${d.discrepancy_id}`}
                    >
                      Investigate
                    </button>
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

export default DiscrepanciesPage