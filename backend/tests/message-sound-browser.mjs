// Uses intercepted API fixtures only; does not sign in or modify production data.
import assert from 'node:assert/strict'
import { chromium, expect } from '@playwright/test'

const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true })
try {
  const page = await browser.newPage({ serviceWorkers: 'block' })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.addInitScript(() => {
    localStorage.setItem('bcommunity-token', 'browser-fixture')
    localStorage.setItem('bcommunity-token-expires-at', String(Date.now() + 3600000))
    localStorage.setItem('bcommunity-message-sound', 'off')
    window.chimeNotes = 0
    const create = AudioContext.prototype.createOscillator
    AudioContext.prototype.createOscillator = function (...args) {
      window.chimeNotes++
      return create.apply(this, args)
    }
  })
  const user = { id: 1, name: 'Sound Test', avatar: '', isAdmin: false }
  const chat = { id: 1, name: 'Other Member', avatar: '', participantIds: [1, 2],
    time: new Date().toISOString(), lastMessage: 'Old message', unread: 0,
    messages: [{ id: 1, senderId: 2, text: 'Old message', status: 'read', type: 'text' }] }
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname
    let data = []
    if (path === '/api/auth/me') data = user
    if (path === '/api/conversations') data = [chat]
    if (path === '/api/conversations/1') data = chat
    if (path === '/api/members') data = [user, { id: 2, name: 'Other Member' }]
    await route.fulfill({ json: { data, meta: { total: Array.isArray(data) ? data.length : 1, expiresAt: Date.now() + 3600000 } } })
  })
  await page.goto((process.env.FRONTEND_ORIGIN || 'https://bcommuniy-main.vercel.app') + '/messages')
  await page.bringToFront()
  await page.getByRole('button', { name: 'Turn on message sound' }).click()
  await expect(page.getByRole('button', { name: 'Message sound on' })).toBeVisible()
  await expect.poll(() => page.evaluate(() => window.chimeNotes)).toBe(2)
  // Clear the preview count, then verify the same sound plays for a received message.
  await page.evaluate(() => { window.chimeNotes = 0 })
  chat.messages.push({ id: 2, senderId: 2, text: 'New incoming message', status: 'sent', type: 'text' })
  chat.lastMessage = 'New incoming message'; chat.unread = 1
  await expect.poll(() => page.evaluate(() => window.chimeNotes), { timeout: 8000 }).toBe(2)
  // Change pages: global listening continues while viewing the feed.
  await page.getByRole('link', { name: 'Bcommunity', exact: true }).click()
  chat.messages.push({ id: 3, senderId: 2, text: 'Incoming on feed', status: 'sent', type: 'text' })
  await expect.poll(() => page.evaluate(() => window.chimeNotes), { timeout: 8000 }).toBe(4)
  // A fresh chat route preserves the preference, then mute stops further chimes.
  await page.locator('a[href="/messages"]').first().click()
  await page.getByRole('button', { name: 'Message sound on' }).click()
  chat.messages.push({ id: 4, senderId: 2, text: 'Muted incoming', status: 'sent', type: 'text' })
  await page.waitForTimeout(2300)
  assert.equal(await page.evaluate(() => window.chimeNotes), 4)
  assert.equal(await page.evaluate(() => localStorage.getItem('bcommunity-message-sound')), 'off')
  assert.deepEqual(errors, [])
  console.log('PASS: real browser audio unlock, preview, incoming chime, listening on feed, and mute.')
} finally {
  await browser.close()
}
