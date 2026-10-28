// Bcommunity service worker: shows chat notifications. It deliberately caches nothing,
// so the app always loads the latest version and signed-in data never lands in a cache.

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()))

self.addEventListener('push', event => {
  let data = {}
  try {
    data = event.data ? event.data.json() : {}
  } catch {
    data = { body: event.data?.text() }
  }
  event.waitUntil(self.registration.showNotification(data.title || 'Bcommunity', {
    body: data.body || 'New message',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: data.url || 'bcommunity-message',
    renotify: true,
    // Ask the OS for its notification sound, including when the app is closed.
    // Spoken announcements are controlled by the user's phone settings.
    silent: false,
    lang: 'km-KH',
    data: { url: data.url || '/messages' },
  }))
})

self.addEventListener('notificationclick', event => {
  event.notification.close()
  const url = new URL(event.notification.data?.url || '/messages', self.location.origin).href
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    const open = windows.find(client => client.url.startsWith(self.location.origin))
    if (open) {
      await open.focus()
      return open.navigate(url)
    }
    return self.clients.openWindow(url)
  })())
})
