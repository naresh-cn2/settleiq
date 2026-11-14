import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

interface ParsedRecord {
  kind: string
  id: string
  amount: string
  currency: string
  batch?: string
  reference?: string
  created?: string
  arrival_date?: string
  posted?: string
  narration?: string
  type?: string
  charge?: string
  [key: string]: string | undefined
}

interface ImportPreview {
  accepted_count: number
  quarantined_count: number
  duplicate_count: number
  accepted: Array<{ kind: string; id: string; amount: string; currency: string; digest: string }>
  quarantined: Array<{ index: number; reason: string; detail: string }>
  duplicates: string[]
}

export function ImportPage() {
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)
  const [parsedRecords, setParsedRecords] = useState<ParsedRecord[]>([])
  const [validating, setValidating] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [importing, setImporting] = useState(false)
  const navigate = useNavigate()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null
    if (!f) return
    setFile(f)
    setFileName(f.name)
    setParseError(null)
    setPreview(null)
    setValidationError(null)
  }

  const handleParseFile = async () => {
    if (!file) return
    setParsing(true)
    setParseError(null)
    try {
      const text = await file.text()
      let records: ParsedRecord[] = []

      if (file.name.toLowerCase().endsWith('.json')) {
        const data = JSON.parse(text)
        if (Array.isArray(data)) {
          records = data.map((r: any) => ({
            kind: r.kind || 'charge',
            id: r.id || '',
            amount: r.amount || '',
            currency: r.currency || 'USD',
            batch: r.batch,
            reference: r.reference,
            created: r.created,
            arrival_date: r.arrival_date,
            posted: r.posted,
            narration: r.narration,
            type: r.type,
            charge: r.charge,
          }))
        } else if (data.records) {
          records = data.records.map((r: any) => ({
            kind: r.kind || 'charge',
            id: r.id || '',
            amount: r.amount || '',
            currency: r.currency || 'USD',
            batch: r.batch,
            reference: r.reference,
            created: r.created,
            arrival_date: r.arrival_date,
            posted: r.posted,
            narration: r.narration,
            type: r.type,
            charge: r.charge,
          }))
        }
      } else if (file.name.toLowerCase().endsWith('.csv')) {
        records = parseCSV(text)
      } else {
        throw new Error('Unsupported file type. Use .json or .csv')
      }

      records = records.filter((r) => r.id && r.amount && r.currency)
      setParsedRecords(records)
    } catch (err: any) {
      setParseError(err.message || 'Failed to parse file')
    } finally {
      setParsing(false)
    }
  }

  const handleValidate = async () => {
    if (parsedRecords.length === 0) return
    setValidating(true)
    setValidationError(null)
    try {
      // Group records by kind for the API payload.
      const groups: Record<string, ParsedRecord[]> = {}
      for (const r of parsedRecords) {
        if (!groups[r.kind]) groups[r.kind] = []
        groups[r.kind].push(r)
      }

      const payload = {
        records: Object.entries(groups).map(([kind, recs]) => ({
          kind,
          records: recs.map((r) => {
            const { kind: _, ...rest } = r
            return rest
          }),
        })),
        window_start: '2026-10-01',
        window_end: '2026-10-31',
      }

      // Call the validate endpoint directly via fetch.
      // Include the demo token or API key so the request is authenticated.
      const mode = api.auth.getMode()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (mode === 'demo') {
        const token = api.auth.getDemoToken()
        if (token) headers['X-Demo-Token'] = token
      }

      const res = await fetch('/v1/import/validate', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `HTTP ${res.status}`)
      }
      const preview = (await res.json()) as ImportPreview
      setPreview(preview)
    } catch (err: any) {
      setValidationError(err.message || 'Validation failed')
    } finally {
      setValidating(false)
    }
  }

  const handleCreateRun = async () => {
    if (parsedRecords.length === 0) return
    setImporting(true)
    try {
      const groups: Record<string, ParsedRecord[]> = {}
      for (const r of parsedRecords) {
        if (!groups[r.kind]) groups[r.kind] = []
        groups[r.kind].push(r)
      }

      const payload = {
        records: Object.entries(groups).map(([kind, recs]) => ({
          kind,
          records: recs.map((r) => {
            const { kind: _, ...rest } = r
            return rest
          }),
        })),
        window_start: '2026-10-01',
        window_end: '2026-10-31',
      }

      await api.runs.create(payload as any)
      navigate('/')
    } catch (err: any) {
      setValidationError(err.message || 'Failed to create run')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Data Import</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem', marginTop: '4px' }}>
            Upload reconciliation data in JSON or CSV format. Records are validated
            before processing — no data is persisted until you confirm.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/')}
          data-testid="nav-dashboard"
        >
          Dashboard
        </button>
      </div>

      {validationError && (
        <div className="error" style={{ marginBottom: '16px' }}>
          {validationError}
        </div>
      )}

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        {/* Upload Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Upload File</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group">
              <label className="label">File</label>
              <input
                type="file"
                accept=".json,.csv"
                onChange={handleFileChange}
                disabled={parsing}
                data-testid="import-file-input"
              />
              {fileName && (
                <div className="text-muted" style={{ fontSize: '0.8125rem' }}>
                  {fileName}
                </div>
              )}
            </div>
            <button
              className="btn btn-primary"
              onClick={handleParseFile}
              disabled={!file || parsing}
              data-testid="import-parse"
            >
              {parsing ? 'Parsing...' : 'Parse & Preview'}
            </button>
            {parseError && (
              <div className="error" style={{ marginTop: '12px', fontSize: '0.875rem' }}>
                {parseError}
              </div>
            )}
          </div>
        </div>

        {/* Parsed Records Preview */}
        {parsedRecords.length > 0 && (
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 className="card-title">Parsed Records ({parsedRecords.length})</h2>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setParsedRecords([])
                  setFile(null)
                  setFileName('')
                  setPreview(null)
                }}
              >
                Clear
              </button>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Kind</th>
                    <th>ID</th>
                    <th>Amount</th>
                    <th>Currency</th>
                    <th>Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedRecords.slice(0, 50).map((r, i) => (
                    <tr key={i}>
                      <td className="mono text-muted">{r.kind}</td>
                      <td className="mono text-truncate">{r.id}</td>
                      <td className="mono">{r.amount}</td>
                      <td className="mono text-muted">{r.currency}</td>
                      <td className="mono text-truncate text-muted">{r.reference || r.batch || '—'}</td>
                    </tr>
                  ))}
                  {parsedRecords.length > 50 && (
                    <tr>
                      <td colSpan={5} className="text-muted">
                        …and {parsedRecords.length - 50} more records
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleValidate}
              disabled={validating}
              data-testid="import-validate"
            >
              {validating ? 'Validating…' : 'Validate Records'}
            </button>
          </div>
        )}

        {/* Validation Preview */}
        {preview && (
          <div className="card" style={{ borderTop: `3px solid ${preview.quarantined_count > 0 ? 'var(--warning)' : 'var(--success)'}` }}>
            <div className="card-header">
              <h2 className="card-title">Validation Preview</h2>
            </div>
            <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', marginBottom: '16px' }}>
              <div className="card" style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)' }}>
                <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Accepted</div>
                <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>{preview.accepted_count}</div>
              </div>
              <div className="card" style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)' }}>
                <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Quarantined</div>
                <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--warning)' }}>{preview.quarantined_count}</div>
              </div>
              <div className="card" style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius)' }}>
                <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Duplicates</div>
                <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-muted)' }}>{preview.duplicate_count}</div>
              </div>
            </div>

            {preview.quarantined.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '0.875rem', marginBottom: '8px', color: 'var(--warning)' }}>Quarantined Records</h3>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Index</th>
                        <th>Reason</th>
                        <th>Detail</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.quarantined.map((q, i) => (
                        <tr key={i}>
                          <td className="mono text-muted">{q.index}</td>
                          <td className="mono text-truncate">{q.reason}</td>
                          <td className="mono text-truncate text-muted">{q.detail}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {preview.accepted_count > 0 && preview.quarantined_count === 0 && (
              <div style={{ background: 'rgba(63, 185, 80, 0.1)', border: '1px solid var(--success)', borderRadius: 'var(--radius)', padding: '16px', marginBottom: '16px' }}>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>✓ All records passed validation.</span>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                className="btn btn-primary"
                onClick={handleCreateRun}
                disabled={importing || preview.accepted_count === 0}
                data-testid="import-create-run"
              >
                {importing ? 'Creating Run…' : 'Create Reconciliation Run'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function parseCSV(text: string): ParsedRecord[] {
  const lines = text.split(/\r?\n/).filter((l) => l.trim())
  if (lines.length === 0) return []

  const header = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''))
  const records: ParsedRecord[] = []

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map((v) => v.trim().replace(/"/g, ''))
    const record: ParsedRecord = { kind: 'charge', id: '', amount: '', currency: 'USD' }
    header.forEach((h, idx) => {
      if (values[idx] !== undefined) record[h] = values[idx]
    })
    if (record.id && record.amount) records.push(record)
  }

  return records
}

export default ImportPage
