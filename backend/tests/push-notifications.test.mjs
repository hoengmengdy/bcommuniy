import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'

test('background push requests OS sound and retains Khmer title and chat destination', async () => {
  const events = {}
  let shown, pending
  // A service worker has no window or foreground page; notifications must work alone.
  const self = {
    addEventListener: (name, handler) => { events[name] = handler },
    registration: { showNotification: async (title, options) => { shown = { title, options } } },
  }
  const source = await readFile(new URL('../../public/sw.js', import.meta.url), 'utf8')
  vm.runInNewContext(source, { self })
  events.push({ data: { json: () => ({ title: 'មានគេឆាតមក', body: 'Member: Hello', url: '/messages?c=4' }) },
    waitUntil: promise => { pending = promise } })
  await pending
  assert.equal(shown.title, 'មានគេឆាតមក')
  assert.equal(shown.options.body, 'Member: Hello')
  assert.equal(shown.options.silent, false)
  assert.equal(shown.options.lang, 'km-KH')
  assert.equal(shown.options.renotify, true)
  assert.equal(shown.options.data.url, '/messages?c=4')
})
