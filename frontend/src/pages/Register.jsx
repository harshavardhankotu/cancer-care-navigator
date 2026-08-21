import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { DisclaimerBar, ErrorBox } from '../components/Layout.jsx'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await register(email, password); navigate('/') }
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
        <div className="mb-3"><label className="label">Password (6+ characters)</label>
          <input className="input" type="password" minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        <button className="btn-primary w-full" disabled={busy}>{busy ? '…' : 'Register'}</button>
        <p className="text-xs text-slate-500 mt-3">Already registered? <a className="text-blue-600 underline" href="/login">Log in</a></p>
      </form>
      <DisclaimerBar />
    </div>
  )
}
