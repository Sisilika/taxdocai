import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [doc, setDoc] = useState(null)
  const [fileUrl, setFileUrl] = useState(null)
  const [review, setReview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setFileUrl(URL.createObjectURL(file))
    setLoading(true)
    setError(null)
    setReview(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setDoc(data)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  function updateField(idx, value) {
    const updated = { ...doc, fields: doc.fields.map((f, i) => i === idx ? { ...f, value } : f) }
    setDoc(updated)
  }

  async function saveEdits() {
    await fetch(`${API_BASE}/api/documents/${doc.document_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(doc),
    })
  }

  async function runReview() {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/agent/review/${doc.document_id}`, { method: 'POST' })
      const data = await res.json()
      setReview(data)
    } finally {
      setLoading(false)
    }
  }

  function exportFile(type) {
    window.open(`${API_BASE}/api/export/${type}/${doc.document_id}`, '_blank')
  }

  return (
    <div className="app-shell">
      <div className="header">
        <h1>TaxDocAI — Document Review</h1>
        <span style={{ fontSize: 12, color: '#888' }}>extraction → validation → human review → export</span>
      </div>

      {!doc && (
        <div className="upload-zone">
          <p>Upload a W-2 / 1099 / K-1 (PDF or image)</p>
          <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleUpload} />
        </div>
      )}

      {loading && <p>Processing…</p>}
      {error && <div className="issue error">{error}</div>}

      {doc && (
        <>
          <div className="split-view">
            <div className="panel">
              <h3>Source Document</h3>
              {fileUrl && fileUrl.match(/\.(png|jpe?g)$/i) ? (
                <img src={fileUrl} alt="source" style={{ width: '100%', borderRadius: 6 }} />
              ) : (
                <iframe src={fileUrl} title="source pdf" style={{ width: '100%', height: 500, border: 'none' }} />
              )}
            </div>

            <div className="panel">
              <h3>Extracted Fields — {doc.doc_type} ({doc.tax_year || 'year unknown'})</h3>
              <div className="field-row" style={{ fontWeight: 600, fontSize: 12, color: '#888' }}>
                <span>Box</span><span>Value</span><span>Conf.</span>
              </div>
              {doc.fields.map((f, i) => (
                <div className="field-row" key={i}>
                  <span>{f.box_label}</span>
                  <input value={f.value} onChange={(e) => updateField(i, e.target.value)} />
                  <span className={f.confidence < 0.6 ? 'confidence-low' : 'confidence-ok'}>
                    {Math.round(f.confidence * 100)}%
                  </span>
                </div>
              ))}

              <div className="actions">
                <button onClick={saveEdits}>Save edits</button>
                <button className="secondary" onClick={runReview}>Run validation agent</button>
              </div>

              {review && (
                <>
                  <h4 style={{ marginTop: 16 }}>Agent Review ({review.anomalies_flagged} flagged)</h4>
                  {review.issues.map((iss, i) => (
                    <div className={`issue ${iss.severity}`} key={i}>
                      <strong>{iss.field || 'General'}:</strong> {iss.message}
                    </div>
                  ))}
                  <div className="summary-box">{review.summary}</div>
                </>
              )}

              <div className="actions">
                <button className="secondary" onClick={() => exportFile('csv')}>Export CSV</button>
                <button className="secondary" onClick={() => exportFile('xml')}>Export XML</button>
                <button className="secondary" onClick={() => { setDoc(null); setReview(null); setFileUrl(null) }}>
                  Upload another
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
