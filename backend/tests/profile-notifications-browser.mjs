// Intercepts all API calls and browser push APIs; never sends a real notification.
import assert from 'node:assert/strict'
import { chromium, expect } from '@playwright/test'

const browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true })
const origin = process.env.FRONTEND_ORIGIN || 'https://bcommuniy-main.vercel.app'
const user = { id: 1, name: 'Profile Test', avatar: '', isAdmin: false, skills: [] }

async function openProfile({ iphone = false, denied = false } = {}) {
  const page = await browser.newPage({ serviceWorkers: 'block', viewport: { width: 390, height: 844 },
    ...(iphone ? { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1' } : {}) })
  const requests = []
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.addInitScript(({ denied }) => {
    localStorage.setItem('bcommunity-token', 'browser-fixture')
    localStorage.setItem('bcommunity-token-expires-at', String(Date.now() + 3600000))
    let permission = denied ? 'denied' : 'default'
    let subscription = null
    window.permissionPrompts = 0
    window.Notification = class {
      static get permission() { return permission }
      static async requestPermission() { window.permissionPrompts++; permission = 'granted'; return permission }
    }
    const registration = { pushManager: {
      getSubscription: async () => subscription,
      subscribe: async () => {
        subscription = { endpoint: 'https://push.example.com/test-device',
          toJSON: () => ({ endpoint: 'https://push.example.com/test-device', keys: { auth: 'test', p256dh: 'test' } }),
          unsubscribe: async () => { subscription = null; return true } }
        return subscription
      },
    } }
    Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: {
      getRegistration: async () => registration,
      register: async () => registration,
      ready: Promise.resolve(registration),
    } })
  }, { denied })
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname
    requests.push([route.request().method(), path])
    let data = []
    if (path === '/api/auth/me') data = user
    if (path === '/api/users/2') data = { ...user, id: 2, name: 'Another Member' }
    if (path === '/api/push/key') data = { publicKey: 'BA' + 'A'.repeat(85) }
    await route.fulfill({ json: { data, meta: { total: Array.isArray(data) ? data.length : 1, expiresAt: Date.now() + 3600000 } } })
  })
  await page.goto(origin + '/profile')
  return { page, requests, errors }
}

try {
  const { page, requests, errors } = await openProfile()
  const toggle = page.getByRole('switch')
  await expect(toggle).toHaveAttribute('aria-checked', 'false')
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-checked', 'true')
  assert.equal(await page.evaluate(() => window.permissionPrompts), 1)
  assert.ok(requests.some(([method, path]) => method === 'POST' && path === '/api/push/subscriptions'))
  await page.screenshot({ path: 'profile-notifications-mobile.png', fullPage: true })
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-checked', 'false')
  assert.ok(requests.some(([method, path]) => method === 'DELETE' && path === '/api/push/subscriptions'))
  await page.goto(origin + '/profile/2')
  await expect(page.getByRole('heading', { name: 'Another Member', exact: true })).toBeVisible()
  await expect(page.getByRole('switch')).toHaveCount(0)
  assert.deepEqual(errors, [])
  await page.close()

  const blocked = await openProfile({ denied: true })
  await expect(blocked.page.getByText('ការជូនដំណឹងត្រូវបានបិទដោយទូរស័ព្ទ។', { exact: false })).toBeVisible()
  await expect(blocked.page.getByRole('switch')).toHaveCount(0)
  assert.equal(await blocked.page.evaluate(() => window.permissionPrompts), 0)
  await blocked.page.close()

  const iphone = await openProfile({ iphone: true })
  await expect(iphone.page.getByText('នៅលើ iPhone៖', { exact: false })).toBeVisible()
  await expect(iphone.page.getByRole('switch')).toHaveCount(0)
  assert.deepEqual(iphone.errors, [])
  await iphone.page.close()
  console.log('PASS: own-profile push on/off, server subscription cleanup, mobile layout, public-profile privacy, denied permission and iPhone installation guidance.')
} finally {
  await browser.close()
}
