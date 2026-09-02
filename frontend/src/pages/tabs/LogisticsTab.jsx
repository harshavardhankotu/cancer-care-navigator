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

      <section className="card mt-4">
        <h2 className="font-semibold mb-1">📦 Essential Records Checklist for Hospital Transfer & Travel</h2>
        <p className="text-xs text-slate-500 mb-3">
          Oncologists at receiving hospitals almost always require primary physical materials — not just paper summaries.
          Check off physical materials as you pack them:
        </p>
        <TransferPackingList caseId={caseId} />
      </section>
    </div>
  )
}

function TransferPackingList({ caseId }) {
  const [checked, setChecked] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(`ccn_transfer_pack_${caseId}`) || '{}')
    } catch {
      return {}
    }
  })

  const toggle = (idx) => {
    const updated = { ...checked, [idx]: !checked[idx] }
    setChecked(updated)
    try {
      localStorage.setItem(`ccn_transfer_pack_${caseId}`, JSON.stringify(updated))
    } catch { /* storage full / disabled */ }
  }

  const items = [
    { label: 'Original biopsy / pathology glass slides & FFPE tissue blocks', note: 'Receiving hospital will re-read slides in their own pathology lab' },
    { label: 'Raw imaging scans on DICOM optical disc (CD/DVD) or flash drive', note: 'Paper reports are not enough; radiologists need the 3D DICOM slices' },
    { label: 'Complete histopathology, IHC, and molecular/biomarker reports', note: 'EGFR, ALK, HER2, BRCA, PD-L1, NGS panels where applicable' },
    { label: 'Operative & surgical notes', note: 'Required if any prior biopsy, lumpectomy, or resection was performed' },
    { label: 'Chemotherapy / radiation flow sheets', note: 'Must state exact drug regimens, doses in mg/m², cycle dates, and cumulative radiation dose' },
    { label: 'Hospital discharge summaries', note: 'All inpatient stays related to oncologic care or complications' },
    { label: 'Recent blood work (last 14–30 days)', note: 'Complete blood count (CBC), liver function (LFT), kidney function (KFT/eGFR)' },
    { label: 'Government photo ID & health scheme / insurance card', note: 'Required for hospital registration, admission, and subsidy claim desks' },
    { label: 'Travel concessions & accommodation arranged', note: 'e.g. Indian Railways cancer concession certificate / hospital dharmashala / guest house' },
  ]

  const doneCount = Object.values(checked).filter(Boolean).length

  return (
    <div>
      <div className="text-xs text-slate-600 mb-2 font-medium">
        Prepared: {doneCount} of {items.length} items
      </div>
      <div className="space-y-2 text-sm">
        {items.map((it, idx) => (
          <label
            key={idx}
            className={`flex items-start gap-2.5 p-2 rounded border cursor-pointer transition-colors ${checked[idx] ? 'bg-green-50/70 border-green-200 line-through text-slate-400' : 'border-slate-200 hover:bg-slate-50'}`}
          >
            <input
              type="checkbox"
              className="mt-0.5 rounded text-blue-600 focus:ring-blue-500"
              checked={!!checked[idx]}
              onChange={() => toggle(idx)}
            />
            <div>
              <div className="font-medium text-slate-800">{it.label}</div>
              <div className="text-xs text-slate-500">{it.note}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
