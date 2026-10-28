// Friendly display for the API's ISO-8601 UTC timestamps, in the viewer's local time zone.

const toDate = value => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const sameDay = (a, b) => a.toDateString() === b.toDateString()

// "2:43 PM" today, "Yesterday 2:43 PM", "Oct 28, 2:43 PM" earlier this year, "Oct 28, 2025" before that.
export function chatTime(value) {
  const date = toDate(value)
  if (!date) return ''
  const now = new Date()
  const clock = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  if (sameDay(date, now)) return clock
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (sameDay(date, yesterday)) return 'Yesterday ' + clock
  if (date.getFullYear() === now.getFullYear()) {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ', ' + clock
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })
}

// "Just now", "5 min ago", "3 hours ago", "2 days ago", then a date.
export function timeAgo(value) {
  const date = toDate(value)
  if (!date) return ''
  const seconds = Math.max(0, (Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'Just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return chatTime(value)
}
