import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { ErrorBox } from '../components/Layout.jsx'

const FACTOR_LABELS = {
  public_or_nonprofit_ownership: 'Public / non-profit ownership',
  national_accreditation_noted: 'National accreditation noted publicly',
  scheme_empanelment_noted: 'Government scheme empanelment noted',
  capability_breadth: 'Breadth of cancer capabilities',
}
const NOTE_STYLES = {
  ownership: 'bg-blue-50 border-blue-200 text-blue-900',
  accreditation: 'bg-green-50 border-green-200 text-green-900',
  scheme_empanelment: 'bg-purple-50 border-purple-200 text-purple-900',
}

export default function Centers() {
  const [centers, setCenters] = useState([])
  const [summary, setSummary] = useState([])
  const [methodology, setMethodology] = useState(null)
  const [cancerType, setCancerType] = useState('')
  const [capability, setCapability] = useState('')
  const [sort, setSort] = useState('score')
  const [error, setError] = useState(null)

  useEffect(() => {
    api('/centers/wait-summary').then(setSummary).catch(() => {})
    api('/centers/methodology').then(setMethodology).catch(() => {})
  }, [])

  useEffect(() => {
    const params = new URLSearchParams()
    if (cancerType) params.set('cancer_type', cancerType)
    if (capability) params.set('capability', capability)
    params.set('sort', sort)
    api(`/centers?${params.toString()}`).then(setCenters).catch((e) => setError(e.message))
  }, [cancerType, capability, sort])

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">Specialist centres — compared on facts, not reviews</h1>
      <p className="text-xs text-slate-500 mb-3">
        Starter seed list of well-known Indian cancer centres. Ranking uses ONLY objective,
        publicly citable facts with sources shown. This is <strong>not</strong> a quality rating.
        Individual doctors are deliberately not scored.
      </p>
      <ErrorBox error={error} />

      {methodology && (
        <details className="card mb-4">
          <summary className="cursor-pointer font-semibold text-sm">📊 How centres are compared (full transparency)</summary>
          <ul className="list-disc ml-5 text-sm mt-2 space-y-1">
            {methodology.principles.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
          <table className="text-sm mt-3 mb-2">
            <tbody>
              {Object.entries(methodology.weights).map(([k, v]) => (
                <tr key={k}><td className="pr-4 py-0.5 text-slate-600">{FACTOR_LABELS[k] || k}</td><td className="font-semibold">+{v}</td></tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs font-semibold text-slate-500">What we CANNOT measure:</p>
          <ul className="list-disc ml-5 text-xs text-slate-500 mb-2">
            {methodology.what_we_cannot_measure.map((x, i) => <li key={i}>{x}</li>)}
          </ul>
          <p className="text-xs font-semibold text-slate-500">Verify ANY hospital yourself (free official sources):</p>
          <ul className="ml-5 text-xs">
            {methodology.verify_any_hospital_yourself.map((l, i) => (
              <li key={i}><a className="text-blue-600 underline break-all" href={l.url} target="_blank" rel="noreferrer">{l.label} ↗</a></li>
            ))}
          </ul>
        </details>
      )}

      <div className="card mb-4 flex flex-wrap gap-2 items-end">
        <div><label className="label">Cancer type</label>
          <input className="input" placeholder="e.g., breast" value={cancerType} onChange={(e) => setCancerType(e.target.value)} /></div>
        <div><label className="label">Capability</label>
          <input className="input" placeholder="e.g., proton, transplant" value={capability} onChange={(e) => setCapability(e.target.value)} /></div>
        <div><label className="label">Sort by</label>
          <select className="input" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="score">Objective fact score</option>
            <option value="name">Name (A–Z)</option>
          </select></div>
        {summary.length > 0 && (
          <div className="ml-auto text-xs text-slate-500 max-w-sm">
            Crowdsourced waits:{' '}
            {summary.map((s) => `${s.center_name.split('(')[0].trim()} ~${s.avg_recent_wait_days}d`).join(' · ')}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {centers.map((c, idx) => (
          <div key={c.id} className="card relative">
            {sort === 'score' && (
              <span className="absolute top-3 right-3 text-xs font-bold bg-slate-800 text-white rounded-full px-2 py-1">
                #{idx + 1} · {c.objective_score.total}/{c.objective_score.max}
              </span>
            )}
            <div className="font-semibold pr-20">{c.name}</div>
            <div className="text-sm text-slate-500">{c.location}</div>
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-slate-500">Score breakdown ({c.objective_score.total}/{c.objective_score.max})</summary>
              <table className="text-xs mt-1">
                <tbody>
                  {Object.entries(c.objective_score.breakdown).map(([k, v]) => (
                    <tr key={k}>
                      <td className="pr-3 py-0.5 text-slate-500">{FACTOR_LABELS[k]}</td>
                      <td className={`py-0.5 font-semibold ${v > 0 ? 'text-green-700' : 'text-slate-300'}`}>
                        {v > 0 ? `+${v}` : '0'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
            <div className="mt-2">{(c.capabilities || []).map((x) => <span key={x} className="chip">{x}</span>)}</div>
            {(c.notes || []).length > 0 && (
              <div className="mt-2 space-y-1">
                {c.notes.map((n, i) => (
                  <div key={i} className={`text-xs rounded border p-1.5 ${NOTE_STYLES[n.note_type] || 'bg-slate-50 border-slate-200'}`}>
                    <span className="font-semibold uppercase text-[10px] mr-1">{n.note_type.replace(/_/g, ' ')}</span>
                    {n.detail}{' '}
                    {n.source_url && (
                      <a className="underline font-medium whitespace-nowrap" href={n.source_url} target="_blank" rel="noreferrer">
                        source: {n.source_name || 'link'} ↗
                      </a>
                    )}
                    {n.as_of_date && <span className="text-slate-400"> (as of {n.as_of_date})</span>}
                  </div>
                ))}
              </div>
            )}
            <p className="text-[10px] text-amber-700 mt-2">Facts change — verify at the linked source before deciding. Not medical advice.</p>
          </div>
        ))}
      </div>
    </div>
  )
}
