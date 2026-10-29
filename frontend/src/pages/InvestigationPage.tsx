import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, InvestigationReport, TransactionTrace } from '../api'

export function InvestigationPage() {
  const { id } = useParams<{ id: string }>()
  const [discrepancy, setDiscrepancy] = useState<any | null>(null)
  const [report, setReport] = useState<InvestigationReport | null>(null)
  const [trace, setTrace] = useState<TransactionTrace | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [resolving, setResolving] = useState(false)
  const [resolutionReason, setResolutionReason] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState('')
  const [appliedAction, setAppliedAction] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    const fetchData = async () => {
      try {
        setLoading(true)
        const discData = await api.discrepancies.get(id!)
        setDiscrepancy(discData)

        try {
          const invReport = await api.investigation.get(id!)
          setReport(invReport)
          if (invReport.trace) {
            setTrace(invReport.trace)
          }
        } catch {
          // Investigation endpoint optional fallback
        }
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [id])

  const handleApplyDraft = (action: string, reason: string) => {
    setResolutionReason(reason)
    setAppliedAction(action)
    if (discrepancy?.decision?.surviving_candidates?.length > 0) {
      setSelectedCandidate(discrepancy.decision.surviving_candidates[0].candidate_id)
    }
  }

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!discrepancy) return
    try {
      setResolving(true)
      await api.discrepancies.resolve(
        discrepancy.discrepancy_id,
        resolutionReason,
        selectedCandidate || undefined
      )
      alert('Discrepancy resolved and recorded in hash-chained audit journal.')
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

  const statusColor = (status: string) => {
    switch (status) {
      case 'MATCHED':
        return 'var(--success)'
      case 'BREAK':
      case 'SHORTFALL':
        return 'var(--danger)'
      case 'DELAYED':
        return 'var(--warning)'
      case 'ORPHAN':
        return '#a371f7'
      default:
        return 'var(--text-muted)'
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Discrepancy Investigation</h1>
          <div className="mono text-muted" style={{ fontSize: '0.875rem', marginTop: '4px' }}>
            ID: {discrepancy.discrepancy_id} | Constituent: {discrepancy.constituent_id}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="badge" style={{ fontSize: '0.875rem' }}>{discrepancy.type}</span>
          <span className={`badge ${discrepancy.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}`}>
            {discrepancy.status || 'OPEN'}
          </span>
        </div>
      </div>

      {/* Reconstructed Transaction Journey Trace */}
      {trace && (
        <div className="card" style={{ marginBottom: '24px', borderColor: 'var(--accent)' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🔍</span> Visual Transaction Journey Trace
            </h2>
            <span className="mono" style={{ fontSize: '0.8125rem', color: trace.is_closed ? 'var(--success)' : 'var(--danger)' }}>
              {trace.is_closed ? '● Reconciled Balance Closed' : '● Balance Open / Residual Detected'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '20px', padding: '12px', background: 'var(--bg)', borderRadius: 'var(--radius)' }}>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>GROSS CHARGES</div>
              <div className="mono" style={{ fontWeight: 600 }}>${trace.gross_amount}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>FEES DEDUCTED</div>
              <div className="mono" style={{ fontWeight: 600 }}>-${trace.fee_amount}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>REFUNDS</div>
              <div className="mono" style={{ fontWeight: 600 }}>-${trace.refund_amount}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>NET EXPECTED</div>
              <div className="mono" style={{ fontWeight: 600, color: 'var(--accent)' }}>${trace.net_expected}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>PAYOUT PAID</div>
              <div className="mono" style={{ fontWeight: 600 }}>${trace.net_paid}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>BANK DEPOSITED</div>
              <div className="mono" style={{ fontWeight: 600 }}>${trace.bank_deposited}</div>
            </div>
            <div>
              <div className="text-muted" style={{ fontSize: '0.75rem' }}>UNRESOLVED RESIDUAL</div>
              <div className="mono" style={{ fontWeight: 700, color: trace.residual === '0.00' ? 'var(--success)' : 'var(--danger)' }}>
                ${trace.residual}
              </div>
            </div>
          </div>

          {/* Visual trace nodes flow */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflowX: 'auto', paddingBottom: '8px' }}>
            {trace.nodes.map((node, idx) => (
              <div key={node.node_id || idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  padding: '12px',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius)',
                  border: `1px solid ${statusColor(node.status)}`,
                  minWidth: '160px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>{node.kind}</span>
                    <span style={{ fontSize: '0.6875rem', color: statusColor(node.status), fontWeight: 600 }}>{node.status}</span>
                  </div>
                  <div className="mono" style={{ fontWeight: 700, fontSize: '1rem' }}>
                    {node.amount} {node.currency}
                  </div>
                  <div className="mono text-muted" style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                    {node.reference || node.node_id}
                  </div>
                  {node.date && (
                    <div className="text-muted" style={{ fontSize: '0.6875rem' }}>{node.date}</div>
                  )}
                </div>
                {idx < trace.nodes.length - 1 && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '1.25rem', userSelect: 'none' }}>➔</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(360px, 0.8fr)' }}>
        {/* Left Column: AI Forensic Co-Pilot & Evidence */}
        <div style={{ display: 'grid', gap: '20px' }}>
          {/* AI Forensic Investigator Card */}
          {report && (
            <div className="card" style={{ border: '1px solid #388bfd' }}>
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>🤖</span> AI Forensic Co-Pilot
                </h2>
                <span className="badge" style={{ background: 'rgba(56, 139, 253, 0.15)', color: 'var(--accent)' }}>
                  Deterministic Evidence Engine
                </span>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  Ranked hypotheses based on algebraic trace analysis and transaction flow evidence:
                </div>

                <div style={{ display: 'grid', gap: '12px' }}>
                  {report.hypotheses.map(hyp => (
                    <div key={hyp.rank} style={{
                      padding: '14px',
                      background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius)',
                      borderLeft: `4px solid ${hyp.confidence === 'HIGH' ? 'var(--success)' : hyp.confidence === 'MEDIUM' ? 'var(--warning)' : 'var(--danger)'}`,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                        <div>
                          <strong style={{ fontSize: '0.9375rem' }}>#{hyp.rank} {hyp.title}</strong>
                        </div>
                        <span className={`badge ${hyp.confidence === 'HIGH' ? 'badge-success' : 'badge-warning'}`}>
                          {hyp.confidence} CONFIDENCE
                        </span>
                      </div>
                      <p style={{ fontSize: '0.8125rem', color: 'var(--text)', marginBottom: '10px' }}>
                        {hyp.description}
                      </p>

                      <div style={{ fontSize: '0.75rem', marginBottom: '8px' }}>
                        <strong style={{ color: 'var(--success)' }}>Supporting Evidence:</strong>
                        <ul style={{ paddingLeft: '18px', marginTop: '4px', color: 'var(--text-muted)' }}>
                          {hyp.supporting_evidence.map((ev, i) => (
                            <li key={i}>{ev}</li>
                          ))}
                        </ul>
                      </div>

                      {hyp.contradicting_evidence && hyp.contradicting_evidence.length > 0 && (
                        <div style={{ fontSize: '0.75rem', marginBottom: '8px' }}>
                          <strong style={{ color: 'var(--danger)' }}>Contradicting Evidence:</strong>
                          <ul style={{ paddingLeft: '18px', marginTop: '4px', color: 'var(--text-muted)' }}>
                            {hyp.contradicting_evidence.map((ev, i) => (
                              <li key={i}>{ev}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '8px', borderTop: '1px solid var(--border)' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          Recommended: <span className="mono" style={{ color: 'var(--accent)' }}>{hyp.recommended_action}</span>
                        </span>
                        {discrepancy.status === 'OPEN' && (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleApplyDraft(hyp.recommended_action, report.draft_resolution?.reason || hyp.description)}
                          >
                            Apply Draft Resolution
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {discrepancy.status === 'OPEN' && report.draft_resolution && (
                <div style={{
                  padding: '12px',
                  background: 'rgba(56, 139, 253, 0.08)',
                  borderRadius: 'var(--radius)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--accent)' }}>
                      Quick One-Click AI Pre-Fill:
                    </span>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Action: {report.draft_resolution.action} ({report.draft_resolution.resolved_by})
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn btn-primary btn-sm"
                    onClick={() => handleApplyDraft(report.draft_resolution.action, report.draft_resolution.reason)}
                  >
                    Accept AI Draft
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Raw Discrepancy Evidence & Contributing Records */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Contributing Records & Decision Metadata</h2>
            </div>
            <div className="mono" style={{ marginBottom: '16px', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)' }}>
              {discrepancy.reason}
            </div>

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
                <div className="card" style={{ padding: '12px', borderColor: 'var(--success)' }}>
                  <strong style={{ color: 'var(--success)' }}>Matched Candidate</strong>
                  <div className="mono" style={{ marginTop: '8px' }}>
                    ID: {discrepancy.decision.matched_candidate.candidate_id} | Amount: {discrepancy.decision.matched_candidate.amount} {discrepancy.decision.matched_candidate.currency}
                  </div>
                </div>
              )}
              {discrepancy.decision && discrepancy.decision.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1 && (
                <div className="card" style={{ borderColor: 'var(--warning)' }}>
                  <h4 style={{ color: 'var(--warning)', marginBottom: '8px' }}>⚠ Ambiguous Match - Multiple Candidates</h4>
                  <p className="text-muted" style={{ marginBottom: '12px', fontSize: '0.8125rem' }}>
                    {discrepancy.decision.surviving_candidates.length} equally valid candidates. Manual tie-breaker selection required.
                  </p>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {discrepancy.decision.surviving_candidates.map((c: any, i: number) => (
                      <div key={i} className="card" style={{ padding: '10px' }}>
                        <div className="mono" style={{ fontSize: '0.8125rem' }}>
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

        {/* Right Column: Resolution Panel & Audit Journal */}
        <div style={{ display: 'grid', gap: '20px', alignContent: 'start' }}>
          {/* Resolution Form */}
          {discrepancy.status === 'OPEN' ? (
            <div className="card" style={{ borderColor: 'var(--accent)' }}>
              <div className="card-header">
                <h3 className="card-title">Resolve Discrepancy</h3>
                {appliedAction && (
                  <span className="badge" style={{ background: 'rgba(56, 139, 253, 0.2)', color: 'var(--accent)' }}>
                    Action: {appliedAction}
                  </span>
                )}
              </div>
              <form onSubmit={handleResolve}>
                <div className="form-group" style={{ marginBottom: '16px' }}>
                  <label className="label">Resolution Justification Reason (required)</label>
                  <textarea
                    className="textarea"
                    rows={4}
                    value={resolutionReason}
                    onChange={e => setResolutionReason(e.target.value)}
                    placeholder="Document forensic justification for resolving this break..."
                    required
                  />
                </div>
                {discrepancy.decision?.surviving_candidates && discrepancy.decision.surviving_candidates.length > 1 && (
                  <div className="form-group" style={{ marginBottom: '16px' }}>
                    <label className="label">Selected Candidate (required for ambiguous match)</label>
                    <select
                      className="select"
                      value={selectedCandidate}
                      onChange={e => setSelectedCandidate(e.target.value)}
                      required
                    >
                      <option value="">Select candidate tie-breaker...</option>
                      {discrepancy.decision.surviving_candidates.map((c: any, i: number) => (
                        <option key={i} value={c.candidate_id}>
                          {c.candidate_id} — {c.amount} {c.currency} ({c.date})
                        </option>
                      ))}
                    </select>
                  </div>
                )}
                <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!resolutionReason.trim() || resolving}
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    {resolving ? 'Recording in Ledger...' : 'Commit Immutable Resolution'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="card" style={{ borderColor: 'var(--success)' }}>
              <div className="card-header">
                <h3 className="card-title" style={{ color: 'var(--success)' }}>✓ Discrepancy Resolved</h3>
              </div>
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>
                This discrepancy has been resolved and committed to the hash-chained audit journal.
              </p>
            </div>
          )}

          {/* Resolution History / Audit Ledger Record */}
          <div className="card">
            <h3 style={{ marginBottom: '12px' }}>Audit Journal History</h3>
            {discrepancy.resolution_history && discrepancy.resolution_history.length > 0 ? (
              discrepancy.resolution_history.map((r: any, i: number) => (
                <div key={i} style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong style={{ color: 'var(--success)' }}>{r.status || 'RESOLVED'}</strong>
                    <span className="text-muted" style={{ fontSize: '0.75rem' }}>{r.timestamp || ''}</span>
                  </div>
                  <p className="mono" style={{ fontSize: '0.8125rem' }}>{r.reason}</p>
                  {r.resolved_by && (
                    <div className="text-muted" style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                      By: <span className="mono">{r.resolved_by}</span>
                    </div>
                  )}
                  {r.selected_candidate && (
                    <div className="mono text-muted" style={{ fontSize: '0.75rem', marginTop: '2px' }}>
                      Selected Candidate: {r.selected_candidate}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-muted" style={{ fontSize: '0.875rem' }}>No resolution records in audit journal yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvestigationPage
