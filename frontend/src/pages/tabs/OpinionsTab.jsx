import React, { useEffect, useState } from 'react'
import { api, downloadFile } from '../../api.js'
import { ErrorBox, isPlaceholder, PH } from '../../components/Layout.jsx'

export default function OpinionsTab({ caseId }) {
  const [doctors, setDoctors] = useState([])
  const [selected, setSelected] = useState([])
  const [requests, setRequests] = useState([])
  const [packages, setPackages] = useState([])
  const [comparison, setComparison] = useState(null)
  const [error, setError] = useState(null)
  const [respondFor, setRespondFor] = useState(null)

  const load = () => {
    api('/doctors').then(setDoctors).catch((e) => setError(e.message))
    api(`/cases/${caseId}/opinions`).then(setRequests).catch((e) => setError(e.message))
    api(`/cases/${caseId}/packages`).then(setPackages).catch(() => {})
    api(`/cases/${caseId}/opinions/comparison`).then(setComparison).catch(() => {})
  }
  useEffect(() => { load() }, [caseId])

  const toggle = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))

  const createDrafts = async () => {
    setError(null)
    try {
      await api(`/cases/${caseId}/opinions`, { method: 'POST', body: { doctor_ids: selected } })
      setSelected([]); load()
    } catch (e) { setError(e.message) }
  }

  const act = async (oid, action, response) => {
    setError(null)
    try {
      await api(`/opinions/${oid}`, { method: 'PATCH', body: { action, response } })
      setRespondFor(null); load()
    } catch (e) { setError(e.message) }
  }

  const genPackage = async () => {
    try { await api(`/cases/${caseId}/packages`, { method: 'POST' }); load() }
    catch (e) { setError(e.message) }
  }

  return (
    <div>
      <ErrorBox error={error} />

      <div className="card mb-4 bg-blue-50/50 border-blue-200">
        <h3 className="font-semibold text-blue-900 text-sm mb-1">
          💡 How Second Opinions Work in Cancer Care Navigator
        </h3>
        <p className="text-xs text-blue-950 leading-relaxed mb-2">
          Seeking a second opinion before major irreversible treatment (surgery, radiation, first-line chemo) is standard oncology practice.
          To get a fast, credible opinion:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-slate-700">
          <div className="bg-white p-2 rounded border border-blue-100">
            <strong>1. Pack your records</strong>
            <p className="text-slate-500 mt-0.5">Upload biopsy reports, scans, and notes in the Records tab.</p>
          </div>
          <div className="bg-white p-2 rounded border border-blue-100">
            <strong>2. Create snapshot package</strong>
            <p className="text-slate-500 mt-0.5">Generate an immutable PDF snapshot that doctors can review without logging in.</p>
          </div>
          <div className="bg-white p-2 rounded border border-blue-100">
            <strong>3. Reach out in parallel</strong>
            <p className="text-slate-500 mt-0.5">Consult 2–3 specialists simultaneously to prevent multi-week sequential delays.</p>
          </div>
        </div>
      </div>

      <section className="card mb-4">
        <h2 className="font-semibold mb-1">1. Select doctors for parallel second opinions</h2>
        <p className="text-xs text-slate-500 mb-3">
          Directory entries are placeholders — a human must curate and verify real contacts before use.
          Dispatch stays manual: you send the package yourself, then mark the request as sent.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {doctors.map((d) => (
            <label key={d.id} className={`border rounded p-2 flex gap-2 items-start cursor-pointer ${selected.includes(d.id) ? 'border-blue-500 bg-blue-50' : 'border-slate-200'}`}>
              <input type="checkbox" className="mt-1" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} />
              <span>
                <span className="text-sm font-medium">{d.name}</span>
                {isPlaceholder(d) && <PH />}
                <span className="block text-xs text-slate-500">{d.credentials} · {d.hospital}</span>
                <span className="block text-xs text-slate-400">SLA ~{d.avg_response_time_days} days · remote review: {d.accepts_remote_case_review ? 'yes' : 'no'}</span>
              </span>
            </label>
          ))}
        </div>
        <button className="btn-primary mt-3" disabled={selected.length === 0} onClick={createDrafts}>
          Create draft requests ({selected.length}) + snapshot package
        </button>
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-2">2. Outreach tracker</h2>
        {requests.length === 0 && <p className="text-sm text-slate-500">No opinion requests yet.</p>}
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-slate-500 border-b">
            <th className="py-1">Doctor</th><th>Status</th><th>SLA</th><th>Actions</th>
          </tr></thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id} className="border-b align-top">
                <td className="py-2">
                  <div className="font-medium">{r.doctor?.name}</div>
                  <div className="text-xs text-slate-400">{r.doctor?.hospital}</div>
                  {isPlaceholder(r.doctor) && <PH label="placeholder doctor" />}
                </td>
                <td><StatusChip status={r.status} overdue={r.overdue} /></td>
                <td className="text-xs text-slate-500">
                  {r.sla_deadline ? `due ${new Date(r.sla_deadline).toLocaleDateString()}` : '—'}
                  {r.overdue && <span className="block text-red-600 font-semibold">OVERDUE — no response</span>}
                </td>
                <td className="py-2">
                  <div className="flex flex-wrap gap-1">
                    {r.status === 'drafted' && (
                      <>
                        <button className="btn-secondary" onClick={() => downloadFile(`/packages/${r.case_package_version_id}/pdf`, `package-v.pdf`)}>Download package PDF</button>
                        <button className="btn-primary" onClick={() => act(r.id, 'mark_sent')}>Mark as sent</button>
                      </>
                    )}
                    {r.status === 'sent' && (
                      <>
                        <button className="btn-secondary" onClick={() => act(r.id, 'acknowledge')}>Acknowledged</button>
                        <button className="btn-secondary" onClick={() => act(r.id, 'no_response')}>No response</button>
                        <button className="btn-secondary" onClick={() => act(r.id, 'decline')}>Declined</button>
                      </>
                    )}
                    {['sent', 'acknowledged'].includes(r.status) && (
                      <button className="btn-primary" onClick={() => setRespondFor(respondFor === r.id ? null : r.id)}>
                        {respondFor === r.id ? 'Cancel' : 'Record opinion'}
                      </button>
                    )}
                  </div>
                  {respondFor === r.id && <RespondForm onSave={(resp) => act(r.id, 'respond', resp)} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card mb-4">
        <h2 className="font-semibold mb-2">3. Side-by-side comparison</h2>
        {!comparison || comparison.columns.length === 0 ? (
          <p className="text-sm text-slate-500">Received opinions will appear here for comparison.</p>
        ) : (
          <>
            {comparison.conflict_detected && (
              <div className="bg-red-50 border border-red-300 text-red-700 rounded p-2 mb-3 text-sm font-semibold">
                ⚠ Conflict detected: received opinions recommend different treatment modalities. Raise this explicitly with both doctors.
              </div>
            )}
            <div className="overflow-x-auto">
              <table className="w-full text-sm border">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="border p-2 text-left"></th>
                    {comparison.columns.map((c) => (
                      <th key={c.opinion_request_id} className={`border p-2 text-left ${c.conflicts_flagged ? 'bg-red-50' : ''}`}>
                        {c.doctor_name}<div className="text-xs font-normal text-slate-400">{c.hospital}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[['Recommended modality', 'recommended_modality'],
                    ['Sequencing note', 'sequencing_note'],
                    ['Caveats', 'caveats'],
                    ['Tests requested', 'requested_tests']].map(([label, key]) => (
                    <tr key={key}>
                      <td className="border p-2 bg-slate-50 text-xs font-semibold">{label}</td>
                      {comparison.columns.map((c) => (
                        <td key={c.opinion_request_id} className={`border p-2 ${c.conflicts_flagged && key === 'recommended_modality' ? 'bg-red-50 font-medium' : ''}`}>
                          {c[key] || '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>

      <section className="card">
        <div className="flex justify-between items-center mb-2">
          <h2 className="font-semibold">4. Case packages (immutable snapshots)</h2>
          <button className="btn-secondary" onClick={genPackage}>Generate new version</button>
        </div>
        <p className="text-xs text-slate-500 mb-2">
          A package freezes the case state at generation time. New information means a new version — snapshots are never edited.
        </p>
        <ul className="text-sm">
          {packages.map((p) => (
            <li key={p.id} className="flex items-center gap-3 py-1 border-b last:border-b-0 flex-wrap">
              <span className="font-medium">v{p.version_number}</span>
              <span className="text-xs text-slate-400">{new Date(p.generated_at).toLocaleString()}</span>
              <div className="ml-auto flex gap-1">
                <button className="btn-secondary" onClick={() => downloadFile(`/packages/${p.id}/pdf`, `case-package-v${p.version_number}.pdf`)}>PDF</button>
                <ShareButtons pkgId={p.id} />
              </div>
            </li>
          ))}
          {packages.length === 0 && <li className="text-slate-500">None yet.</li>}
        </ul>
      </section>
    </div>
  )
}

function ShareButtons({ pkgId }) {
  const [share, setShare] = useState(null)
  const [copied, setCopied] = useState(false)

  const createLink = async () => {
    try {
      const r = await api(`/packages/${pkgId}/share-link`, { method: 'POST' })
      const url = `${window.location.origin}${r.share_path}`
      setShare(url)
      if (navigator.share) {
        navigator.share({ title: 'Second-opinion case package', url })
          .catch(() => { /* user cancelled — link stays visible to copy */ })
      }
    } catch (e) { alert(e.message) }
  }

  return (
    <>
      {!share
        ? <button className="btn-primary" onClick={createLink} title="Read-only link a doctor can open without an account">Share link</button>
        : <>
            <input readOnly value={share} onFocus={(e) => e.target.select()}
                   className="input !w-56 !py-1 text-xs" />
            <button className="btn-secondary" onClick={() => { navigator.clipboard.writeText(share); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </>}
    </>
  )
}

function StatusChip({ status, overdue }) {
  const colors = {
    drafted: 'bg-slate-100 text-slate-600',
    sent: 'bg-blue-100 text-blue-700',
    acknowledged: 'bg-yellow-100 text-yellow-700',
    opinion_received: 'bg-green-100 text-green-700',
    no_response: 'bg-red-100 text-red-700',
    declined: 'bg-slate-200 text-slate-500',
  }
  return <span className={`text-xs rounded px-2 py-0.5 font-medium ${colors[status] || 'bg-slate-100'}`}>{status}{overdue ? ' (overdue)' : ''}</span>
}

function RespondForm({ onSave }) {
  const [form, setForm] = useState({ opinion_recommended_modality: '', opinion_sequencing_note: '', opinion_caveats: '', opinion_requested_tests: '' })
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  return (
    <div className="mt-2 border rounded p-3 bg-slate-50 grid grid-cols-1 md:grid-cols-2 gap-2">
      <div className="md:col-span-2"><label className="label">Recommended modality * (e.g., "Surgery first", "Chemoradiation")</label>
        <input className="input" value={form.opinion_recommended_modality} onChange={set('opinion_recommended_modality')} /></div>
      <div><label className="label">Sequencing note</label><textarea className="input" rows={2} value={form.opinion_sequencing_note} onChange={set('opinion_sequencing_note')} /></div>
      <div><label className="label">Caveats</label><textarea className="input" rows={2} value={form.opinion_caveats} onChange={set('opinion_caveats')} /></div>
      <div className="md:col-span-2"><label className="label">Tests requested by this doctor</label>
        <input className="input" value={form.opinion_requested_tests} onChange={set('opinion_requested_tests')} /></div>
      <button className="btn-primary" disabled={!form.opinion_recommended_modality}
        onClick={() => onSave({ ...form, opinion_recommended_modality: form.opinion_recommended_modality })}>
        Save opinion
      </button>
    </div>
  )
}
