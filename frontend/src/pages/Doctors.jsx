import React, { useEffect, useState } from 'react'
import { api } from '../api.js'
import { ErrorBox, isPlaceholder, PH } from '../components/Layout.jsx'

export default function Doctors() {
  const [doctors, setDoctors] = useState([])
  const [specialty, setSpecialty] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : ''
    api(`/doctors${params}`).then(setDoctors).catch((e) => setError(e.message))
  }, [specialty])

  return (
    <div>
      <h1 className="text-xl font-bold mb-1">Doctor directory</h1>
      <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3 text-xs text-blue-900">
        <strong>Why there are no doctor rankings here:</strong> doctor ratings are easy to game
        ("bought reviews") and expose platforms to defamation claims. We only display verifiable,
        credential-level fields — checked by a human curator against public registers such as the{' '}
        <a className="underline" href="https://www.nmc.org.in/information-desk/indian-medical-register/" target="_blank" rel="noreferrer">
          NMC Indian Medical Register ↗</a>. All entries below are role-level placeholders until
        that curation happens.
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Filter by specialty; sort order below is alphabetical, not a ranking.
      </p>
      <ErrorBox error={error} />
      <div className="card mb-4"><label className="label">Filter by specialty</label>
        <input className="input max-w-xs" placeholder="e.g., oncology, breast" value={specialty} onChange={(e) => setSpecialty(e.target.value)} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {doctors.map((d) => (
          <div key={d.id} className="card">
            <div className="font-semibold">{d.name}{isPlaceholder(d) && <PH label="placeholder — not a real individual" />}</div>
            <div className="text-sm text-slate-600">{d.credentials} · {d.hospital}</div>
            <div className="mt-2">{(d.specialty_tags || []).map((t) => <span key={t} className="chip">{t}</span>)}</div>
            <p className="text-xs text-slate-400 mt-2">
              Remote case review: {d.accepts_remote_case_review ? 'yes' : 'no'} · typical response ~{d.avg_response_time_days} days
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
