import React from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.jsx'

export const DISCLAIMER =
  'This is not medical advice. It organizes your records and flags questions to raise with your treating oncologist.'

export function DisclaimerBar() {
  return (
    <footer className="fixed bottom-0 inset-x-0 bg-amber-100 border-t border-amber-300 text-amber-900 text-xs px-4 py-2 text-center z-40">
      ⚠️ {DISCLAIMER}{' '}
      <Link to="/privacy" className="underline ml-2">Privacy</Link> ·{' '}
      <Link to="/terms" className="underline">Terms</Link> ·{' '}
      <Link to="/support" className="underline font-semibold text-blue-700">💙 Support us</Link>
    </footer>
  )
}

export function PH({ label = 'unverified / example data' }) {
  return (
    <span className="inline-block align-middle text-[10px] font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 border border-amber-300 rounded px-1.5 py-0.5 ml-2">
      {label}
    </span>
  )
}

export function isPlaceholder(row) {
  const marker = `${row?.verified_by || ''} ${row?.external_id || ''} ${row?.manufacturer || ''}`.toLowerCase()
  return marker.includes('placeholder') || marker.includes('seed') || marker.includes('example')
}

export function ErrorBox({ error }) {
  if (!error) return null
  return <div className="bg-red-50 border border-red-200 text-red-700 rounded p-2 my-2 text-sm">{String(error)}</div>
}

function Nav() {
  const { email, logout } = useAuth()
  const navigate = useNavigate()
  const cls = ({ isActive }) =>
    `px-3 py-1.5 rounded text-sm ${isActive ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-200'}`
  return (
    <nav className="bg-white shadow mb-4">
      <div className="max-w-6xl mx-auto flex items-center gap-1 px-4 py-2 flex-wrap">
        <Link to="/" className="font-bold text-blue-700 mr-4">Cancer Care Navigator <span className="text-xs font-normal text-slate-400">MVP</span></Link>
        <NavLink to="/" end className={cls}>My Cases</NavLink>
        <NavLink to="/centers" className={cls}>Centres</NavLink>
        <NavLink to="/doctors" className={cls}>Doctors</NavLink>
        <NavLink to="/coverage-check" className={cls}>Quick Coverage Check</NavLink>
        <div className="ml-auto flex items-center gap-2">
          {email ? (
            <>
              <span className="text-xs text-slate-500">{email}</span>
              <button className="btn-secondary" onClick={() => { logout(); navigate('/login') }}>Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-secondary">Log in</Link>
              <Link to="/register" className="btn-primary">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export default function Layout() {
  return (
    <div className="min-h-screen pb-12">
      <Nav />
      <main className="max-w-6xl mx-auto px-4">
        <Outlet />
      </main>
      <DisclaimerBar />
    </div>
  )
}
