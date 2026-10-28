import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api, apiAction, apiList } from '../services/api.js'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => { users.value = [] })
  }
  const fetchUsers = () => apiAction(async () => {
    users.value = await apiList('/users')
    return users.value
  })
  const addUser = userData => apiAction(async () => {
    const user = (await api('/users', { method: 'POST', body: userData })).data
    users.value.push(user)
    return user
  })
  const deleteUser = id => apiAction(async () => {
    await api('/users/' + id, { method: 'DELETE' })
    users.value = users.value.filter(user => user.id !== id)
    return true
  })
  const renameUser = (id, name) => apiAction(async () => {
    const user = (await api('/users/' + id, { method: 'PUT', body: { name } })).data
    users.value = users.value.map(existing => (existing.id === id ? user : existing))
    return user
  })
  return { users, fetchUsers, addUser, deleteUser, renameUser }
})
