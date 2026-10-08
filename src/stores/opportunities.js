import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiAction, apiList } from '../services/api.js'

export const useOpportunitiesStore = defineStore('opportunities', () => {
  const jobs = ref([])
  const events = ref([])
  const load = () => apiAction(async () => {
    const result = await Promise.all([apiList('/jobs'), apiList('/events')])
    ;[jobs.value, events.value] = result
    return true
  })
  return { jobs, events, load }
})
