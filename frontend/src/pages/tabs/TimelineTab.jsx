import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'
import { ModeBadge } from './DocumentsTab.jsx'

export default function TimelineTab({ caseId }) {
  const [docs, setDocs] = useState([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [error, setError] = useState(null)

  useEffect(() => {
    api(`/cases/${caseId}/documents`).then(setDocs).catch((e) => setError(e.message))
  }, [caseId])

  const filteredDocs = docs.filter((d) => {
    const type = (d.extracted_doc_type || '').toLowerCase()
    if (category !== 'all') {
      if (category === 'pathology' && !type.includes('patholog') && !type.includes('biopsy')) return false
      if (category === 'imaging' && !type.includes('imaging') && !type.includes('scan') && !type.includes('mri') && !type.includes('ct') && !type.includes('pet')) return false
      if (category === 'lab' && !type.includes('lab') && !type.includes('blood') && !type.includes('marker')) return false
      if (category === 'note' && (type.includes('patholog') || type.includes('imaging') || type.includes('lab'))) return false
    }
    if (!search.trim()) return true
    const q = search.toLowerCase()
    const src = (d.extracted_source || '').toLowerCase()
    const findings = (d.extracted_key_findings || []).join(' ').toLowerCase()
    const dt = (d.extracted_date || d.uploaded_at || '').toLowerCase()
    return type.includes(q) || src.includes(q) || findings.includes(q) || dt.includes(q)
  })

  const groups = {}
  for (const d of filteredDocs) {
    const isUnconfirmed = !d.extracted_date || !!d.raw_extraction_json?.date_unconfirmed
    const dt = d.extracted_date || d.uploaded_at.slice(0, 10)
    const key = isUnconfirmed ? `${dt} (Upload date)` : dt
    ;(groups[key] = groups[key] || []).push(d)
  }
  const sorted = Object.entries(groups).sort((a, b) => (a[0] < b[0] ? 1 : -1))

  if (error) return <ErrorBox error={error} />

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <p className="text-xs text-slate-500 max-w-xl">
          Chronological record timeline. Verified report dates appear with clear markers;
          upload-time estimates are highlighted for review.
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

      {docs.length > 0 && (
        <div className="flex gap-1.5 mb-3 flex-wrap text-xs">
          {[
            ['all', 'All records'],
            ['pathology', '🔬 Pathology & Biopsy'],
            ['imaging', '🩻 Imaging (CT/PET/MRI)'],
            ['lab', '🧪 Labs & Blood'],
            ['note', '📝 Notes & Other'],
          ].map(([cat, label]) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-2.5 py-1 rounded-full border transition-colors ${category === cat ? 'bg-blue-600 text-white border-blue-600 font-medium' : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'}`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

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
                    {(!d.extracted_date || d.raw_extraction_json?.date_unconfirmed) && (
                      <span className="ml-1 text-[10px] font-semibold rounded px-1.5 py-0.5 bg-amber-100 text-amber-800 border border-amber-300">
                        ⚠️ Date unconfirmed
                      </span>
                    )}
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
