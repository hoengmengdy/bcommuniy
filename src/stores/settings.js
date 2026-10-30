import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { messages } from '@/i18n'

// Theme (light/dark) and language (km/en) are per device, so they live in localStorage.
// index.html applies the saved values before the first paint; this store keeps them in sync.
const read = (key, fallback) => {
  try {
    return localStorage.getItem(key) || fallback
  } catch {
    return fallback
  }
}
const save = (key, value) => {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Private mode: the choice still applies for this visit.
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const root = document.documentElement
  const theme = ref(root.dataset.theme === 'dark' ? 'dark' : 'light')
  const lang = ref(read('bcommunity-lang', 'km') === 'en' ? 'en' : 'km')

  watch(theme, value => {
    root.dataset.theme = value
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', value === 'dark' ? '#11131c' : '#6d28d9')
    save('bcommunity-theme', value)
  }, { immediate: true })

  watch(lang, value => {
    root.lang = value
    save('bcommunity-lang', value)
  }, { immediate: true })

  const toggleTheme = () => { theme.value = theme.value === 'dark' ? 'light' : 'dark' }
  const setLang = value => { lang.value = value }

  // t('nav.search') → text in the current language; {name} placeholders are filled from params.
  function t(key, params = {}) {
    const text = messages[lang.value]?.[key] ?? messages.en[key] ?? key
    return text.replace(/\{(\w+)\}/g, (_, name) => params[name] ?? '')
  }

  return { theme, lang, toggleTheme, setLang, t }
})
