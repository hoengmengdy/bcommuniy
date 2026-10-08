// Starts isolated Flask/Vite servers and uses a temporary database.
// Requires the backend venv and installed Chrome (or PLAYWRIGHT_CHANNEL).
import assert from 'node:assert/strict'
import { randomBytes, randomUUID } from 'node:crypto'
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdtemp, rm } from 'node:fs/promises'
import { createServer as createNetServer } from 'node:net'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { setTimeout as delay } from 'node:timers/promises'
import { chromium, expect } from '@playwright/test'
import { createServer } from 'vite'

const built = process.argv.includes('--built')
const root = fileURLToPath(new URL('../../', import.meta.url))
const directory = await mkdtemp(path.join(tmpdir(), 'bcommunity-auth-'))
const portReservation = createNetServer()
portReservation.listen(0, '127.0.0.1')
await once(portReservation, 'listening')
const backendPort = portReservation.address().port
await new Promise(resolve => portReservation.close(resolve))
const backendOrigin = `http://127.0.0.1:${backendPort}`
const password = randomUUID()
const adminPassword = randomUUID()
const python = process.env.PYTHON || path.join(root, 'backend', 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const backend = spawn(python, ['-u', '-c', `
import os
from backend.app import create_app
from backend.extensions import db
from backend.services.auth import create_user
app = create_app({"TESTING": True, "RATELIMIT_ENABLED": False})
with app.app_context():
    db.create_all()
    create_user({"name": "Test Admin", "email": "admin@example.com", "password": os.environ["AUTH_TEST_ADMIN_PASSWORD"], "role": "Admin"}, admin=True)
    create_user({"name": "Existing Browser Member", "email": "member@example.com", "password": os.environ["AUTH_TEST_MEMBER_PASSWORD"]})
    db.session.commit()
if os.environ["AUTH_TEST_BUILT_FRONTEND"] == "1":
    from waitress import serve
    serve(app, host="127.0.0.1", port=${backendPort})
else:
    app.run(host="127.0.0.1", port=${backendPort}, use_reloader=False)
`], {
  cwd: root, windowsHide: true,
  env: { ...process.env, SECRET_KEY: randomBytes(32).toString('hex'),
    DATABASE_URL: 'sqlite:///' + path.join(directory, 'test.db').replaceAll('\\', '/'),
    TOKEN_MAX_AGE: '86400', AUTH_TEST_BUILT_FRONTEND: built ? '1' : '0', AUTH_TEST_ADMIN_PASSWORD: adminPassword, AUTH_TEST_MEMBER_PASSWORD: password },
  stdio: ['ignore', 'pipe', 'pipe'],
})
let logs = '', backendError
backend.stdout.on('data', chunk => { logs += chunk })
backend.stderr.on('data', chunk => { logs += chunk })
backend.on('error', error => { backendError = error })
let vite, browser
try {
  let ready = false
  for (let attempt = 0; attempt < 150; attempt++) {
    if (backendError || backend.exitCode !== null) throw backendError || new Error(logs)
    try { ready = (await fetch(backendOrigin + '/api/health')).status === 401 } catch {}
    if (ready) break
    await delay(100)
  }
  assert.ok(ready, 'Isolated backend must start: ' + logs)
  let origin = backendOrigin
  if (!built) {
    vite = await createServer({ root, server: { port: 0, strictPort: false,
      proxy: { '/api': { target: backendOrigin, changeOrigin: true } } } })
    await vite.listen()
    origin = `http://127.0.0.1:${vite.httpServer.address().port}`
  }
  console.log(built ? 'Testing built frontend and API served together by Waitress.' : 'Testing Vite frontend with proxied Flask API.')
  browser = await chromium.launch({ channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true })
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  const paths = ['/', '/questions', '/knowledge', '/reviews', '/mentorship', '/leaderboard',
    '/profile', '/messages', '/post/1', '/admin', '/admin/users']
  for (const protectedPath of paths) {
    await page.goto(origin + protectedPath)
    await expect(page).toHaveURL(/\/auth\?redirect=/)
    await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
    await expect(page.locator('.navbar-wrapper, .admin-layout, .home-view')).toHaveCount(0)
  }
  console.log('PASS: every direct protected URL requires login; protected UI stays hidden.')

  for (const path of ['/auth', '/register', '/signup', '/create-account', '/auth?mode=register']) {
    await page.goto(origin + path)
    await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
    await expect(page.locator('.auth-form input')).toHaveCount(2)
    await expect(page.locator('.auth-form button')).toHaveCount(1)
    await expect(page.locator('.auth-container')).not.toContainText(/create.?account|create an account|register|sign.?up/i)
  }
  assert.equal((await page.request.post(origin + '/api/auth/register', {
    data: { name: 'Uninvited', email: 'uninvited@example.com', password, confirmPassword: password },
  })).status(), 401)
  await page.goto(origin + '/questions?tab=all#answers')
  assert.equal((await page.request.post(origin + '/api/users', {
    data: { name: 'Unauthorized Admin', email: 'admin2@example.com', password },
  })).status(), 401)
  await page.getByLabel('Email Address', { exact: true }).fill('unregistered@example.com')
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await expect(page.locator('.toast-error')).toContainText('Invalid email or password.')
  await expect(page.locator('.navbar-wrapper')).toHaveCount(0)
  await page.getByLabel('Email Address', { exact: true }).fill('member@example.com')
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await expect(page).toHaveURL(origin + '/questions?tab=all#answers')
  await expect(page.getByRole('button', { name: 'Sign Out', exact: true })).toBeVisible()
  console.log('PASS: Login has no signup option; direct signup URLs and anonymous registration APIs are blocked.')
  const token = await page.evaluate(() => sessionStorage.getItem('bcommunity-token'))
  const headers = { Authorization: 'Bearer ' + token }
  assert.ok([404, 405].includes((await page.request.post(origin + '/api/auth/register', { headers, data: {} })).status()))
  const created = await page.request.post(origin + '/api/posts', { headers,
    data: { content: 'Protected browser test content' } })
  assert.equal(created.status(), 201)
  const post = (await created.json()).data
  for (const protectedPath of [...paths.filter(p => !p.startsWith('/admin') && p !== '/post/1'), '/post/' + post.id]) {
    await page.goto(origin + protectedPath)
    await expect(page).toHaveURL(origin + protectedPath)
    await expect(page.getByRole('button', { name: 'Sign Out', exact: true })).toBeVisible()
  }
  await expect(page.getByText('Protected browser test content', { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByText('Protected browser test content', { exact: true })).toBeVisible()
  assert.equal(await page.evaluate(() => sessionStorage.getItem('bcommunity-token')), token)
  await page.goto(origin + '/admin/users')
  await expect(page).toHaveURL(origin + '/')
  assert.equal((await page.request.get(origin + '/api/users', { headers })).status(), 403)
  console.log('PASS: existing-account login, content access, refresh restoration, and admin restrictions.')

  await page.goto(origin + '/profile')
  await page.getByRole('button', { name: 'Edit Profile', exact: true }).click()
  await page.getByLabel('Profile Photo', { exact: true }).setInputFiles({
    name: 'invalid.svg', mimeType: 'image/svg+xml', buffer: Buffer.from('<svg/>'),
  })
  await expect(page.getByRole('alert')).toContainText('Choose a JPEG, PNG, WebP or GIF')
  const photo = await page.evaluate(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 64; canvas.height = 64
    const context = canvas.getContext('2d')
    context.fillStyle = '#7c3aed'; context.fillRect(0, 0, 64, 64)
    return canvas.toDataURL('image/png').split(',')[1]
  })
  await page.getByLabel('Profile Photo', { exact: true }).setInputFiles({
    name: 'profile.png', mimeType: 'image/png', buffer: Buffer.from(photo, 'base64'),
  })
  await expect(page.getByAltText('Profile photo preview')).toHaveAttribute('src', /^data:image\/png;base64,/)
  await page.getByRole('button', { name: 'Save Changes', exact: true }).click()
  await expect(page.locator('.modal-backdrop')).toHaveCount(0)
  await expect(page.locator('.profile-avatar')).toHaveAttribute('src', /^data:image\/webp;base64,/)
  const storedPhoto = await page.locator('.profile-avatar').getAttribute('src')
  await page.reload()
  await expect(page.locator('.profile-avatar')).toHaveAttribute('src', storedPhoto)
  assert.equal(await page.locator('.profile-avatar').evaluate(image => image.complete && image.naturalWidth === 256), true)
  console.log('PASS: photo uploads reject SVG, save a normalized image, and survive browser refresh.')

  // Hold the logout response: the frontend must hide content immediately.
  let releaseLogout, logoutStarted
  const started = new Promise(resolve => { logoutStarted = resolve })
  await page.route('**/api/auth/logout', async route => {
    logoutStarted()
    await new Promise(resolve => { releaseLogout = resolve })
    await route.continue()
  })
  await page.getByRole('button', { name: 'Sign Out', exact: true }).click()
  await started
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
  await expect(page.locator('.navbar-wrapper, .home-view')).toHaveCount(0)
  assert.equal(await page.evaluate(() => sessionStorage.getItem('bcommunity-token')), null)
  const logoutDone = page.waitForResponse(response => response.url().endsWith('/api/auth/logout'))
  releaseLogout()
  assert.equal((await logoutDone).status(), 200)
  await page.unroute('**/api/auth/logout')
  assert.equal((await page.request.get(origin + '/api/posts', { headers })).status(), 401)
  await page.goBack()
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
  await page.goto(origin + '/post/' + post.id)
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
  console.log('PASS: logout hides content before the API finishes; revoked tokens and browser Back are blocked.')

  async function login(email, secret, target) {
    await page.goto(origin + '/auth?redirect=' + encodeURIComponent(target))
    await page.locator('input[type="email"]').fill(email)
    await page.locator('input[type="password"]').fill(secret)
    await page.getByRole('button', { name: 'Sign In', exact: true }).click()
    await expect(page).toHaveURL(origin + target)
  }
  await page.locator('input[type="email"]').fill('member@example.com')
  await page.locator('input[type="password"]').fill('incorrect-password')
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await expect(page.locator('.toast-error')).toContainText('Invalid email or password.')
  await expect(page.locator('.navbar-wrapper')).toHaveCount(0)
  await login('member@example.com', password, '/knowledge')
  await expect(page.getByRole('heading', { name: 'Knowledge Base', exact: true })).toBeVisible()
  console.log('PASS: invalid login is blocked; valid login returns to the requested page.')

  // Exercise the real expiry timer without waiting 24 hours.
  if (built) {
    await page.evaluate(() => sessionStorage.setItem('bcommunity-token-expires-at', String(Date.now() - 1)))
    await page.reload()
  } else {
    await page.evaluate(async () => {
      const { setSessionExpiry } = await import('/src/services/api.js')
      setSessionExpiry(Date.now() + 100)
    })
  }
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
  await expect(page.locator('.knowledge-container, .navbar-wrapper')).toHaveCount(0)
  console.log('PASS: session expiry redirects and hides protected content automatically.')

  await login('member@example.com', password, '/messages')
  const activeToken = await page.evaluate(() => sessionStorage.getItem('bcommunity-token'))
  assert.equal((await page.request.post(origin + '/api/auth/logout', {
    headers: { Authorization: 'Bearer ' + activeToken },
  })).status(), 200)
  await page.evaluate(() => window.dispatchEvent(new Event('focus')))
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible()
  await expect(page.locator('.messages-layout')).toHaveCount(0)
  await login('admin@example.com', adminPassword, '/admin/users')
  await expect(page.getByRole('heading', { name: 'Admin Panel', exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Admin Panel', exact: true })).toBeVisible()
  assert.deepEqual(errors, [], 'No browser runtime errors')
  console.log('PASS: server revocation is detected on focus; admin access survives refresh.')

  // Existing integration test verifies all feature stores through the same isolated servers.
  const smoke = spawn(process.execPath, [path.join(root, 'backend/tests/frontend-smoke.mjs')], {
    cwd: root, env: { ...process.env, FRONTEND_ORIGIN: origin, SMOKE_ADMIN_EMAIL: 'admin@example.com', SMOKE_ADMIN_PASSWORD: adminPassword }, windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  let smokeOutput = ''
  smoke.stdout.on('data', chunk => { smokeOutput += chunk })
  smoke.stderr.on('data', chunk => { smokeOutput += chunk })
  const [code] = await once(smoke, 'exit')
  assert.equal(code, 0, smokeOutput)
  console.log(smokeOutput.trim())
} finally {
  await browser?.close()
  await vite?.close()
  if (backend.exitCode === null && !backendError) {
    const stopped = once(backend, 'exit')
    backend.kill()
    await stopped
  }
  // Only remove the exact temporary directory created by this test.
  if (path.dirname(directory) === path.resolve(tmpdir()) && path.basename(directory).startsWith('bcommunity-auth-')) {
    await rm(directory, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 })
  }
}
