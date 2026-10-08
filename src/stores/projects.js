import { defineStore } from 'pinia'
import { api, apiAction, apiList } from '../services/api.js'

export const useProjectsStore = defineStore('projects', {
  state: () => ({ members: [], tasks: [] }),
  actions: {
    load() {
      return apiAction(async () => {
        const [members, tasks] = await Promise.all([apiList('/members'), apiList('/tasks')])
        this.members = members
        this.tasks = tasks
        return true
      })
    },
    addTask(taskData) {
      return apiAction(async () => {
        const task = (await api('/tasks', { method: 'POST', body: taskData })).data
        this.tasks.push(task)
        return task
      })
    },
    updateTaskStatus(taskId, status) {
      return apiAction(async () => {
        const task = (await api('/tasks/' + taskId, { method: 'PUT', body: { status } })).data
        const index = this.tasks.findIndex(t => t.id === taskId)
        if (index >= 0) this.tasks[index] = task
        return task
      })
    },
  },
})
