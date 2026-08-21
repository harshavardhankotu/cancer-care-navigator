import React, { createContext, useContext, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api, getToken, setToken } from './api.js'

const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [email, setEmail] = useState(null)
  const [ready, setReady] = useState(!getToken())

  useEffect(() => {
    if (getToken()) {
      api('/auth/me')
        .then((me) => { setEmail(me.email); setReady(true) })
        .catch(() => setToken(null))
        .finally(() => setReady(true))
    }
  }, [])

  const login = async (emailArg, password) => {
    const r = await api('/auth/login', { method: 'POST', body: { email: emailArg, password } })
    setToken(r.token); setEmail(r.email)
  }
  const register = async (emailArg, password) => {
    const r = await api('/auth/register', { method: 'POST', body: { email: emailArg, password } })
    setToken(r.token); setEmail(r.email)
  }
  const logout = () => { setToken(null); setEmail(null) }

  return <AuthCtx.Provider value={{ email, login, register, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

export function RequireAuth({ children }) {
  const { email, ready } = useAuth()
  if (!ready) return <div className="p-8 text-slate-500">Loading…</div>
  if (!getToken()) return <Navigate to="/login" replace />
  return children
}
