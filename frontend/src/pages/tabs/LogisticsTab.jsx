import React, { useEffect, useState } from 'react'
import { api } from '../../api.js'
import { ErrorBox } from '../../components/Layout.jsx'

export default function LogisticsTab({ caseId }) {
  const [transfers, setTransfers] = useState([])
  const [summary, setSummary] = useState([])
  const [waitForm, setWaitForm] = useState({ center_name: '', reported_wait_days: '' })
  const [transferForm, setTransferForm] = useState({ from_hospital: '', to_hospital: '' })
  const [error, setError] = useState(null)

  const load = () => {
    api(`/cases/${caseId}/transfers`).then(setTransfers).catch((e) => setError(e.message))
    api('/centers/wait-summary').then(setSummary).catch(() => {})
  }
  useEffect(() => { load() }, [caseId])

  const submitWait = async (e) => {
    e.preventDefault(); setError(null)
    try {
      await api('/wait-reports', { method: 'POST', body: { center_name: waitForm.center_name, reported_wait_days: Number(waitForm.reported_wait_days) } })
      setWaitForm({ center_name: '', reported_wait_days: '' }); load()
    } catch (err) { setError(err.message) }
  }

  const addTransfer = async (e) => {
    e.preventDefault(); setError(null)
    try {
      await api(`/cases/${caseId}/transfers`, { method: 'POST', body: transferForm })
      setTransferForm({ from_hospital: '', to_hospital: '' }); load()
    } catch (err) { setError(err.message) }
  }

  const setStatus = async (id, status) => {
    try { await api(`/transfers/${id}?status=${status}`, { method: 'PATCH' }); load() }
    catch (err) { setError(err.message) }
  }

  return (
    <div>
      <ErrorBox error={error} />

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">Crowdsourced wait times</h2>
        <p className="text-xs text-slate-500 mb-3">
          Family-reported appointment wait times, averaged over the last 90 days. Crowdsourced data — treat as indicative only.
        </p>
        <form onSubmit={submitWait} className="flex flex-wrap gap-2 items-end mb-3">
          <div><label className="label">Centre name</label><input className="input" value={waitForm.center_name} onChange={(e) => setWaitForm({ ...waitForm, center_name: e.target.value })} required /></div>
          <div><label className="label">Reported wait (days)</label><input className="input" type="number" min="0" value={waitForm.reported_wait_days} onChange={(e) => setWaitForm({ ...waitForm, reported_wait_days: e.target.value })} required /></div>
          <button className="btn-primary">Submit report</button>
        </form>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-slate-500 border-b"><th className="py-1">Centre</th><th>Avg recent wait</th><th>Reports</th></tr></thead>
          <tbody>
            {summary.map((s) => (
              <tr key={s.center_name} className="border-b last:border-b-0">
                <td className="py-1.5">{s.center_name}</td>
                <td>{s.avg_recent_wait_days} days</td>
                <td className="text-xs text-slate-400">{s.report_count} ({s.window})</td>
              </tr>
            ))}
            {summary.length === 0 && <tr><td colSpan="3" className="text-slate-500 py-2">No reports yet.</td></tr>}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-1">Transfer requests checklist</h2>
        <p className="text-xs text-slate-500 mb-3">Track records transfer between hospitals: requested → received → uploaded to case file.</p>
        <form onSubmit={addTransfer} className="flex flex-wrap gap-2 items-end mb-3">
          <div><label className="label">From hospital</label><input className="input" value={transferForm.from_hospital} onChange={(e) => setTransferForm({ ...transferForm, from_hospital: e.target.value })} /></div>
          <div><label className="label">To hospital</label><input className="input" value={transferForm.to_hospital} onChange={(e) => setTransferForm({ ...transferForm, to_hospital: e.target.value })} required /></div>
          <button className="btn-primary">Add request</button>
        </form>
        {transfers.map((t) => (
          <div key={t.id} className="border rounded p-2 mb-2 flex items-center gap-3 flex-wrap text-sm">
            <span className="font-medium">{t.from_hospital || '?'} → {t.to_hospital || '?'}</span>
            <span className={`text-xs rounded px-2 py-0.5 font-medium ${t.status === 'uploaded' ? 'bg-green-100 text-green-700' : t.status === 'received' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-600'}`}>{t.status}</span>
            <div className="ml-auto flex gap-1">
              {t.status === 'requested' && <button className="btn-secondary" onClick={() => setStatus(t.id, 'received')}>Mark received</button>}
              {t.status === 'received' && <button className="btn-primary" onClick={() => setStatus(t.id, 'uploaded')}>Mark uploaded</button>}
            </div>
          </div>
        ))}
        {transfers.length === 0 && <p className="text-sm text-slate-500">No transfer requests yet.</p>}
      </section>
    </div>
  )
}
