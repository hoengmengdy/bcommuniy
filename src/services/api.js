import { useUiStore } from '../stores/ui.js'

const API_URL = (import.meta.env?.VITE_API_URL || '/api').replace(/\/$/, '')
let token = globalThis.sessionStorage?.getItem('bcommunity-token') || ''

export function setToken(value) {
  token = value || ''
  if (token) globalThis.sessionStorage?.setItem('bcommunity-token', token)
  else globalThis.sessionStorage?.removeItem('bcommunity-token')
}
export const hasToken = () => Boolean(token)

export async function api(endpoint, { method = 'GET', body, ...options } = {}) {
  const response = await fetch(API_URL + endpoint, {
    ...options,
    method,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
      ...options.headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })
  let result
  try { result = await response.json() }
  catch { throw new Error('The API returned an invalid response. Check that Flask is running.') }
  if (!response.ok) {
    if (response.status === 401) {
      setToken('')
      globalThis.dispatchEvent?.(new Event('bcommunity-session-expired'))
    }
    const error = new Error(result.error?.message || 'API request failed.')
    error.status = response.status
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
    useUiStore().addToast(error.message || 'Unable to reach the API. Start the Flask backend.', 'error')
    return null
  }
}
