import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api, apiAction, apiList, expireSession, getSessionVersion, hasToken, setToken, setSessionExpiry } from '../services/api.js'

export const usePostsStore = defineStore('posts', () => {
  const posts = ref([])
  const currentUser = ref(null)
  let initialization
  let verification
  globalThis.addEventListener?.('bcommunity-session-expired', () => {
    currentUser.value = null
    posts.value = []
    initialization = undefined
  })
  globalThis.addEventListener?.('bcommunity-session-changed', () => { posts.value = [] })

  const getPostById = computed(() => id => posts.value.find(post => post.id === id))
  function replacePost(post) {
    const index = posts.value.findIndex(item => item.id === post.id)
    if (index < 0) posts.value.unshift(post)
    else posts.value[index] = post
    return post
  }
  async function fetchPosts() {
    posts.value = await apiList('/posts')
    return posts.value
  }
  async function validateSession() {
    if (!hasToken()) {
      currentUser.value = null
      posts.value = []
      return false
    }
    const version = getSessionVersion()
    if (verification?.version === version) return verification.promise
    const promise = (async () => {
      try {
        const response = await api('/auth/me')
        if (version !== getSessionVersion()) return false
        setSessionExpiry(response.meta.expiresAt)
        if (!hasToken()) return false
        currentUser.value = response.data
        return true
      } catch {
        // Network failures also fail closed; an unverified session cannot render content.
        if (version === getSessionVersion()) expireSession()
        return false
      } finally {
        if (verification?.version === version) verification = undefined
      }
    })()
    verification = { version, promise }
    return promise
  }
  async function initialize() {
    if (!hasToken()) return false
    if (!initialization) initialization = (async () => {
      if (!currentUser.value && !await validateSession()) return false
      await apiAction(fetchPosts)
      return Boolean(currentUser.value)
    })()
    return initialization
  }
  // Registration creates an account without granting a session. Login is required next.
  const registerAccount = data => api('/auth/register', { method: 'POST', body: data })
  async function authenticate(data) {
    const response = await api('/auth/login', { method: 'POST', body: data })
    setToken(response.data.token, response.data.expiresAt)
    if (!hasToken()) throw new Error('Your session expired. Please sign in again.')
    currentUser.value = response.data.user
    globalThis.dispatchEvent?.(new Event('bcommunity-session-changed'))
    await apiAction(fetchPosts)
    return currentUser.value
  }
  function logout() {
    const pending = hasToken() ? api('/auth/logout', { method: 'POST' }) : Promise.resolve()
    // Remove access immediately, even when the revocation request is slow or fails.
    expireSession()
    return apiAction(async () => { await pending; return true })
  }
  const addPost = (content, tag = '#General', codeSnippet = null, codeLanguage = 'javascript',
    isQuestion = false, imageUrl = null, projectUrl = null) => apiAction(async () => {
    const response = await api('/posts', { method: 'POST', body: {
      content, tag, codeSnippet, codeLanguage, isQuestion, image: imageUrl, projectUrl,
    } })
    return replacePost(response.data)
  })
  const addComment = (postId, text, parentId = null, codeSnippet = null,
    codeLanguage = 'javascript') => apiAction(async () => {
    const response = await api('/posts/' + postId + '/comments', { method: 'POST',
      body: { text, parentId, codeSnippet, codeLanguage } })
    await fetchPost(postId)
    return response.data
  })
  async function fetchPost(id) {
    return replacePost((await api('/posts/' + id)).data)
  }
  const likePost = postId => apiAction(async () =>
    replacePost((await api('/posts/' + postId + '/like', { method: 'POST' })).data))
  const updateProfile = (name, bio, role, skills) => apiAction(async () => {
    currentUser.value = (await api('/profile', { method: 'PUT', body: { name, bio, role, skills } })).data
    await fetchPosts()
    return currentUser.value
  })
  const markAsSolved = (postId, commentId) => apiAction(async () =>
    replacePost((await api('/posts/' + postId + '/solve', {
      method: 'POST', body: { commentId },
    })).data))
  return { posts, currentUser, getPostById, initialize, validateSession, fetchPosts, fetchPost, authenticate, registerAccount,
    logout, addPost, addComment, likePost, updateProfile, markAsSolved }
})
