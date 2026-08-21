import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'
import { ModeBadge } from './DocumentsTab.jsx'

export default function TimelineTab({ caseId }) {
  const [docs, setDocs] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    api(`/cases/${caseId}/documents`).then(setDocs).catch((e) => setError(e.message))
  }, [caseId])

  const groups = {}
  for (const d of docs) {
    const key = d.extracted_date || d.uploaded_at.slice(0, 10)
    ;(groups[key] = groups[key] || []).push(d)
  }
  const sorted = Object.entries(groups).sort((a, b) => (a[0] < b[0] ? 1 : -1))

  if (error) return <ErrorBox error={error} />

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3">
        Chronological record timeline. Entries come from manual entry or free local PDF
        extraction — always verify details.
      </p>
      {sorted.length === 0 && (
        <div className="card text-slate-500 text-sm">
          No records yet — use the Documents tab to add one (with or without a file).
        </div>
      )}
      {sorted.map(([date, entries]) => (
        <div key={date} className="mb-4">
          <div className="text-sm font-semibold text-blue-700 bg-blue-50 inline-block rounded px-2 py-0.5 mb-2">{date}</div>
          <div className="border-l-2 border-blue-200 ml-3 pl-4 space-y-3">
            {entries.map((d) => (
              <div key={d.id} className="card !py-3">
                <span className="font-medium">{d.extracted_doc_type || 'Record'}</span>
                <span className="text-sm text-slate-500"> · {d.extracted_source || 'Unknown source'}</span>
                <ModeBadge doc={d} />
                {(d.extracted_key_findings || []).length > 0 && (
                  <ul className="list-disc ml-5 text-sm text-slate-600 mt-1">
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
