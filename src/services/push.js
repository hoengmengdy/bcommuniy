// Chat notifications via Web Push. iPhone needs iOS 16.4+ and the app added to the Home Screen.
import { api } from './api.js'

const isIos = () => /iphone|ipad|ipod/i.test(navigator.userAgent)
  || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
const isStandalone = () => window.matchMedia?.('(display-mode: standalone)').matches || navigator.standalone === true

export const pushSupported = () => 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window

// iPhone Safari only offers push after "Add to Home Screen"; tell people instead of hiding the option.
export const needsHomeScreenInstall = () => isIos() && !isStandalone()

export function registerServiceWorker() {
  if (!('serviceWorker' in navigator) || !import.meta.env.PROD) return
  navigator.serviceWorker.register('/sw.js').catch(() => {})
}

function keyBytes(base64url) {
  const base64 = (base64url + '='.repeat((4 - (base64url.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/')
  return Uint8Array.from(atob(base64), c => c.charCodeAt(0))
}

export async function pushEnabled() {
  if (!pushSupported() || Notification.permission !== 'granted') return false
  const registration = await navigator.serviceWorker.getRegistration()
  return Boolean(await registration?.pushManager.getSubscription())
}

// Must run from a tap: browsers only show the permission prompt after a user gesture.
export async function enablePush() {
  if (!pushSupported()) throw new Error('This browser cannot show notifications.')
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') throw new Error('Notifications are blocked. Allow them in your phone settings.')
  const { publicKey } = (await api('/push/key')).data
  if (!publicKey) throw new Error('Notifications are not set up on the server yet.')
  const registration = await navigator.serviceWorker.register('/sw.js')
  await navigator.serviceWorker.ready
  const subscription = await registration.pushManager.getSubscription()
    || await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(publicKey) })
  await api('/push/subscriptions', { method: 'POST', body: subscription.toJSON() })
  return true
}

// A profile switch explicitly turns off notifications for this browser/device.
export async function turnOffPush() {
  const registration = await navigator.serviceWorker?.getRegistration()
  const subscription = await registration?.pushManager.getSubscription()
  if (!subscription) return
  await api('/push/subscriptions', { method: 'DELETE', body: { endpoint: subscription.endpoint } })
  if (!await subscription.unsubscribe()) throw new Error('Could not turn off notifications. Please try again.')
}

// On sign-out, stop this device receiving the previous user's messages.
export async function disablePush() {
  try {
    const registration = await navigator.serviceWorker?.getRegistration()
    await (await registration?.pushManager.getSubscription())?.unsubscribe()
  } catch {
    // Nothing to clean up, or the browser refused; the server drops dead subscriptions on next send.
  }
}
