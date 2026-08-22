import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'
import { ModeBadge } from './DocumentsTab.jsx'

export default function TimelineTab({ caseId }) {
  const [docs, setDocs] = useState([])
  const [search, setSearch] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    api(`/cases/${caseId}/documents`).then(setDocs).catch((e) => setError(e.message))
  }, [caseId])

  const filteredDocs = docs.filter((d) => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    const type = (d.extracted_doc_type || '').toLowerCase()
    const src = (d.extracted_source || '').toLowerCase()
    const findings = (d.extracted_key_findings || []).join(' ').toLowerCase()
    const dt = (d.extracted_date || d.uploaded_at || '').toLowerCase()
    return type.includes(q) || src.includes(q) || findings.includes(q) || dt.includes(q)
  })

  const groups = {}
  for (const d of filteredDocs) {
    const key = d.extracted_date || d.uploaded_at.slice(0, 10)
    ;(groups[key] = groups[key] || []).push(d)
  }
  const sorted = Object.entries(groups).sort((a, b) => (a[0] < b[0] ? 1 : -1))

  if (error) return <ErrorBox error={error} />

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <p className="text-xs text-slate-500 max-w-xl">
          Chronological record timeline. Entries come from manual entry or free local PDF
          extraction — always verify details.
        </p>
        <div className="flex items-center gap-2">
          {docs.length > 2 && (
            <input
              type="text"
              className="input !w-56 text-xs py-1"
              placeholder="🔍 Search timeline…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          )}
          {docs.length > 0 && (
            <button
              className="btn-secondary text-xs"
              onClick={() => window.print()}
              title="Print timeline for oncologist consultation"
            >
              🖨️ Print timeline
            </button>
          )}
        </div>
      </div>

      {docs.length === 0 && (
        <div className="card text-slate-500 text-sm">
          No records yet — use the Records tab to add one (with or without a file).
        </div>
      )}

      {docs.length > 0 && sorted.length === 0 && (
        <div className="card text-slate-500 text-sm">
          No records matching "{search}".
        </div>
      )}

      {sorted.map(([date, entries]) => (
        <div key={date} className="mb-4">
          <div className="text-sm font-semibold text-blue-700 bg-blue-50 inline-block rounded px-2 py-0.5 mb-2 border border-blue-200">
            📅 {date}
          </div>
          <div className="border-l-2 border-blue-200 ml-3 pl-4 space-y-3">
            {entries.map((d) => (
              <div key={d.id} className="card !py-3 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between flex-wrap gap-1">
                  <div>
                    <span className="font-medium text-slate-800">{d.extracted_doc_type || 'Record'}</span>
                    <span className="text-sm text-slate-500"> · {d.extracted_source || 'Unknown source'}</span>
                    <ModeBadge doc={d} />
                  </div>
                  {d.has_file && (
                    <span className="text-[11px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                      📎 Attached file
                    </span>
                  )}
                </div>
                {(d.extracted_key_findings || []).length > 0 && (
                  <ul className="list-disc ml-5 text-sm text-slate-600 mt-2 space-y-0.5">
                    {d.extracted_key_findings.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
