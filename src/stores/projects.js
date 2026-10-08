import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, apiAction, apiList } from '../services/api.js'

export const useProjectsStore = defineStore('projects', () => {
  const members = ref([])
  const tasks = ref([])
  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => { members.value = []; tasks.value = [] })
  }
  const load = () => apiAction(async () => {
    const result = await Promise.all([apiList('/members'), apiList('/tasks')])
    ;[members.value, tasks.value] = result
    return true
  })
  const addTask = taskData => apiAction(async () => {
    const task = (await api('/tasks', { method: 'POST', body: taskData })).data
    tasks.value.push(task)
    return task
  })
  const updateTaskStatus = (taskId, status) => apiAction(async () => {
    const task = (await api('/tasks/' + taskId, { method: 'PUT', body: { status } })).data
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index >= 0) tasks.value[index] = task
    return task
  })
  return { members, tasks, load, addTask, updateTaskStatus }
})
