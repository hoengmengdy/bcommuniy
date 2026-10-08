import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const toasts = ref([])
  let toastIdCounter = 0

  function addToast(message, type = 'success') {
    const id = toastIdCounter++
    const toast = { id, message, type }
    toasts.value.push(toast)

    setTimeout(() => {
      removeToast(id)
    }, 3000) // Toast disappears after 3 seconds
  }

  function removeToast(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  return {
    toasts,
    addToast,
    removeToast
  }
})
