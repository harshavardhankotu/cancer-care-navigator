import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { DisclaimerBar, ErrorBox } from '../components/Layout.jsx'
import { COUNTRIES } from '../countries.js'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [country, setCountry] = useState('')
  const [consent, setConsent] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await register(email, password, country); navigate('/') }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm">
        <h1 className="text-lg font-bold mb-1">Create family account</h1>
        <ErrorBox error={error} />
        <div className="mb-2"><label className="label">Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        <div className="mb-2"><label className="label">Password (6+ characters)</label>
          <input className="input" type="password" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        <div className="mb-2"><label className="label">Your country (personalises centres &amp; schemes)</label>
          <select className="input" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">Prefer not to say</option>
            {COUNTRIES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select></div>

        <label className="flex gap-2 items-start text-xs text-slate-600 my-3 cursor-pointer">
          <input type="checkbox" className="mt-0.5" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
          <span>
            I give free, specific, informed consent (DPDP Act 2023) to process: <strong>my email,
            the case details I enter, and documents I upload</strong> — for the sole purpose of
            organising our case file, flagging guideline-sourced questions, and preparing second-opinion
            packages. My data is never sold or shared. I can export or delete everything at any time
            from Account settings. I have read the{' '}
            <a className="text-blue-600 underline" href="/privacy" target="_blank">privacy notice</a> and{' '}
            <a className="text-blue-600 underline" href="/terms" target="_blank">terms</a>.
          </span>
        </label>
        <p className="text-[10px] text-slate-400 -mt-1 mb-2">
          Adding a patient under 18? You confirm you are their parent or lawful guardian.
        </p>

        <button className="btn-primary w-full" disabled={busy || !consent}>{busy ? '…' : 'Create account'}</button>
        <p className="text-xs text-slate-500 mt-3">Already registered? <a className="text-blue-600 underline" href="/login">Log in</a></p>
      </form>
      <DisclaimerBar />
    </div>
  )
}
