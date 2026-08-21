import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

const STATUS_STYLE = {
  eligible: 'border-l-green-500 bg-green-50',
  needs_verification: 'border-l-yellow-400 bg-yellow-50',
  not_eligible: 'border-l-slate-300',
}

export default function PlanTab({ caseId }) {
  const [plan, setPlan] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api(`/cases/${caseId}/personal-plan`).then(setPlan).catch((e) => setError(e.message))
  }, [caseId])

  if (error) return <ErrorBox error={error} />
  if (!plan) return <div className="text-slate-500">Building your personal plan…</div>

  const eligible = plan.schemes.filter((s) => s.status !== 'not_eligible')

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3">
        Personalised for this case (country: <strong>{plan.country}</strong>) using public,
        citable information only. Not medical advice — decisions rest with you and your doctors.
      </p>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">🏥 Centres near you ({plan.country})</h2>
        <p className="text-xs text-slate-500 mb-2">Ranked by objective public facts — see the Centres page for the full breakdown.</p>
        <ul className="text-sm space-y-1">
          {plan.local_centres.map((c) => (
            <li key={c.id} className="flex justify-between gap-2 border-b last:border-b-0 pb-1">
              <span><strong>{c.name}</strong> <span className="text-slate-400">· {c.location}</span></span>
              <span className="shrink-0 text-xs font-bold bg-slate-800 text-white rounded-full px-2 py-0.5">{c.score}/{c.max_score}</span>
            </li>
          ))}
          {plan.local_centres.length === 0 && (
            <li className="text-slate-500">No seeded centres for {plan.country} yet — check the global list below.</li>
          )}
        </ul>
        {plan.global_centres.length > 0 && (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-blue-600">Global leaders worth knowing about (for hard cases / second opinions)</summary>
            <ul className="text-sm space-y-1 mt-1">
              {plan.global_centres.map((c) => (
                <li key={c.id} className="flex justify-between gap-2">
                  <span>{c.name} <span className="text-slate-400">· {c.country}</span></span>
                  <span className="text-xs font-bold">{c.score}/{c.max_score}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">💰 Coverage you may qualify for</h2>
        <p className="text-xs text-slate-500 mb-2">Rules-based match vs your financial profile — always confirm with the scheme itself.</p>
        {eligible.length === 0 && <p className="text-sm text-slate-500">No schemes found for {plan.country}. Add your financial details in the Finance tab.</p>}
        {eligible.map((s) => (
          <details key={s.scheme_id} className={`border rounded p-2 mb-2 text-sm border-l-4 ${STATUS_STYLE[s.status]}`}>
            <summary className="cursor-pointer font-medium">
              {s.scheme_name}
              <span className="ml-2 text-xs font-semibold uppercase text-slate-500">{s.status.replace(/_/g, ' ')}</span>
            </summary>
            <p className="text-xs text-slate-600 mt-1">{s.summary}</p>
            {s.coverage_limit && <p className="text-xs text-slate-500 mt-0.5">Limit: {s.coverage_limit}</p>}
            {(s.reasons || []).length > 0 && (
              <ul className="list-disc ml-5 text-xs text-slate-500 mt-1">
                {s.reasons.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            )}
          </details>
        ))}
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">🧪 Recruiting trials (sites in {plan.country} first)</h2>
        {plan.trials.length === 0 && <p className="text-sm text-slate-500">No trials loaded — try the Trials tab.</p>}
        <ul className="text-sm space-y-2">
          {plan.trials.map((t) => (
            <li key={t.external_id || t.title}>
              <a className="text-blue-700 underline" href={t.url} target="_blank" rel="noreferrer">{t.title} ↗</a>
              <span className="block text-xs text-slate-500">
                {t.external_id}{t.country_sites > 0 ? ` · ${t.country_sites} site(s) in ${plan.country}` : ''}{t.live ? ' · live registry data' : ' · example data'}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">❓ Questions to raise with your treating oncologist</h2>
        {plan.questions_to_ask.length === 0 && <p className="text-sm text-slate-500">No open decision flags — nothing queued right now.</p>}
        <ol className="list-decimal ml-5 text-sm space-y-2">
          {plan.questions_to_ask.map((q, i) => (
            <li key={i}>
              {q.question}
              {q.why_it_matters && <span className="block text-xs text-slate-500">Why it matters: {q.why_it_matters}</span>}
              {q.source && <span className="block text-xs text-slate-400">Source: {q.source}</span>}
            </li>
          ))}
        </ol>
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">✅ Suggested next steps</h2>
        <ol className="list-decimal ml-5 text-sm space-y-1">
          {plan.next_steps.map((s, i) => <li key={i}>{s}</li>)}
        </ol>
      </section>

      <div className="bg-amber-100 border border-amber-300 rounded p-3 text-xs text-amber-900">
        ⚠️ {plan.disclaimer}
      </div>
    </div>
  )
}
