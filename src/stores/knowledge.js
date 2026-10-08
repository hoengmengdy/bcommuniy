import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, apiAction, apiList } from '../services/api.js'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const questions = ref([])
  const articles = ref([])
  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => {
      questions.value = []
      articles.value = []
    })
  }
  const load = () => apiAction(async () => {
    const result = await Promise.all([apiList('/questions'), apiList('/articles')])
    ;[questions.value, articles.value] = result
    return true
  })
  const addQuestion = question => apiAction(async () => {
    const created = (await api('/questions', { method: 'POST', body: question })).data
    questions.value.unshift(created)
    return created
  })
  return { questions, articles, load, addQuestion }
})
