import { useUiStore } from '../stores/ui.js'

const API_URL = (import.meta.env?.VITE_API_URL || '/api').replace(/\/$/, '')
let token = globalThis.sessionStorage?.getItem('bcommunity-token') || ''
let expiresAt = Number(globalThis.sessionStorage?.getItem('bcommunity-token-expires-at')) || 0
let expiryTimer
let sessionVersion = 0

function scheduleExpiry() {
  clearTimeout(expiryTimer)
  if (!token || !expiresAt) return
  const remaining = expiresAt - Date.now()
  if (remaining <= 0) return expireSession()
  expiryTimer = setTimeout(scheduleExpiry, Math.min(remaining, 2147483647))
  expiryTimer.unref?.()
}

export function setToken(value, expiration = 0) {
  const nextToken = value || ''
  if (nextToken !== token) sessionVersion++
  token = nextToken
  if (token) globalThis.sessionStorage?.setItem('bcommunity-token', token)
  else globalThis.sessionStorage?.removeItem('bcommunity-token')
  setSessionExpiry(expiration)
}

export function setSessionExpiry(expiration) {
  expiresAt = token && Number.isFinite(Number(expiration)) ? Number(expiration) : 0
  if (expiresAt > 0) globalThis.sessionStorage?.setItem('bcommunity-token-expires-at', String(expiresAt))
  else globalThis.sessionStorage?.removeItem('bcommunity-token-expires-at')
  scheduleExpiry()
}

export function expireSession() {
  setToken('')
  globalThis.dispatchEvent?.(new Event('bcommunity-session-expired'))
}

export function hasToken() {
  if (token && expiresAt && expiresAt <= Date.now()) expireSession()
  return Boolean(token)
}
export const getSessionVersion = () => sessionVersion

export async function api(endpoint, { method = 'GET', body, ...options } = {}) {
  const publicRequest = method.toUpperCase() === 'POST' && endpoint === '/auth/login'
  if (!publicRequest && !hasToken()) {
    const error = new Error('Please sign in to continue.')
    error.status = 401
    throw error
  }
  const requestToken = publicRequest ? '' : token
  const requestVersion = sessionVersion
  const response = await fetch(API_URL + endpoint, {
    ...options,
    cache: 'no-store',
    method,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(requestToken ? { Authorization: 'Bearer ' + requestToken } : {}),
      ...options.headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })
  // A late response from the previous session must never refill protected stores
  // or sign out a different user. Logout deliberately clears the local token first.
  if (!publicRequest && endpoint !== '/auth/logout' && requestVersion !== sessionVersion) {
    const error = new Error('The session changed. Please try again.')
    error.code = 'SESSION_CHANGED'
    throw error
  }
  if (response.status === 401 && requestToken && requestVersion === sessionVersion) expireSession()
  let result
  try { result = await response.json() }
  catch { throw new Error('The API returned an invalid response. Check that Flask is running.') }
  if (!response.ok) {
    const error = new Error(result.error?.message || 'API request failed.')
    error.status = response.status
    throw error
  }
  // Reading the body can also overlap logout or a new login.
  if (!publicRequest && endpoint !== '/auth/logout' && requestVersion !== sessionVersion) {
    const error = new Error('The session changed. Please try again.')
    error.code = 'SESSION_CHANGED'
    throw error
  }
  return result
}

export async function apiList(endpoint) {
  const rows = []
  let page = 1
  while (true) {
    const separator = endpoint.includes('?') ? '&' : '?'
    const response = await api(endpoint + separator + 'page=' + page + '&per_page=100')
    rows.push(...response.data)
    if (!response.meta || rows.length >= response.meta.total || !response.data.length) return rows
    page++
  }
}

export async function apiAction(callback) {
  try { return await callback() }
  catch (error) {
    if (error.status !== 401 && error.code !== 'SESSION_CHANGED') {
      useUiStore().addToast(error.message || 'Unable to reach the API. Start the Flask backend.', 'error')
    }
    return null
  }
}
