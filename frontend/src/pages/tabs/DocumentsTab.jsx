import React, { useEffect, useRef, useState } from 'react'
import { api, downloadFile } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

export function ModeBadge({ doc }) {
  const mode = doc.raw_extraction_json?.extraction_mode
  if (!mode) return null
  const map = {
    pdf_text: ['auto-read from PDF text', 'bg-green-100 text-green-800 border-green-300'],
    manual: ['entered manually', 'bg-blue-100 text-blue-800 border-blue-300'],
    stub: ['could not read — needs correction', 'bg-amber-100 text-amber-800 border-amber-300'],
  }
  const [label, cls] = map[mode] || [mode, 'bg-slate-100 border-slate-300']
  return <span className={`ml-2 text-[10px] font-semibold rounded px-1.5 py-0.5 border ${cls}`}>{label}</span>
}

export default function DocumentsTab({ caseId, onChanged }) {
  const [docs, setDocs] = useState([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [showManual, setShowManual] = useState(false)
  const fileRef = useRef()
  const [meta, setMeta] = useState({ extracted_date: '', extracted_source: '', extracted_doc_type: '' })
  const [manual, setManual] = useState({ extracted_date: '', extracted_source: '', extracted_doc_type: '', finding: '' })

  const load = () => api(`/cases/${caseId}/documents`).then(setDocs).catch((e) => setError(e.message))
  useEffect(() => { load() }, [caseId])

  const upload = async (e) => {
    e.preventDefault()
    if (!fileRef.current.files[0]) { setError('Choose a PDF or image file'); return }
    setBusy(true); setError(null)
    try {
      const fd = new FormData()
      fd.append('file', fileRef.current.files[0])
      Object.entries(meta).forEach(([k, v]) => v && fd.append(k, v))
      await api(`/cases/${caseId}/documents`, { method: 'POST', formData: fd })
      fileRef.current.value = ''
      setMeta({ extracted_date: '', extracted_source: '', extracted_doc_type: '' })
      load(); onChanged && onChanged()
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  const addManual = async (e) => {
    e.preventDefault(); setError(null)
    try {
      await api(`/cases/${caseId}/records`, {
        method: 'POST',
        body: {
          extracted_date: manual.extracted_date || null,
          extracted_source: manual.extracted_source,
          extracted_doc_type: manual.extracted_doc_type,
          key_findings: manual.finding ? manual.finding.split('\n') : [],
        },
      })
      setManual({ extracted_date: '', extracted_source: '', extracted_doc_type: '', finding: '' })
      setShowManual(false)
      load(); onChanged && onChanged()
    } catch (err) { setError(err.message) }
  }

  const saveDoc = async (doc, patch) => {
    try {
      await api(`/documents/${doc.id}`, { method: 'PATCH', body: patch })
      load(); onChanged && onChanged()
    } catch (err) { setError(err.message) }
  }

  const remove = async (doc) => {
    if (!window.confirm('Delete this record?')) return
    try { await api(`/documents/${doc.id}`, { method: 'DELETE' }); load(); onChanged && onChanged() }
    catch (err) { setError(err.message) }
  }

  return (
    <div>
      <ErrorBox error={error} />
      <div className="flex gap-2 mb-3">
        <button className="btn-secondary" onClick={() => { setShowManual(!showManual) }}>
          {showManual ? 'Cancel' : '+ Add record without file'}
        </button>
        <span className="text-xs text-slate-500 self-center">Fastest way to build the timeline — no scanning needed.</span>
      </div>

      {showManual && (
        <form onSubmit={addManual} className="card mb-4 grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div><label className="label">Date</label><input className="input" type="date" value={manual.extracted_date} onChange={(e) => setManual({ ...manual, extracted_date: e.target.value })} /></div>
          <div><label className="label">Source hospital/lab</label><input className="input" value={manual.extracted_source} onChange={(e) => setManual({ ...manual, extracted_source: e.target.value })} /></div>
          <div><label className="label">Type (e.g., Pathology report)</label><input className="input" value={manual.extracted_doc_type} onChange={(e) => setManual({ ...manual, extracted_doc_type: e.target.value })} /></div>
          <div className="md:col-span-4"><label className="label">Key findings (one per line)</label>
            <textarea className="input" rows={2} value={manual.finding} onChange={(e) => setManual({ ...manual, finding: e.target.value })} /></div>
          <button className="btn-primary">Add to timeline</button>
        </form>
      )}

      <form onSubmit={upload} className="card mb-4">
        <h2 className="font-semibold mb-2">Upload document (PDF / image)</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div><label className="label">File</label><input className="input" type="file" accept=".pdf,.png,.jpg,.jpeg" ref={fileRef} /></div>
          <div><label className="label">Document date (optional override)</label><input className="input" type="date" value={meta.extracted_date} onChange={(e) => setMeta({ ...meta, extracted_date: e.target.value })} /></div>
          <div><label className="label">Source hospital/lab (optional)</label><input className="input" value={meta.extracted_source} onChange={(e) => setMeta({ ...meta, extracted_source: e.target.value })} /></div>
          <div><label className="label">Document type (optional)</label><input className="input" value={meta.extracted_doc_type} onChange={(e) => setMeta({ ...meta, extracted_doc_type: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" disabled={busy}>{busy ? 'Uploading…' : 'Upload'}</button>
        <p className="text-xs text-slate-500 mt-2">
          Digital PDFs are read automatically (free local extraction). Scanned images get placeholder
          fields you can correct below in one click.
        </p>
      </form>

      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="text-xs text-slate-500 font-medium">{docs.length} total record(s)</div>
        {docs.length > 2 && (
          <input
            type="text"
            className="input !w-64 text-xs py-1"
            placeholder="🔍 Search records, findings, sources…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        )}
      </div>

      {docs
        .filter((d) => {
          if (!search.trim()) return true
          const q = search.toLowerCase()
          const type = (d.extracted_doc_type || '').toLowerCase()
          const src = (d.extracted_source || '').toLowerCase()
          const fn = (d.original_filename || '').toLowerCase()
          const findings = (d.extracted_key_findings || []).join(' ').toLowerCase()
          return type.includes(q) || src.includes(q) || fn.includes(q) || findings.includes(q)
        })
        .map((d) => (
          <EditableDoc key={d.id} doc={d} onSave={saveDoc} onDelete={remove} />
        ))}
    </div>
  )
}

function EditableDoc({ doc, onSave, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState({
    extracted_date: doc.extracted_date || '',
    extracted_source: doc.extracted_source || '',
    extracted_doc_type: doc.extracted_doc_type || '',
    findingsText: (doc.extracted_key_findings || []).join('\n'),
  })

  return (
    <div className="card mb-3">
      <div className="flex justify-between items-start flex-wrap gap-2">
        <div>
          <span className="font-medium">{doc.extracted_doc_type || 'Document'}</span>
          <span className="text-sm text-slate-500"> · {doc.extracted_source || 'Unknown source'} · {doc.extracted_date || doc.uploaded_at.slice(0, 10)}</span>
          <ModeBadge doc={doc} />
          {doc.original_filename && <div className="text-xs text-slate-400">{doc.original_filename}</div>}
        </div>
        <div className="flex gap-2">
          {doc.has_file && (
            <button className="btn-secondary no-underline"
               onClick={() => downloadDoc(doc)}>Download file</button>
          )}
          <button className="btn-secondary" onClick={() => setEditing(!editing)}>{editing ? 'Close' : 'Correct fields'}</button>
          <button className="btn-danger" onClick={() => onDelete(doc)}>Delete</button>
        </div>
      </div>

      {!editing && (doc.extracted_key_findings || []).length > 0 && (
        <ul className="list-disc ml-5 text-sm text-slate-600 mt-1">
          {doc.extracted_key_findings.map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      )}

      {editing && (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div><label className="label">Date</label><input className="input" type="date" value={draft.extracted_date}
            onChange={(e) => setDraft({ ...draft, extracted_date: e.target.value })} /></div>
          <div><label className="label">Source hospital/lab</label><input className="input" value={draft.extracted_source}
            onChange={(e) => setDraft({ ...draft, extracted_source: e.target.value })} /></div>
          <div><label className="label">Document type</label><input className="input" value={draft.extracted_doc_type}
            onChange={(e) => setDraft({ ...draft, extracted_doc_type: e.target.value })} /></div>
          <div className="md:col-span-3"><label className="label">Key findings (one per line)</label>
            <textarea className="input" rows={3} value={draft.findingsText}
              onChange={(e) => setDraft({ ...draft, findingsText: e.target.value })} /></div>
          <button className="btn-primary" onClick={() => onSave(doc, {
            extracted_date: draft.extracted_date || null,
            extracted_source: draft.extracted_source,
            extracted_doc_type: draft.extracted_doc_type,
            extracted_key_findings: draft.findingsText.split('\n').map((s) => s.trim()).filter(Boolean),
          })}>Save corrections</button>
        </div>
      )}
    </div>
  )
}

async function downloadDoc(doc) {
  try { await downloadFile(`/documents/${doc.id}/file`, doc.original_filename || 'document') }
  catch (e) { alert(e.message) }
}
