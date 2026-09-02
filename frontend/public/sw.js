// Minimal offline shell: app pages load even on flaky connections.
// API calls are NEVER cached (health data must be fresh; privacy).
const CACHE = 'ccn-shell-v1'
const SHELL = ['/', '/index.html', '/manifest.webmanifest']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return
  const url = new URL(event.request.url)
  if (url.pathname.startsWith('/api/')) return // network only for health data (never cached)
  event.respondWith(
    caches.match(event.request).then(
      (hit) =>
        hit ||
        fetch(event.request)
          .then((res) => {
            if (!res || res.status !== 200 || res.type !== 'basic') return res
            const copy = res.clone()
            caches.open(CACHE).then((c) => c.put(event.request, copy))
            return res
          })
          .catch(() => caches.match('/index.html')),
    ),
  )
})
