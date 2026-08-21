import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import { DisclaimerBar, ErrorBox } from '../components/Layout.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await login(email, password); navigate('/') }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  const tryDemo = async () => {
    setBusy(true); setError(null)
    try { await login('demo@navigator.app', 'demo1234'); navigate('/') }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={submit} className="card w-full max-w-sm">
        <h1 className="text-lg font-bold mb-1">Log in</h1>
        <p className="text-xs text-slate-500 mb-3">Family account — all cases and documents are private to your account.</p>
        <ErrorBox error={error} />
        <div className="mb-2"><label className="label">Email</label>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        <div className="mb-3"><label className="label">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        <button className="btn-primary w-full" disabled={busy}>{busy ? '…' : 'Log in'}</button>
        <button type="button" className="btn-secondary w-full mt-2" onClick={tryDemo} disabled={busy}>
          Try demo (sample case, no signup)
        </button>
        <p className="text-xs text-slate-500 mt-3">No account? <a className="text-blue-600 underline" href="/register">Register</a></p>
        <p className="text-xs text-slate-500">
          Free tools, no account needed:{' '}
          <a className="text-blue-600 underline" href="/coverage-check">Quick coverage check</a> ·{' '}
          <a className="text-blue-600 underline" href="/centers">Centres directory</a>
        </p>
      </form>
      <DisclaimerBar />
    </div>
  )
}
