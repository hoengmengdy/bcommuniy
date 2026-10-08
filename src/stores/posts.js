import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api, apiAction, apiList, hasToken, setToken } from '../services/api.js'

export const usePostsStore = defineStore('posts', () => {
  const posts = ref([])
  const currentUser = ref(null)
  let initialization
  globalThis.addEventListener?.('bcommunity-session-expired', () => { currentUser.value = null })

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
  async function initialize() {
    if (!initialization) initialization = (async () => {
      if (hasToken()) {
        try { currentUser.value = (await api('/auth/me')).data }
        catch { setToken(''); currentUser.value = null }
      }
      await apiAction(fetchPosts)
    })()
    return initialization
  }
  async function authenticate(mode, data) {
    const response = await api('/auth/' + mode, { method: 'POST', body: data })
    setToken(response.data.token)
    currentUser.value = response.data.user
    globalThis.dispatchEvent?.(new Event('bcommunity-session-changed'))
    await apiAction(fetchPosts)
    return currentUser.value
  }
  const logout = () => apiAction(async () => {
    await api('/auth/logout', { method: 'POST' })
    setToken('')
    currentUser.value = null
    globalThis.dispatchEvent?.(new Event('bcommunity-session-changed'))
    return true
  })
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
  return { posts, currentUser, getPostById, initialize, fetchPosts, fetchPost, authenticate,
    logout, addPost, addComment, likePost, updateProfile, markAsSolved }
})
