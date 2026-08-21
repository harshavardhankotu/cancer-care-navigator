// Minimal offline shell: app pages load even on flaky connections.
// API calls are NEVER cached (health data must be fresh; privacy).
const CACHE = 'ccn-shell-v1'
const SHELL = ['/', '/index.html', '/manifest.webmanifest']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)))
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)
  if (url.pathname.startsWith('/api/')) return // network only
  event.respondWith(
    caches.match(event.request).then(
      (hit) =>
        hit ||
        fetch(event.request)
          .then((res) => {
            const copy = res.clone()
            caches.open(CACHE).then((c) => c.put(event.request, copy))
            return res
          })
          .catch(() => caches.match('/index.html')),
    ),
  )
})
