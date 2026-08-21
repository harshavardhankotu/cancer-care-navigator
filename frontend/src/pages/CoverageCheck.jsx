import React, { useState } from 'react'
import { api } from '../api.js'
import { DISCLAIMER, ErrorBox } from '../components/Layout.jsx'

const INSURANCE = [['uninsured', 'Uninsured'], ['private_insured', 'Private insurance'], ['employer_group', 'Employer group cover'], ['government_scheme', 'Government scheme'], ['unknown', 'Not sure']]
const INCOME = [['low', 'Low'], ['lower_middle', 'Lower middle'], ['middle', 'Middle'], ['upper_middle', 'Upper middle'], ['high', 'High'], ['unknown', 'Prefer not to say']]
const EMPLOYMENT = [['central_government_employee', 'Central govt employee'], ['central_government_pensioner', 'Central govt pensioner'], ['state_government', 'State government'], ['private_sector', 'Private sector'], ['informal_sector', 'Informal / self-employed'], ['other', 'Other'], ['unknown', 'Prefer not to say']]

export default function CoverageCheck() {
  const [form, setForm] = useState({ insurance_status: 'uninsured', income_bracket: 'unknown', employment: 'unknown' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const submit = async (e) => {
    e.preventDefault(); setError(null)
    try { setResult(await api('/coverage-check', { method: 'POST', body: form })) }
    catch (err) { setError(err.message) }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-xl font-bold mb-1">Quick coverage check</h1>
      <p className="text-xs text-slate-500 mb-3">
        No case needed. Rules-based indicative check against seeded public scheme descriptions —
        eligibility is always confirmed by the official scheme, never by this tool.
      </p>
      <ErrorBox error={error} />
      <form onSubmit={submit} className="card mb-4 grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
        <div><label className="label">Insurance status</label>
          <select className="input" value={form.insurance_status} onChange={(e) => setForm({ ...form, insurance_status: e.target.value })}>
            {INSURANCE.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select></div>
        <div><label className="label">Household income bracket</label>
          <select className="input" value={form.income_bracket} onChange={(e) => setForm({ ...form, income_bracket: e.target.value })}>
            {INCOME.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select></div>
        <div><label className="label">Employment</label>
          <select className="input" value={form.employment} onChange={(e) => setForm({ ...form, employment: e.target.value })}>
            {EMPLOYMENT.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select></div>
        <button className="btn-primary">Check</button>
      </form>

      {result && (
        <>
          {result.results.map((r) => (
            <div key={r.scheme_id} className={`card mb-2 border-l-4 ${r.status === 'eligible' ? 'border-l-green-500' : r.status === 'needs_verification' ? 'border-l-yellow-400' : 'border-l-slate-300'}`}>
              <div className="font-medium">{r.scheme_name}
                <span className="ml-2 text-xs font-semibold uppercase text-slate-500">{r.status.replace('_', ' ')}</span>
              </div>
              <ul className="list-disc ml-5 text-sm text-slate-600 mt-1">{r.reasons.map((x, i) => <li key={i}>{x}</li>)}</ul>
              {r.coverage_limit && <p className="text-xs text-slate-500 mt-1">Coverage limit: {r.coverage_limit}</p>}
              {(r.exclusions || []).length > 0 && (
                <p className="text-xs text-slate-500 mt-1">Common exclusions: {r.exclusions.join('; ')}</p>
              )}
            </div>
          ))}
          <div className="bg-amber-50 border border-amber-300 rounded p-3 text-xs text-amber-900">
            ⚠️ {result.disclaimer}
          </div>
          <p className="text-xs text-slate-500 mt-2">{DISCLAIMER}</p>
        </>
      )}
    </div>
  )
}
