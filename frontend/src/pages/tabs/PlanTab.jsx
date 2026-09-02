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
  const [checkedSteps, setCheckedSteps] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(`ccn_plan_steps_${caseId}`) || '{}')
    } catch {
      return {}
    }
  })

  useEffect(() => {
    api(`/cases/${caseId}/personal-plan`).then(setPlan).catch((e) => setError(e.message))
  }, [caseId])

  const toggleStep = (idx) => {
    const updated = { ...checkedSteps, [idx]: !checkedSteps[idx] }
    setCheckedSteps(updated)
    try {
      localStorage.setItem(`ccn_plan_steps_${caseId}`, JSON.stringify(updated))
    } catch { /* storage full / disabled */ }
  }

  if (error) return <ErrorBox error={error} />
  if (!plan) return <div className="text-slate-500">Building your personal plan…</div>

  const eligible = plan.schemes.filter((s) => s.status !== 'not_eligible')

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <p className="text-xs text-slate-500 max-w-xl">
          Personalised for this case (country: <strong>{plan.country}</strong>) using public,
          citable information only. Not medical advice — decisions rest with you and your doctors.
        </p>
        <button
          className="btn-primary text-xs"
          onClick={() => window.print()}
          title="Print or save PDF of My Plan"
        >
          🖨️ Print / Save Plan
        </button>
      </div>

      <div className="mb-4 bg-blue-50 border border-blue-200 text-blue-900 rounded p-3 text-xs leading-relaxed">
        <strong>Audience note:</strong> {plan.audience_note}
      </div>

      {/* 1. Journey Triage: Needs Attention & In Progress */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <div className="card border-l-4 border-l-amber-500 bg-amber-50/30">
          <h3 className="font-semibold text-amber-950 text-sm flex items-center gap-1.5 mb-2">
            ⚠️ Needs Attention ({(plan.needs_attention || []).length})
          </h3>
          {(plan.needs_attention || []).length > 0 ? (
            <div className="space-y-2">
              {plan.needs_attention.map((item, i) => (
                <div key={i} className="text-xs bg-white border border-amber-200 rounded p-2.5 shadow-sm">
                  <div className="font-medium text-slate-900">{item.title}</div>
                  <div className="text-slate-600 mt-1">{item.action}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No urgent sequencing flags or missing baseline records identified right now.</p>
          )}
        </div>

        <div className="card border-l-4 border-l-blue-500 bg-blue-50/30">
          <h3 className="font-semibold text-blue-950 text-sm flex items-center gap-1.5 mb-2">
            ⏳ In Progress ({(plan.in_progress || []).length})
          </h3>
          {(plan.in_progress || []).length > 0 ? (
            <div className="space-y-2">
              {plan.in_progress.map((item, i) => (
                <div key={i} className="text-xs bg-white border border-blue-200 rounded p-2.5 shadow-sm">
                  <div className="font-medium text-slate-900">{item.title}</div>
                  <div className="text-slate-600 mt-1">{item.detail}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No active specialist requests or hospital transfers in progress.</p>
          )}
        </div>
      </div>

      {/* 2. Diagnostic & Second-Opinion Readiness */}
      {plan.record_readiness && (
        <div className="card mb-4 bg-slate-50 border-slate-200">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">Case Readiness & Record Coverage</h3>
            <span className="text-xs text-slate-500">{plan.record_readiness.total_documents} document(s) on timeline</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className={`p-2 rounded border flex items-center gap-1.5 ${plan.record_readiness.has_pathology ? 'bg-green-50 border-green-200 text-green-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
              <span>{plan.record_readiness.has_pathology ? '✅' : '⚠️'}</span>
              <span>Pathology / Biopsy</span>
            </div>
            <div className={`p-2 rounded border flex items-center gap-1.5 ${plan.record_readiness.has_imaging ? 'bg-green-50 border-green-200 text-green-800' : 'bg-slate-100 border-slate-200 text-slate-600'}`}>
              <span>{plan.record_readiness.has_imaging ? '✅' : '⚪'}</span>
              <span>Scans (CT/PET/MRI)</span>
            </div>
            <div className={`p-2 rounded border flex items-center gap-1.5 ${plan.record_readiness.has_labs ? 'bg-green-50 border-green-200 text-green-800' : 'bg-slate-100 border-slate-200 text-slate-600'}`}>
              <span>{plan.record_readiness.has_labs ? '✅' : '⚪'}</span>
              <span>Lab / Blood Reports</span>
            </div>
            <div className={`p-2 rounded border flex items-center gap-1.5 ${plan.second_opinion_readiness?.has_package ? 'bg-green-50 border-green-200 text-green-800' : 'bg-blue-50 border-blue-200 text-blue-800'}`}>
              <span>{plan.second_opinion_readiness?.has_package ? '✅' : '📋'}</span>
              <span>Case Package</span>
            </div>
          </div>
          {plan.record_readiness.has_unconfirmed_dates && (
            <p className="text-[11px] text-amber-700 mt-2">
              ⚠️ Some timeline records have unconfirmed dates — check the Records tab to verify report dates.
            </p>
          )}
        </div>
      )}

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
        {plan.plan_tier === 'free' && (
          <p className="text-[11px] text-slate-400 mt-2">
            Showing top 6 per list — supporters see up to 12 (see “Support” page). Everything essential stays free.
          </p>
        )}
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">💰 Coverage you may qualify for</h2>
        <p className="text-xs text-slate-500 mb-2">
          Rules-based match vs your financial profile — always confirm with the scheme itself.
          💎 marks programmes most patients have never heard of.
        </p>
        {eligible.length === 0 && <p className="text-sm text-slate-500">No schemes found for {plan.country}. Add your financial details in the Finance tab.</p>}
        {eligible.map((s) => (
          <details key={s.scheme_id} className={`border rounded p-2 mb-2 text-sm border-l-4 ${STATUS_STYLE[s.status]}`}>
            <summary className="cursor-pointer font-medium">
              {s.category && s.category !== 'general' ? '💎 ' : ''}{s.scheme_name}
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
        <h2 className="font-semibold mb-1">✈️ Treatment abroad (intercountry options)</h2>
        <p className="text-xs text-slate-500 mb-2">{plan.options_abroad?.note}</p>
        {(plan.options_abroad?.centres || []).length > 0 && (
          <ul className="text-sm space-y-1 mb-3">
            {plan.options_abroad.centres.map((c) => (
              <li key={c.id} className="flex justify-between gap-2 border-b last:border-b-0 pb-1">
                <span>
                  {c.website ? (
                    <a href={c.website} target="_blank" rel="noreferrer" className="text-blue-700 underline">{c.name} ↗</a>
                  ) : c.name}
                  <span className="text-slate-400"> · {c.country}</span>
                </span>
                <span className="text-xs font-bold shrink-0">{c.score}/{c.max_score}</span>
              </li>
            ))}
          </ul>
        )}
        {(plan.options_abroad?.notes || []).map((n, i) => (
          <div key={i} className="text-xs bg-slate-50 border rounded p-2 mb-1">
            <span className="font-semibold">{n.title}.</span> {n.detail}
            {n.source_url && <> <a className="underline" href={n.source_url} target="_blank" rel="noreferrer">source ↗</a></>}
          </div>
        ))}
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">🧪 Recruiting trials (sites in {plan.country} first)</h2>
        {plan.trials.length === 0 && <p className="text-sm text-slate-500">No trials loaded — try the Trials tab.</p>}
        <ul className="text-sm space-y-2">
          {plan.trials.map((t) => (
            <li key={t.external_id || t.title}>
              <a className="text-blue-700 underline font-medium" href={t.url} target="_blank" rel="noreferrer">{t.title} ↗</a>
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
              <div className="font-medium text-slate-800">{q.question}</div>
              {q.why_it_matters && <span className="block text-xs text-slate-500">Why it matters: {q.why_it_matters}</span>}
              {q.source && <span className="block text-xs text-slate-400">Source: {q.source}</span>}
            </li>
          ))}
        </ol>
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">✅ Prioritized Next Steps ({(plan.action_steps || plan.next_steps).length})</h2>
        <p className="text-xs text-slate-500 mb-2">Focused, state-specific actions for your current stage of navigation:</p>
        <div className="space-y-2 text-sm">
          {(plan.action_steps || plan.next_steps).map((step, i) => {
            const isObj = typeof step === 'object' && step !== null
            const title = isObj ? step.title : step.split(':')[0]
            const text = isObj ? step.explanation : (step.includes(':') ? step.slice(step.indexOf(':') + 1).trim() : step)
            const reason = isObj ? step.reason : ''
            const tab = isObj ? step.tab : ''
            return (
              <label key={i} className={`flex items-start gap-2.5 p-2.5 rounded border cursor-pointer transition-colors ${checkedSteps[i] ? 'bg-green-50 border-green-200 line-through text-slate-400' : 'border-slate-200 hover:bg-slate-50'}`}>
                <input
                  type="checkbox"
                  className="mt-0.5 rounded text-blue-600 focus:ring-blue-500"
                  checked={!!checkedSteps[i]}
                  onChange={() => toggleStep(i)}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{title}</span>
                    {tab && (
                      <span className="text-[10px] uppercase font-semibold tracking-wider bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded border border-slate-200">
                        {tab}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-600 mt-0.5">{text}</div>
                  {reason && <div className="text-[11px] text-slate-400 mt-0.5 italic">Why: {reason}</div>}
                </div>
              </label>
            )
          })}
        </div>
      </section>

      <div className="bg-amber-100 border border-amber-300 rounded p-3 text-xs text-amber-900">
        ⚠️ {plan.disclaimer}
      </div>
    </div>
  )
}
