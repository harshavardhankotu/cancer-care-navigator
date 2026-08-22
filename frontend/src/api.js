const TOKEN_KEY = 'ccn_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY))

export async function api(path, { method = 'GET', body, formData } = {}) {
  const headers = {}
  if (!formData && body !== undefined) headers['Content-Type'] = 'application/json'
  if (getToken()) headers['Authorization'] = `Bearer ${getToken()}`
  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: formData ? formData : body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (res.status === 401 && getToken()) {
    setToken(null)
    window.location.href = '/login'
    throw new Error('Session expired — please log in again.')
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`
    try { msg = (await res.json()).detail || msg } catch { /* keep default */ }
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res.blob()
}

export async function downloadFile(path, filename) {
  const blob = await api(path)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  setTimeout(() => {
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, 100)
}
