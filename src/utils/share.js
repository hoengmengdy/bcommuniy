// Sharing a post: the phone's share sheet (Messenger, Telegram, copy link…), or copy the link on desktop.

export const postUrl = post => `${window.location.origin}/post/${post.id}`

export function postSnippet(post, length = 80) {
  const text = (post.title || post.content || (post.codeSnippet ? 'Code snippet' : 'Photo')).replace(/\s+/g, ' ').trim()
  return text.length > length ? text.slice(0, length - 1) + '…' : text
}

// Returns 'shared', 'copied', or null if the person closed the share sheet.
export async function sharePost(post) {
  const url = postUrl(post)
  if (navigator.share) {
    try {
      await navigator.share({ title: 'Bcommunity', text: postSnippet(post), url })
      return 'shared'
    } catch (error) {
      if (error?.name === 'AbortError') return null
    }
  }
  try {
    await navigator.clipboard.writeText(url)
    return 'copied'
  } catch {
    // Clipboard API is unavailable on HTTP and can be denied in embedded browsers.
    const focused = document.activeElement
    const input = document.createElement('textarea')
    input.value = url
    input.readOnly = true
    input.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none'
    document.body.appendChild(input)
    try {
      input.focus()
      input.select()
      input.setSelectionRange(0, url.length)
      if (document.execCommand?.('copy')) return 'copied'
    } catch {
      // A browser may expose the legacy API but still reject copying.
    } finally {
      input.remove()
      focused?.focus({ preventScroll: true })
    }
  }
  // Still let the member copy/share the link when both clipboard methods are blocked.
  window.prompt('Copy this link to share the post:', url)
  return null
}
