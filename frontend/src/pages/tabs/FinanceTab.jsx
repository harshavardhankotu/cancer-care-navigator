import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

const INSURANCE = [['uninsured', 'Uninsured'], ['private_insured', 'Private insurance'], ['employer_group', 'Employer group cover'], ['government_scheme', 'Government scheme'], ['unknown', 'Not sure']]
const INCOME = [['low', 'Low'], ['lower_middle', 'Lower middle'], ['middle', 'Middle'], ['upper_middle', 'Upper middle'], ['high', 'High'], ['unknown', 'Prefer not to say']]

const CURRENCY_MAP = {
  IN: '₹ (INR)',
  US: '$ (USD)',
  GB: '£ (GBP)',
  DE: '€ (EUR)',
  FR: '€ (EUR)',
  IT: '€ (EUR)',
  ES: '€ (EUR)',
  NL: '€ (EUR)',
  CA: 'CA$ (CAD)',
  AU: 'AU$ (AUD)',
  SG: 'S$ (SGD)',
  JP: '¥ (JPY)',
  BR: 'R$ (BRL)',
}

export default function FinanceTab({ caseId, country = 'IN' }) {
  const [profile, setProfile] = useState({ insurance_status: 'unknown', insurer_name: '', income_bracket: 'unknown', budget_ceiling: '' })
  const [match, setMatch] = useState(null)
  const [schemes, setSchemes] = useState([])
  const [paps, setPaps] = useState([])
  const [error, setError] = useState(null)

  const curr = CURRENCY_MAP[(country || 'IN').toUpperCase()] || 'Local currency'

  useEffect(() => {
    api(`/cases/${caseId}/financial-profile`).then((p) => p && setProfile({
      insurance_status: p.insurance_status || 'unknown',
      insurer_name: p.insurer_name || '',
      income_bracket: p.income_bracket || 'unknown',
      budget_ceiling: p.budget_ceiling ?? '',
    })).catch(() => {})
    api(`/schemes?country=${country || ''}`).then(setSchemes).catch(() => {})
    api('/assistance-programs').then(setPaps).catch(() => {})
  }, [caseId, country])

  const save = async () => {
    setError(null)
    try {
      await api(`/cases/${caseId}/financial-profile`, {
        method: 'PUT',
        body: { ...profile, budget_ceiling: profile.budget_ceiling === '' ? null : Number(profile.budget_ceiling) },
      })
      runMatch()
    } catch (e) { setError(e.message) }
  }

  const runMatch = async () => {
    setError(null)
    try { setMatch(await api(`/cases/${caseId}/coverage-match`, { method: 'POST' })) }
    catch (e) { setError(e.message) }
  }

  return (
    <div>
      <ErrorBox error={error} />
      <section className="card mb-4">
        <h2 className="font-semibold mb-1">Financial profile (all fields optional)</h2>
        <p className="text-xs text-slate-500 mb-3">Used only for rules-based scheme matching within this app. No real insurance APIs are queried.</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div><label className="label">Insurance status</label>
            <select className="input" value={profile.insurance_status} onChange={(e) => setProfile({ ...profile, insurance_status: e.target.value })}>
              {INSURANCE.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select></div>
          <div><label className="label">Insurer name</label>
            <input className="input" value={profile.insurer_name} onChange={(e) => setProfile({ ...profile, insurer_name: e.target.value })} /></div>
          <div><label className="label">Income bracket</label>
            <select className="input" value={profile.income_bracket} onChange={(e) => setProfile({ ...profile, income_bracket: e.target.value })}>
              {INCOME.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select></div>
          <div><label className="label">Budget ceiling ({curr})</label>
            <input className="input" type="number" min="0" value={profile.budget_ceiling} onChange={(e) => setProfile({ ...profile, budget_ceiling: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" onClick={save}>Save & match coverage</button>
      </section>

      {match && (
        <section className="card mb-4">
          <h2 className="font-semibold mb-2">Coverage match results</h2>
          {match.results.map((r) => (
            <div key={r.scheme_id} className={`border rounded p-2 mb-2 text-sm border-l-4 ${r.status === 'eligible' ? 'border-l-green-500 bg-green-50' : r.status === 'needs_verification' ? 'border-l-yellow-400 bg-yellow-50' : 'border-l-slate-300'}`}>
              <span className="font-medium">{r.scheme_name}</span>
              <span className="ml-2 text-xs font-semibold uppercase text-slate-500">{r.status.replace('_', ' ')}</span>
              <ul className="list-disc ml-5 text-xs text-slate-600 mt-1">{r.reasons.map((x, i) => <li key={i}>{x}</li>)}</ul>
              {r.coverage_limit && <p className="text-xs text-slate-500 mt-1">Limit: {r.coverage_limit}</p>}
            </div>
          ))}
          {match.network_matches.length > 0 && (
            <div className="text-sm mt-2">
              <strong>Network matches:</strong>{' '}
              {match.network_matches.map((m) => `${m.scheme_name} → ${m.matched_hospitals.join(', ')}`).join(' | ')}
            </div>
          )}
          {match.gaps.length > 0 && (
            <div className="bg-purple-50 border border-purple-300 text-purple-800 rounded p-2 mt-2 text-sm whitespace-pre-line">
              ⚠ Coverage gaps detected — added to Decision Flags:<br />{match.gaps.join('\n')}
            </div>
          )}
        </section>
      )}

      <section className="card mb-4">
        <h2 className="font-semibold mb-2">Seeded coverage schemes</h2>
        {schemes.map((s) => (
          <details key={s.id} className="border-b last:border-b-0 py-2 text-sm">
            <summary className="cursor-pointer font-medium">{s.scheme_name}</summary>
            <p className="text-xs text-slate-600 mt-1">{s.eligibility_summary}</p>
            <p className="text-xs text-slate-500 mt-1">Limit: {s.coverage_limit}</p>
            <p className="text-[10px] text-amber-700 mt-1">Verify current parameters on official portals — last seeded check {s.last_verified_date}.</p>
          </details>
        ))}
      </section>

      <section className="card">
        <h2 className="font-semibold mb-2">Patient assistance programmes</h2>
        {paps.map((p) => (
          <div key={p.id} className="border-b last:border-b-0 py-2 text-sm">
            <span className="font-medium">{p.drug_name}</span>
            <span className="ml-2 text-[10px] uppercase font-semibold bg-amber-100 text-amber-800 border border-amber-300 rounded px-1.5 py-0.5">placeholder</span>
            <p className="text-xs text-slate-600 mt-1">{p.program_type}</p>
            <p className="text-xs text-slate-500">{p.eligibility_criteria}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
