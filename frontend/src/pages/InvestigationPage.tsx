import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

export function InvestigationPage() {
  const { id } = useParams<{ id: string }>()
  const [discrepancy, setDiscrepancy] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState(false)
  const [resolutionReason, setResolutionReason] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState('')

  useEffect(() => {
    if (!id) return
    const fetch = async () => {
      try {
        setLoading(true)
        const data = await api.discrepancies.get(id!)
        setDiscrepancy(data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [id])

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!discrepancy) return
    try {
      setResolving(true)
      await api.discrepancies.resolve(discrepancy.discrepancy_id, resolutionReason, selectedCandidate || undefined)
      alert('Discrepancy resolved')
      window.location.reload()
    } catch (err: any) {
      alert(err.message)
    } finally {
      setResolving(false)
    }
  }

  if (loading) return <div className="loading">Loading investigation...</div>
  if (error) return <div className="error">Failed to load investigation: {error}</div>
  if (!discrepancy) return <div className="empty">Discrepancy not found</div>

  const severityColors: Record<string, string> = {
    HIGH: 'badge-high',
    MEDIUM: 'badge-medium',
    LOW: 'badge-low',
    UNKNOWN: 'badge-neutral',
  }

  const candidate = discrepancy.contributing_records?.[0] || discrepancy.decision?.matched_candidate

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Investigation</h1>
        <span className="badge">{discrepancy.type}</span>
      </div>

      <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: '1fr 380px' }}>
        <div>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Discrepancy Details</h2>
              <span className={`badge ${['HIGH','MEDIUM','LOW','UNKNOWN'].includes(discrepancy.severity) ? `badge-${discrepancy.severity.toLowerCase()}` : 'badge-neutral'}`}>
                {discrepancy.severity}
              </span>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong className="mono">{discrepancy.discrepancy_id}</strong>
              <span className="text-muted" style={{ marginLeft: '12px' }}>
                Type: {discrepancy.type} | Constituent: {discrepancy.constituent_kind}:{discrepancy.constituent_id}
              </span>
            </div>
            <div className="mono" style={{ marginBottom: '16px', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)' }}>
              {discrepancy.reason}
            </div>

            <h3 style={{ marginBottom: '8px' }}>Evidence</h3>
            <div style={{ display: 'grid', gap: '12px' }}>
              {discrepancy.contributing_records && discrepancy.contributing_records.map((c: any, i: number) => (
                <div key={i} className="card" style={{ padding: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong>{c.kind}</strong>
                    <span className="mono">{c.candidate_id}</span>
                  </div>
                  <div className="mono" style={{ fontSize: '0.8125rem' }}>
                    Amount: {c.amount} {c.currency} | Date: {c.date} | Ref: {c.reference}
                  </div>
                </div>
              ))}
              {discrepancy.decision && discrepancy.decision.matched_candidate && (
                <div className="card" style={{ padding: '12px' }}>
                  <strong>Matched Candidate</strong>
                  <div className="mono" style={{ marginTop: '8px' }}>
                    ID: {discrepancy.decision.matched_candidate.candidate_id} | Amount: {discrepancy.decision.matched_candidate.amount} {discrepancy.decision.matched_candidate.currency}
                  </div>
                </div>
              )}
            </div>

            {discrepancy.decision && discrepancy.decision.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1 && (
              <div className="card" style={{ marginTop: '16px', borderColor: 'var(--warning)' }}>
                <h4 style={{ color: 'var(--warning)', marginBottom: '8px' }}>⚠ Ambiguous Match - Multiple Candidates</h4>
                <p className="text-muted" style={{ marginBottom: '12px' }}>
                  {discrepancy.decision.surviving_candidates.length} equally valid candidates. No tie-break performed.
                </p>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {discrepancy.decision.surviving_candidates.map((c: any, i: number) => (
                    <div key={i} className="card" style={{ padding: '12px' }}>
                      <div className="mono">
                        {c.candidate_id} | {c.amount} {c.currency} | {c.date} | Ref: {c.reference}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="card" style={{ marginTop: '16px' }}>
            <h3>Resolution History</h3>
            {discrepancy.resolution_history && discrepancy.resolution_history.length > 0 ? (
              discrepancy.resolution_history.map((r: any, i: number) => (
                <div key={i} style={{ padding: '12px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong>{r.status || 'Resolved'}</strong>
                    <span className="text-muted">{r.timestamp || ''}</span>
                  </div>
                  <p className="mono" style={{ fontSize: '0.8125rem' }}>{r.reason}</p>
                  {r.selected_candidate && <p className="mono text-muted" style={{ fontSize: '0.75rem', marginTop: '4px' }}>Selected: {r.selected_candidate}</p>}
                </div>
              ))
            ) : (
              <p className="text-muted">No resolution recorded yet</p>
            )}
          </div>

          {discrepancy.status === 'OPEN' && (
            <div className="card" style={{ marginTop: '16px' }}>
              <h3>Resolve Discrepancy</h3>
              <form onSubmit={handleResolve}>
                <div className="form-group">
                  <label className="label">Resolution Reason (required)</label>
                  <textarea
                    className="textarea"
                    value={resolutionReason}
                    onChange={e => setResolutionReason(e.target.value)}
                    placeholder="Explain why this discrepancy is resolved..."
                    required
                  />
                </div>
                {discrepancy.decision?.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1 && (
                  <div className="form-group">
                    <label className="label">Selected Candidate (required for ambiguous)</label>
                    <select
                      className="select"
                      value={selectedCandidate}
                      onChange={e => setSelectedCandidate(e.target.value)}
                      required={discrepancy.decision?.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1}
                    >
                      <option value="">Select candidate...</option>
                      {discrepancy.decision.surviving_candidates.map((c: any, i: number) => (
                        <option key={i} value={c.candidate_id}>
                          {c.candidate_id} — {c.amount} {c.currency} ({c.date})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                  <button type="submit" className="btn btn-primary" disabled={!resolutionReason.trim() || resolving}>
                    {resolving ? 'Resolving...' : 'Mark Resolved'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        <div>
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Related Records</h2>
              <span className="badge">{discrepancy.type}</span>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <strong className="mono">{discrepancy.discrepancy_id}</strong>
            </div>
            <div style={{ display: 'grid', gap: '12px' }}>
              {discrepancy.contributing_records && discrepancy.contributing_records.map((c: any, i: number) => (
                <div key={i} className="card" style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong>{c.kind}</strong>
                    <span className="mono">{c.candidate_id}</span>
                  </div>
                  <div className="mono" style={{ fontSize: '0.8125rem' }}>
                    Amount: {c.amount} {c.currency} | Date: {c.date} | Ref: {c.reference}
                  </div>
                </div>
              ))}
              {discrepancy.decision?.matched_candidate && (
                <div className="card" style={{ borderColor: 'var(--success)' }}>
                  <h4 style={{ color: 'var(--success)', marginBottom: '8px' }}>Matched Candidate</h4>
                  <div className="mono">
                    {discrepancy.decision.matched_candidate?.candidate_id} | {discrepancy.decision.matched_candidate?.amount} {discrepancy.decision.matched_candidate?.currency}
                  </div>
                </div>
              )}
              {discrepancy.decision && discrepancy.decision.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1 && (
                <div style={{ marginTop: '16px' }}>
                  <h4 style={{ color: 'var(--warning)', marginBottom: '8px' }}>⚠ Ambiguous — {discrepancy.decision.surviving_candidates.length} Candidates</h4>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {discrepancy.decision.surviving_candidates.map((c: any, i: number) => (
                      <div key={i} className="card" style={{ padding: '12px' }}>
                        <div className="mono">
                          {c.candidate_id} | {c.amount} {c.currency} | {c.date} | Ref: {c.reference}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvestigationPage