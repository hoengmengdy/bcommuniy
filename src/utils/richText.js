// Turns post text into safe HTML for v-html.
// Posts may be plain text (line breaks, links, ``` code fences, **bold**) or formatted HTML
// pasted from an editor. HTML is rebuilt from a whitelist, so scripts, event handlers,
// styles and javascript: links never reach the page.

const ALLOWED = new Set(['p', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 's', 'a', 'code', 'pre',
  'blockquote', 'h3', 'h4'])
const RENAME = { h1: 'h3', h2: 'h3', h5: 'h4', h6: 'h4', div: 'p' }
// Removed together with everything inside them.
const DROP = new Set(['script', 'style', 'iframe', 'object', 'embed', 'svg', 'math', 'template', 'noscript',
  'form', 'input', 'textarea', 'button', 'select', 'link', 'meta', 'head', 'title', 'img', 'video', 'audio'])
const LOOKS_LIKE_HTML = /<\/?(p|br|ul|ol|li|strong|b|em|i|u|s|a|code|pre|blockquote|h[1-6]|div|span)\b[^>]*>/i
const URL = /\bhttps?:\/\/[^\s<]+[^\s<.,;:!?)'"]/g

const escape = text => text.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

function safeHref(href) {
  const value = (href || '').trim()
  return /^(https?:|mailto:)/i.test(value) ? value : null
}

function linkify(escaped) {
  return escaped.replace(URL, url => `<a href="${url}" target="_blank" rel="noopener noreferrer nofollow">${url}</a>`)
}

function cleanNode(node, insideLink) {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = escape(node.textContent)
    return insideLink ? text : linkify(text)
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return ''
  const name = node.tagName.toLowerCase()
  if (DROP.has(name)) return ''
  const tag = RENAME[name] || name
  const isLink = tag === 'a'
  const inner = [...node.childNodes].map(child => cleanNode(child, insideLink || isLink)).join('')
  if (!ALLOWED.has(tag)) return inner // Unknown wrappers (span, font…) keep their text only.
  if (tag === 'br') return '<br>'
  if (isLink) {
    const href = safeHref(node.getAttribute('href'))
    if (!href || insideLink) return inner
    return `<a href="${escape(href)}" target="_blank" rel="noopener noreferrer nofollow">${inner}</a>`
  }
  return `<${tag}>${inner}</${tag}>`
}

function sanitizeHtml(html) {
  // DOMParser builds an inert document: nothing in it runs or loads.
  const doc = new DOMParser().parseFromString(html, 'text/html')
  return [...doc.body.childNodes].map(node => cleanNode(node, false)).join('')
}

function inline(text) {
  return linkify(escape(text))
    .replace(/`([^`\n]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
}

function plainToHtml(text) {
  // ``` fences become code blocks; everything else becomes paragraphs with line breaks.
  return text.replace(/\r\n?/g, '\n').split(/```[^\n]*\n?/).map((part, index) => {
    if (index % 2) return part.trim() ? `<pre><code>${escape(part.replace(/\n$/, ''))}</code></pre>` : ''
    return part.split(/\n{2,}/).map(block => block.trim())
      .filter(Boolean)
      .map(block => `<p>${inline(block).replace(/\n/g, '<br>')}</p>`)
      .join('')
  }).join('')
}

export function renderRichText(text) {
  if (!text) return ''
  return LOOKS_LIKE_HTML.test(text) ? sanitizeHtml(text) : plainToHtml(text)
}
