import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

export default function TrialsTab({ caseId, cancerType, country }) {
  const [biomarkers, setBiomarkers] = useState('')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const search = async (e) => {
    if (e) e.preventDefault()
    setError(null)
    try {
      const params = new URLSearchParams({ cancer_type: cancerType || '' })
      if (biomarkers) params.set('biomarkers', biomarkers)
      if (country) params.set('country', country)
      params.set('live', 'true')
      setData(await api(`/trials/search?${params.toString()}`))
    } catch (err) { setError(err.message) }
  }

  useEffect(() => { search() }, [])

  return (
    <div>
      <ErrorBox error={error} />

      <details className="card mb-3">
        <summary className="cursor-pointer font-semibold text-sm">📚 New to clinical trials? Read this first (2 minutes)</summary>
        <div className="text-xs text-slate-600 mt-2 space-y-1.5">
          <p><strong>What phases mean:</strong> Phase 1 tests safety in small groups. Phase 2 tests whether it works.
          Phase 3 compares it against the current standard treatment — Phase-3 results are what usually change
          medical practice.</p>
          <p><strong>Who pays:</strong> the trial typically covers the experimental drug and trial-specific tests.
          Standard-care costs may still apply — this differs by country and insurance, so ask the trial team
          directly what you would pay.</p>
          <p><strong>Before joining, ask:</strong> What are my other options? Who pays for what? Can I withdraw any
          time? Will I get the experimental arm or the control? Who do I contact at night if something goes wrong?</p>
          <p><strong>Why some trials rank higher below:</strong> we order by sites near you first, then a transparent
          importance heuristic (later phase + larger study). It is a reading aid — never a recommendation.</p>
        </div>
      </details>

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
              ? `● ${data.source_note}`
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
                    ? <span className="ml-2 text-[10px] uppercase font-semibold bg-green-100 text-green-800 border border-green-300 rounded px-1.5 py-0.5">live</span>
                    : <span className="ml-2 text-[10px] uppercase font-semibold bg-amber-100 text-amber-800 border border-amber-300 rounded px-1.5 py-0.5">example</span>}
                </div>
                <a href={t.url} target="_blank" rel="noreferrer" className="btn-secondary shrink-0 no-underline">{t.external_id} ↗</a>
              </div>

              {(t.live && t.priority_why?.length > 0) && (
                <p className="text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded px-2 py-1 mt-2">
                  ⭐ {t.priority_why.join(' · ')}
                </p>
              )}

              <div className="flex flex-wrap gap-1 mt-2">
                {t.phase_label && t.phase_label !== 'Example entry' && (
                  <span className={`chip !font-semibold ${String(t.phase_label).includes('3') ? '!bg-purple-100 !border-purple-300 !text-purple-900' : ''}`}>
                    {t.phase_label}
                  </span>
                )}
                {t.enrollment > 0 && <span className="chip">~{t.enrollment.toLocaleString()} participants</span>}
                {t.country_sites > 0 && <span className="chip !bg-blue-50 !border-blue-200">{t.country_sites} site(s) in {country}</span>}
                {t.sponsor && <span className="chip">Sponsor: {t.sponsor}</span>}
                {(t.interventions || []).map((i) => <span key={i} className="chip">💊 {i}</span>)}
                {t.min_age && t.min_age !== 'N/A' && <span className="chip">Age ≥ {t.min_age}</span>}
              </div>

              {t.summary_snippet && <p className="text-xs text-slate-500 mt-2 leading-snug">{t.summary_snippet}</p>}
              {t.location && t.location !== 'See registry listing' && (
                <p className="text-[11px] text-slate-400 mt-1">Sites: {t.location}</p>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  )
}
