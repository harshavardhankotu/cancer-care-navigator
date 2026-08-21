import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { ErrorBox } from '../components/Layout.jsx'

export default function Centers() {
  const [centers, setCenters] = useState([])
  const [summary, setSummary] = useState([])
  const [cancerType, setCancerType] = useState('')
  const [capability, setCapability] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    api('/centers/wait-summary').then(setSummary).catch(() => {})
  }, [])

  useEffect(() => {
    const params = new URLSearchParams()
    if (cancerType) params.set('cancer_type', cancerType)
    if (capability) params.set('capability', capability)
    api(`/centers?${params.toString()}`).then(setCenters).catch((e) => setError(e.message))
  }, [cancerType, capability])

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">Specialist centres directory</h1>
      <p className="text-xs text-slate-500 mb-3">
        Starter seed list of well-known Indian cancer centres. Capabilities are publicly documented but
        require ongoing manual verification — confirm services and current status before travelling.
      </p>
      <ErrorBox error={error} />
      <div className="card mb-4 flex flex-wrap gap-2 items-end">
        <div><label className="label">Cancer type</label>
          <input className="input" placeholder="e.g., breast" value={cancerType} onChange={(e) => setCancerType(e.target.value)} /></div>
        <div><label className="label">Capability</label>
          <input className="input" placeholder="e.g., proton, transplant" value={capability} onChange={(e) => setCapability(e.target.value)} /></div>
        {summary.length > 0 && (
          <div className="ml-auto text-xs text-slate-500">
            Crowdsourced waits:{' '}
            {summary.map((s) => `${s.center_name.split('(')[0].trim()} ~${s.avg_recent_wait_days}d`).join(' · ')}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {centers.map((c) => (
          <div key={c.id} className="card">
            <div className="font-semibold">{c.name}</div>
            <div className="text-sm text-slate-500">{c.location}</div>
            <div className="mt-2">{(c.capabilities || []).map((x) => <span key={x} className="chip">{x}</span>)}</div>
            <p className="text-[10px] text-amber-700 mt-2">Starter seed list — verify before relying. Last seeded check: {c.last_verified_date}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
