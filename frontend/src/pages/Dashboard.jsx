import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, downloadFile } from '../api.js'
import { ErrorBox } from '../components/Layout.jsx'
import { useAuth } from '../auth.jsx'
import { COUNTRIES } from '../countries.js'

const empty = { patient_name: '', cancer_type: '', patient_age: '', patient_sex: 'unknown', stage: '', diagnosis_date: '', current_status: '', country: 'IN' }

export default function Dashboard() {
  const [cases, setCases] = useState([])
  const [form, setForm] = useState(empty)
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const { email, logout } = useAuth()

  const load = () => api('/cases').then(setCases).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const create = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const body = {
        ...form,
        patient_age: form.patient_age ? Number(form.patient_age) : null,
        diagnosis_date: form.diagnosis_date || null,
      }
      const c = await api('/cases', { method: 'POST', body })
      setForm(empty); setShowForm(false)
      navigate(`/cases/${c.id}`)
    } catch (err) { setError(err.message) }
  }

  const deleteCase = async (e, caseId, patientName) => {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm(`Permanently delete case "${patientName}" and all associated documents and packages?`)) return
    try {
      await api(`/cases/${caseId}`, { method: 'DELETE' })
      load()
    } catch (err) { setError(err.message) }
  }

  const deleteAccount = async () => {
    if (!window.confirm('This permanently deletes your account, all cases, documents and files (DPDP right to erasure). Continue?')) return
    if (!window.confirm('Are you absolutely sure? This cannot be undone.')) return
    try {
      await api('/me', { method: 'DELETE' })
      logout(); navigate('/login')
    } catch (err) { setError(err.message) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-bold">My cases</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New case'}
        </button>
      </div>
      <ErrorBox error={error} />

      {showForm && (
        <form onSubmit={create} className="card mb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div><label className="label">Patient name *</label><input className="input" value={form.patient_name} onChange={set('patient_name')} required /></div>
          <div><label className="label">Cancer type * (e.g., "Non-small cell lung cancer")</label><input className="input" value={form.cancer_type} onChange={set('cancer_type')} required /></div>
          <div><label className="label">Age</label><input className="input" type="number" value={form.patient_age} onChange={set('patient_age')} /></div>
          <div><label className="label">Sex</label>
            <select className="input" value={form.patient_sex} onChange={set('patient_sex')}>
              {['female', 'male', 'other', 'unknown'].map((s) => <option key={s}>{s}</option>)}
            </select></div>
          <div><label className="label">Stage</label><input className="input" placeholder="IIIB" value={form.stage} onChange={set('stage')} /></div>
          <div><label className="label">Diagnosis date</label><input className="input" type="date" value={form.diagnosis_date} onChange={set('diagnosis_date')} /></div>
          <div><label className="label">Patient's country (personalises My Plan)</label>
            <select className="input" value={form.country} onChange={set('country')}>
              {COUNTRIES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
            </select></div>
          <div className="md:col-span-2"><label className="label">Current status / treatment plan (free text — drives decision-risk flags)</label>
            <textarea className="input" rows={2} value={form.current_status} onChange={set('current_status')} /></div>
          <div className="md:col-span-2 text-[11px] text-slate-400">
            Why we ask exactly these fields: the decision-flag engine matches published guideline
            risks against them (e.g., radiation started before biomarker testing). All of it stays
            private to your account — never sold or shared.
          </div>
          <div><button className="btn-primary">Create case</button></div>
        </form>
      )}

      {cases.length === 0 && !showForm && (
        <div className="card text-slate-500 text-sm">No cases yet. Click “+ New case” to create one.</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {cases.map((c) => (
          <div key={c.id} className="card hover:shadow-md transition-shadow relative flex flex-col justify-between">
            <Link to={`/cases/${c.id}`} className="block">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold text-slate-800 text-base">{c.patient_name}</div>
                  <div className="text-sm text-slate-600">{c.cancer_type}{c.stage ? ` · Stage ${c.stage}` : ''}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    {c.document_count} document(s) · {c.country || 'Global'}
                  </div>
                </div>
                {c.open_flags > 0 && (
                  <span className="bg-red-100 text-red-700 border border-red-200 rounded px-2 py-1 text-xs font-semibold">
                    {c.open_flags} open flag{c.open_flags > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </Link>
            <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <Link to={`/cases/${c.id}`} className="text-blue-600 font-medium hover:underline">
                Open case file →
              </Link>
              <button
                className="text-slate-400 hover:text-red-600 py-0.5 px-1.5 rounded transition-colors"
                onClick={(e) => deleteCase(e, c.id, c.patient_name)}
                title="Delete this case"
              >
                Delete case
              </button>
            </div>
          </div>
        ))}
      </div>

      <section className="card mt-6">
        <h2 className="font-semibold mb-1">Account &amp; your data rights (DPDP Act 2023)</h2>
        <p className="text-xs text-slate-500 mb-3">Signed in as {email}. Your consent was recorded at signup; you can withdraw it here as easily as you gave it.</p>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={() => downloadFile('/me/export', 'my-data.json').catch((e) => setError(e.message))}>
            Download my data (JSON)
          </button>
          <button className="btn-danger" onClick={deleteAccount}>Delete my account &amp; all data</button>
        </div>
      </section>
    </div>
  )
}
