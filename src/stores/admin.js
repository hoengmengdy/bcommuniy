import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api, apiAction, apiList } from '../services/api.js'

// Administrator-only tools. Every endpoint here returns 403 for regular members.
export const useAdminStore = defineStore('admin', () => {
  const stats = ref(null)
  const posts = ref([])
  const comments = ref([])
  const content = ref({ articles: [], jobs: [], events: [] })

  for (const event of ['bcommunity-session-expired', 'bcommunity-session-changed']) {
    globalThis.addEventListener?.(event, () => {
      stats.value = null
      posts.value = []
      comments.value = []
      content.value = { articles: [], jobs: [], events: [] }
    })
  }

  const fetchStats = (days = 14) => apiAction(async () => {
    stats.value = (await api('/admin/stats?days=' + days)).data
    return stats.value
  })

  // Accounts
  const resetPassword = (id, password) =>
    apiAction(async () => (await api(`/admin/users/${id}/password`, { method: 'POST', body: { password } })).data)
  const forceLogout = id =>
    apiAction(async () => (await api(`/admin/users/${id}/logout`, { method: 'POST' })).data)
  const setReputation = (id, reputation) =>
    apiAction(async () => (await api(`/admin/users/${id}/reputation`, { method: 'PUT', body: { reputation } })).data)
  const updateUser = (id, body) =>
    apiAction(async () => (await api('/users/' + id, { method: 'PUT', body })).data)
  const bulkUsers = (ids, action) =>
    apiAction(async () => (await api('/admin/users/bulk', { method: 'POST', body: { ids, action } })).data)

  // Moderation
  const fetchPosts = () => apiAction(async () => (posts.value = await apiList('/posts')))
  const deletePost = id => apiAction(async () => {
    await api('/posts/' + id, { method: 'DELETE' })
    posts.value = posts.value.filter(post => post.id !== id)
    return true
  })
  const bulkDeletePosts = ids => apiAction(async () => {
    const result = (await api('/admin/posts/bulk-delete', { method: 'POST', body: { ids } })).data
    const removed = new Set(ids)
    posts.value = posts.value.filter(post => !removed.has(post.id))
    return result
  })
  const toggleSolved = id => apiAction(async () => {
    const post = (await api(`/admin/posts/${id}/solved`, { method: 'POST' })).data
    posts.value = posts.value.map(item => (item.id === id ? post : item))
    return post
  })
  const fetchComments = () => apiAction(async () => (comments.value = await apiList('/admin/comments')))
  const deleteComment = id => apiAction(async () => {
    await api('/comments/' + id, { method: 'DELETE' })
    comments.value = comments.value.filter(c => c.id !== id && c.parentId !== id)
    return true
  })

  // Articles, jobs and events
  const fetchContent = kind => apiAction(async () => (content.value[kind] = await apiList('/' + kind)))
  const createContent = (kind, body) => apiAction(async () => {
    const item = (await api('/' + kind, { method: 'POST', body })).data
    content.value[kind].unshift(item)
    return item
  })
  const updateContent = (kind, id, body) => apiAction(async () => {
    const item = (await api(`/${kind}/${id}`, { method: 'PUT', body })).data
    content.value[kind] = content.value[kind].map(existing => (existing.id === id ? item : existing))
    return item
  })
  const deleteContent = (kind, id) => apiAction(async () => {
    await api(`/${kind}/${id}`, { method: 'DELETE' })
    content.value[kind] = content.value[kind].filter(item => item.id !== id)
    return true
  })

  const broadcast = (message, push) =>
    apiAction(async () => (await api('/admin/broadcast', { method: 'POST', body: { message, push } })).data)

  return {
    stats, posts, comments, content,
    fetchStats, resetPassword, forceLogout, setReputation, updateUser, bulkUsers,
    fetchPosts, deletePost, bulkDeletePosts, toggleSolved, fetchComments, deleteComment,
    fetchContent, createContent, updateContent, deleteContent, broadcast,
  }
})

// Shared helpers for admin screens.
export function downloadCsv(filename, rows) {
  if (!rows.length) return
  const columns = Object.keys(rows[0])
  const cell = value => {
    const text = Array.isArray(value) ? value.join('; ') : String(value ?? '')
    // Prefix formula-like values so spreadsheets never execute them.
    const safe = /^[=+\-@\t\r]/.test(text) ? "'" + text : text
    return '"' + safe.replace(/"/g, '""') + '"'
  }
  const csv = [columns.join(','), ...rows.map(row => columns.map(key => cell(row[key])).join(','))].join('\r\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }))
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(link.href), 1000)
}

export const plainText = html => String(html || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()

export function randomPassword() {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
  const bytes = crypto.getRandomValues(new Uint8Array(14))
  return Array.from(bytes, byte => alphabet[byte % alphabet.length]).join('')
}
