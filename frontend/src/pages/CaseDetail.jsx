import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api.js'
import { ErrorBox } from '../components/Layout.jsx'
import TimelineTab from './tabs/TimelineTab.jsx'
import PlanTab from './tabs/PlanTab.jsx'
import DocumentsTab from './tabs/DocumentsTab.jsx'
import FlagsTab from './tabs/FlagsTab.jsx'
import OpinionsTab from './tabs/OpinionsTab.jsx'
import TrialsTab from './tabs/TrialsTab.jsx'
import LogisticsTab from './tabs/LogisticsTab.jsx'
import FinanceTab from './tabs/FinanceTab.jsx'

const TABS = [
  ['plan', '⭐ My Plan'],
  ['timeline', 'Timeline'],
  ['documents', 'Records'],
  ['flags', 'Decision Flags'],
  ['opinions', 'Second Opinions'],
  ['trials', 'Trials'],
  ['logistics', 'Logistics'],
  ['finance', 'Finance & Coverage'],
]

export default function CaseDetail() {
  const { id } = useParams()
  const [tab, setTab] = useState('timeline')
  const [caseData, setCaseData] = useState(null)
  const [flags, setFlags] = useState([])
  const [error, setError] = useState(null)
  const [statusDraft, setStatusDraft] = useState('')

  const load = () => {
    api(`/cases/${id}`).then((c) => { setCaseData(c); setStatusDraft(c.current_status || '') }).catch((e) => setError(e.message))
    api(`/cases/${id}/flags`).then(setFlags).catch(() => {})
  }
  useEffect(() => { load() }, [id])

  if (error) return <ErrorBox error={error} />
  if (!caseData) return <div className="text-slate-500">Loading…</div>

  const openFlags = flags.filter((f) => !f.acknowledged)

  const saveStatus = async () => {
    try {
      await api(`/cases/${id}`, { method: 'PATCH', body: { current_status: statusDraft } })
      await api(`/cases/${id}/evaluate-rules`, { method: 'POST' })
      load()
    } catch (e) { setError(e.message) }
  }

  return (
    <div>
      <div className="card mb-4">
        <h1 className="text-xl font-bold">{caseData.patient_name}</h1>
        <p className="text-sm text-slate-600">
          {caseData.cancer_type}{caseData.stage ? ` · Stage ${caseData.stage}` : ''}
          {caseData.patient_age ? ` · ${caseData.patient_age} yrs` : ''} {caseData.patient_sex ? `· ${caseData.patient_sex}` : ''}
        </p>
        <label className="label mt-3">Current status / treatment plan (edit and save to re-check decision risks)</label>
        <textarea className="input" rows={2} value={statusDraft} onChange={(e) => setStatusDraft(e.target.value)} />
        <button className="btn-primary mt-2" onClick={saveStatus}>Save status & re-check risks</button>
      </div>

      {openFlags.length > 0 && (
        <div className="bg-red-50 border border-red-300 rounded p-3 mb-4">
          <span className="font-semibold text-red-700">⚠ {openFlags.length} open decision flag(s)</span>
          <span className="text-sm text-red-600"> — see the Decision Flags tab. Sources are cited; discuss with your treating oncologist.</span>
        </div>
      )}

      <div role="tablist" aria-label="Case sections" className="flex gap-1 mb-4 flex-wrap border-b border-slate-200 pb-1">
        {TABS.map(([key, label]) => (
          <button key={key}
            role="tab"
            aria-selected={tab === key}
            className={`px-3 py-1.5 rounded-t text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 transition-colors ${tab === key ? 'bg-white font-semibold border border-b-0 border-slate-200' : 'text-slate-500 hover:bg-slate-200'}`}
            onClick={() => setTab(key)}>
            {label}{key === 'flags' && openFlags.length > 0 ? ` (${openFlags.length})` : ''}
          </button>
        ))}
      </div>

      {tab === 'plan' && <PlanTab caseId={id} />}
      {tab === 'timeline' && <TimelineTab caseId={id} />}
      {tab === 'documents' && <DocumentsTab caseId={id} onChanged={load} />}
      {tab === 'flags' && <FlagsTab caseId={id} flags={flags} onChanged={load} />}
      {tab === 'opinions' && <OpinionsTab caseId={id} />}
      {tab === 'trials' && <TrialsTab caseId={id} cancerType={caseData.cancer_type} country={caseData.country || 'IN'} />}
      {tab === 'logistics' && <LogisticsTab caseId={id} />}
      {tab === 'finance' && <FinanceTab caseId={id} country={caseData.country || 'IN'} />}
    </div>
  )
}
