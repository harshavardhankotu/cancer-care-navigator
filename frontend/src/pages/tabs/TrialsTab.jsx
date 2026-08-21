import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

export default function TrialsTab({ caseId, cancerType }) {
  const [biomarkers, setBiomarkers] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const search = async (e) => {
    if (e) e.preventDefault()
    setError(null)
    try {
      const params = new URLSearchParams({ cancer_type: cancerType || '' })
      if (biomarkers) params.set('biomarkers', biomarkers)
      params.set('live', 'true')
      setData(await api(`/trials/search?${params.toString()}`))
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { search() }, [])

  return (
    <div>
      <ErrorBox error={error} />
      <form onSubmit={search} className="card mb-3 flex flex-wrap gap-2 items-end">
        <div><label className="label">Cancer type (from case)</label><input className="input" value={cancerType || ''} disabled /></div>
        <div><label className="label">Biomarkers (comma-separated)</label>
          <input className="input" placeholder="EGFR, ALK, HER2…" value={biomarkers} onChange={(e) => setBiomarkers(e.target.value)} /></div>
        <button className="btn-primary">Search</button>
      </form>

      {data && (
        <>
          <p className={`text-xs rounded p-2 mb-3 border ${data.results[0]?.live ? 'bg-green-50 border-green-200 text-green-800' : 'bg-amber-50 border-amber-300 text-amber-900'}`}>
            {data.results[0]?.live
              ? `● ${data.source_note} — free public registry, no API key needed`
              : `○ ${data.source_note}`}
            {' '}· {data.disclaimer}
          </p>

          {data.results.length === 0 && <div className="card text-sm text-slate-500">No matching studies found.</div>}
          {data.results.map((t) => (
            <div key={t.external_id || t.title} className="card mb-2">
              <div className="flex justify-between items-start gap-2">
                <div>
                  <span className="font-medium">{t.title}</span>
                  {t.live
                    ? <span className="ml-2 text-[10px] uppercase font-semibold bg-green-100 text-green-800 border border-green-300 rounded px-1.5 py-0.5">live registry data</span>
                    : <span className="ml-2 text-[10px] uppercase font-semibold bg-amber-100 text-amber-800 border border-amber-300 rounded px-1.5 py-0.5">example data</span>}
                  {t.india_sites > 0 && (
                    <span className="ml-1 text-[10px] uppercase font-semibold bg-blue-100 text-blue-800 border border-blue-300 rounded px-1.5 py-0.5">
                      {t.india_sites} India site{t.india_sites > 1 ? 's' : ''}
                    </span>
                  )}
                </div>
                <a href={t.url} target="_blank" rel="noreferrer" className="btn-secondary shrink-0 no-underline">{t.source} ↗</a>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {t.external_id} · {t.status}{t.location ? ` · ${t.location}` : ''}
              </p>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
