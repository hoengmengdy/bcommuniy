// Cards slide in as they scroll into view. Works for lists that load later too,
// because a MutationObserver picks up new cards as Vue renders them.
const CARD_SELECTOR = [
  '.post-card',
  '.question-card',
  '.review-card',
  '.mentor-card',
  '.category-card',
  '.stat-card',
  '.mission-card',
  '.sidebar-card',
].join(',')

const STAGGER_MS = 70
const MAX_STAGGER_MS = 350

export function startReveal(root = document.body) {
  if (typeof window === 'undefined' || !('IntersectionObserver' in window)) return
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

  const seen = new WeakSet()

  const io = new IntersectionObserver(entries => {
    // Stagger cards that appear together, in the order they are on screen.
    const visible = entries.filter(e => e.isIntersecting)
    visible.forEach((entry, i) => {
      const el = entry.target
      const delay = Math.min(i * STAGGER_MS, MAX_STAGGER_MS)
      el.style.setProperty('--reveal-delay', `${delay}ms`)
      el.classList.add('is-visible')
      io.unobserve(el)
      // Drop the delay once the card is in, so hover effects respond instantly.
      setTimeout(() => el.style.removeProperty('--reveal-delay'), delay + 600)
    })
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 })

  const track = el => {
    if (seen.has(el)) return
    seen.add(el)
    el.classList.add('reveal')
    io.observe(el)
  }

  const scan = node => {
    if (!(node instanceof Element)) return
    if (node.matches(CARD_SELECTOR)) track(node)
    node.querySelectorAll(CARD_SELECTOR).forEach(track)
  }

  scan(root)
  new MutationObserver(mutations => {
    for (const m of mutations) m.addedNodes.forEach(scan)
  }).observe(root, { childList: true, subtree: true })
}
