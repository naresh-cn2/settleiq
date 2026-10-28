import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { Run } from './types'

export function RunsPage() {
  const [runs, setRuns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)

  const fetchRuns = async () => {
    try {
      setLoading(true)
      const data = await api.runs.list()
      setRuns(data.runs)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRuns()
  }, [])

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const formDataObj = Object.fromEntries(formData.entries())

    const chargeId = `ch_${Date.now()}`
    const payoutId = `po_${Date.now()}`
    const depositId = `bd_${Date.now()}`
    const batch = `sb_${Date.now()}`

    const payload = {
      records: [
        {
          kind: 'charge',
          records: [{
            id: chargeId,
            amount: formDataObj.charge_amount,
            currency: formDataObj.currency,
            created: new Date().toISOString().split('T')[0],
            batch,
          }]
        },
        {
          kind: 'payout',
          records: [{
            id: payoutId,
            amount: formDataObj.payout_amount,
            currency: formDataObj.currency,
            arrival_date: new Date().toISOString().split('T')[0],
            batch,
          }]
        },
        {
          kind: 'deposit',
          records: [{
            id: depositId,
            amount: formDataObj.deposit_amount,
            currency: formDataObj.currency,
            posted: new Date().toISOString().split('T')[0],
            narration: `STRIPE PAYOUT ${batch}`,
            bank_account_last3: '123',
          }]
        },
      ],
      window_start: formDataObj.window_start || '2026-10-01',
      window_end: formDataObj.window_end || '2026-10-31',
    }

    try {
      setCreating(true)
      await api.runs.create(payload)
      setShowCreate(false)
      fetchRuns()
    } catch (err: any) {
      alert(err.message)
    } finally {
      setCreating(false)
    }
  }

  if (loading) return <div className="loading">Loading runs...</div>
  if (error) return <div className="error">Failed to load runs: {error}</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Runs</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          New Run
        </button>
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Create Reconciliation Run</h2>
              <button className="modal-close" onClick={() => setShowCreate(false)}>&times;</button>
            </div>
            <form onSubmit={handleCreate}>
              <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                <div className="form-group">
                  <label className="label">Currency</label>
                  <select name="currency" className="input" defaultValue="USD">
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="JPY">JPY</option>
                    <option value="BHD">BHD</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="label">Charge Amount</label>
                  <input name="charge_amount" type="text" className="input" placeholder="100.00" required />
                </div>
                <div className="form-group">
                  <label className="label">Payout Amount</label>
                  <input name="payout_amount" type="text" className="input" placeholder="95.00" required />
                </div>
                <div className="form-group">
                  <label className="label">Deposit Amount</label>
                  <input name="deposit_amount" type="text" className="input" placeholder="100.00" required />
                </div>
                <div className="form-group">
                  <label className="label">Window Start</label>
                  <input name="window_start" type="date" className="input" defaultValue="2026-10-01" />
                </div>
                <div className="form-group">
                  <label className="label">Window End</label>
                  <input name="window_end" type="date" className="input" defaultValue="2026-10-31" />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Run'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Input Digest</th>
                <th>Rule Version</th>
                <th>Status</th>
                <th>Numerator</th>
                <th>Denominator</th>
                <th>Rate</th>
                <th>Discrepancies</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run: any) => {
                return (
                  <tr key={run.run_id}>
                    <td className="mono">{run.run_id.slice(0, 16)}...</td>
                    <td className="mono">{run.input_digest?.slice(0, 16)}...</td>
                    <td>{run.rule_version}</td>
                    <td>{run.status}</td>
                    <td className="mono">{run.numerator}</td>
                    <td className="mono">{run.denominator}</td>
                    <td>{(run.rate * 100).toFixed(2)}%</td>
                    <td>{run.discrepancy_count}</td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => window.location.href = `/discrepancies?run_id=${run.run_id}`}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default RunsPage