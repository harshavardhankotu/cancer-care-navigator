import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api.js'
import { DISCLAIMER, ErrorBox } from '../components/Layout.jsx'

export default function PackageShareView() {
  const { pkgId, token } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api(`/public/packages/${pkgId}/${token}`).then(setData).catch((e) => setError(e.message))
  }, [pkgId, token])

  if (error) return <ErrorBox error={error} />
  if (!data) return <div className="p-8 text-slate-500">Loading shared package…</div>

  const snap = data.snapshot_json
  const c = snap.case || {}

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-xl font-bold">Second-opinion case package</h1>
      <p className="text-xs text-slate-500">Read-only snapshot · version v{data.version_number} · generated {new Date(data.generated_at).toLocaleString()}</p>
      <div className="bg-amber-100 border border-amber-300 text-amber-900 text-xs rounded p-2 my-2">⚠️ {DISCLAIMER}</div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-2">Patient summary</h2>
        <table className="text-sm w-full">
          <tbody>
            {[['Patient', c.patient_name], ['Age / Sex', `${c.patient_age ?? '—'} / ${c.patient_sex ?? '—'}`],
              ['Diagnosis', c.cancer_type], ['Stage', c.stage || '—'],
              ['Date of diagnosis', c.diagnosis_date || '—'], ['Current status', c.current_status || '—']].map(([k, v]) => (
              <tr key={k}><td className="pr-4 py-0.5 text-slate-500 align-top whitespace-nowrap">{k}</td>
                <td className="py-0.5">{v}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-2">Timeline of records</h2>
        {(snap.documents || []).length === 0 && <p className="text-sm text-slate-500">No documents in this snapshot.</p>}
        <ul className="text-sm space-y-1">
          {(snap.documents || []).map((d, i) => (
            <li key={i} className="border-b last:border-b-0 pb-1">
              <strong>{d.extracted_date || (d.uploaded_at || '').slice(0, 10)}</strong> — {d.doc_type} · {d.source}
              {(d.key_findings || []).length > 0 && (
                <span className="block text-slate-500 text-xs">{d.key_findings.join('; ')}</span>
              )}
            </li>
          ))}
        </ul>
      </div>

      <div className="card mb-3">
        <h2 className="font-semibold mb-2">Open questions raised by the family</h2>
        {(snap.open_flags || []).length === 0 && <p className="text-sm text-slate-500">None at generation time.</p>}
        <ol className="list-decimal ml-5 text-sm space-y-2">
          {(snap.open_flags || []).map((f, i) => (
            <li key={i}>
              {f.flag_type === 'coverage_gap'
                ? <span className="whitespace-pre-line">{f.message}</span>
                : <>
                    {f.condition}
                    <span className="block text-xs text-slate-500">Option this may foreclose: {f.foreclosed_option}</span>
                    <span className="block text-xs text-slate-400">Source: {f.source_guideline} — {f.source_citation}</span>
                  </>}
            </li>
          ))}
        </ol>
      </div>

      <a className="btn-primary no-underline inline-block" href={`/api/public/packages/${pkgId}/${token}/pdf`} target="_blank" rel="noreferrer">
        Open as PDF
      </a>
    </div>
  )
}
