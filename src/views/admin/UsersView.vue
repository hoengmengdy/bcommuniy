<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useUsersStore } from '@/stores/users'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import { downloadCsv, randomPassword, useAdminStore } from '@/stores/admin'

const usersStore = useUsersStore()
const admin = useAdminStore()
const ui = useUiStore()
const me = computed(() => usePostsStore().currentUser)

const loading = ref(true)
onMounted(async () => {
  await usersStore.fetchUsers()
  loading.value = false
})

// Filters and sorting
const search = ref('')
const roleFilter = ref('all')
const statusFilter = ref('all')
const sortKey = ref('joinDate')
const sortDir = ref(-1)
const sortBy = key => {
  if (sortKey.value === key) sortDir.value *= -1
  else { sortKey.value = key; sortDir.value = key === 'name' || key === 'email' ? 1 : -1 }
}
const arrow = key => (sortKey.value === key ? (sortDir.value > 0 ? ' ▲' : ' ▼') : '')

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return usersStore.users
    .filter(user => roleFilter.value === 'all' || user.role === roleFilter.value)
    .filter(user => statusFilter.value === 'all' || user.status === statusFilter.value)
    .filter(user => !q || [user.name, user.email, user.phone, ...(user.skills || [])]
      .some(value => String(value || '').toLowerCase().includes(q)))
    .sort((a, b) => {
      const x = a[sortKey.value] ?? '', y = b[sortKey.value] ?? ''
      return (typeof x === 'number' ? x - y : String(x).localeCompare(String(y))) * sortDir.value
    })
})

// Selection and bulk actions
const selected = ref(new Set())
const allSelected = computed(() => filtered.value.length > 0 && filtered.value.every(u => selected.value.has(u.id)))
const toggle = id => {
  const next = new Set(selected.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selected.value = next
}
const toggleAll = () => {
  selected.value = allSelected.value ? new Set() : new Set(filtered.value.map(u => u.id))
}
const bulkLabels = {
  activate: 'activate', deactivate: 'deactivate', promote: 'make admin', demote: 'remove admin from',
  logout: 'sign out', delete: 'permanently delete',
}
const runBulk = async action => {
  const ids = [...selected.value]
  if (!ids.length) return
  if (!window.confirm(`Really ${bulkLabels[action]} ${ids.length} user(s)?`)) return
  const result = await admin.bulkUsers(ids, action)
  if (!result) return
  ui.addToast(`${result.affected} user(s) updated`, 'success')
  selected.value = new Set()
  await usersStore.fetchUsers()
}

const replaceUser = user => {
  if (user) usersStore.users = usersStore.users.map(u => (u.id === user.id ? user : u))
}

// Create
const showCreate = ref(false)
const blankUser = () => ({ name: '', email: '', role: 'User', password: randomPassword() })
const newUser = ref(blankUser())
const openCreate = () => { newUser.value = blankUser(); showCreate.value = true }
const handleCreate = async () => {
  const created = await usersStore.addUser(newUser.value)
  if (!created) return
  ui.addToast(`User ${created.name} created`, 'success')
  showCreate.value = false
}

// Edit
const editing = ref(null)
const openEdit = user => {
  editing.value = { id: user.id, name: user.name, email: user.email, role: user.role,
                    status: user.status, reputation: user.reputation ?? 0, original: user }
}
const saveEdit = async () => {
  const form = editing.value, original = form.original, changes = {}
  for (const key of ['name', 'email', 'role', 'status']) if (form[key] !== original[key]) changes[key] = form[key]
  let user = original
  if (Object.keys(changes).length) {
    user = await admin.updateUser(form.id, changes)
    if (!user) return
  }
  if (Number(form.reputation) !== original.reputation) {
    user = await admin.setReputation(form.id, Number(form.reputation))
    if (!user) return
  }
  replaceUser(user)
  ui.addToast('User saved', 'success')
  editing.value = null
}

// Password reset
const resetting = ref(null)
const openReset = user => { resetting.value = { user, password: randomPassword(), done: false } }
const doReset = async () => {
  const user = await admin.resetPassword(resetting.value.user.id, resetting.value.password)
  if (!user) return
  replaceUser(user)
  resetting.value.done = true
  ui.addToast('Password changed — the user was signed out everywhere', 'success')
}
const copy = async text => {
  try { await navigator.clipboard.writeText(text); ui.addToast('Copied', 'success') }
  catch { ui.addToast('Copy failed — select the text manually', 'error') }
}

// Quick row actions
const toggleStatus = async user => {
  const status = user.status === 'Active' ? 'Inactive' : 'Active'
  if (status === 'Inactive' && !window.confirm(`Deactivate ${user.name}? They will be signed out and cannot log in.`)) return
  const updated = await admin.updateUser(user.id, { status })
  if (updated) { replaceUser(updated); ui.addToast(`${user.name} is now ${status}`, 'success') }
}
const toggleRole = async user => {
  const role = user.role === 'Admin' ? 'User' : 'Admin'
  if (!window.confirm(role === 'Admin' ? `Give ${user.name} full admin access?` : `Remove admin access from ${user.name}?`)) return
  const updated = await admin.updateUser(user.id, { role })
  if (updated) { replaceUser(updated); ui.addToast(`${user.name} is now ${role}`, 'success') }
}
const forceLogout = async user => {
  if (!window.confirm(`Sign ${user.name} out of every device?`)) return
  if (await admin.forceLogout(user.id)) ui.addToast(`${user.name} was signed out`, 'success')
}
const removeUser = async user => {
  if (!window.confirm(`Permanently delete ${user.name} and all their posts, comments and chats? This cannot be undone.`)) return
  if (await usersStore.deleteUser(user.id)) ui.addToast(`${user.name} deleted`, 'success')
}

const exportCsv = () => downloadCsv(`users-${new Date().toISOString().slice(0, 10)}.csv`,
  filtered.value.map(u => ({ id: u.id, name: u.name, email: u.email, phone: u.phone, role: u.role,
    status: u.status, profileRole: u.profileRole, reputation: u.reputation, skills: u.skills, joined: u.joinDate })))

const formatDate = iso => (iso ? new Date(iso).toLocaleDateString() : '')
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Users</h1>
        <p class="text-muted">Accounts, roles, access and passwords</p>
      </div>
      <div class="adm-actions">
        <button class="adm-btn" @click="exportCsv" :disabled="!filtered.length">Export CSV</button>
        <button class="adm-btn primary" @click="openCreate">+ Create user</button>
      </div>
    </div>

    <div class="glass-panel adm-toolbar">
      <input v-model="search" type="search" class="input-field adm-search" placeholder="Search name, email, phone, skill…" aria-label="Search users" />
      <select v-model="roleFilter" class="input-field" aria-label="Filter by role">
        <option value="all">All roles</option>
        <option value="Admin">Admins</option>
        <option value="User">Users</option>
      </select>
      <select v-model="statusFilter" class="input-field" aria-label="Filter by status">
        <option value="all">All statuses</option>
        <option value="Active">Active</option>
        <option value="Inactive">Inactive</option>
      </select>
      <span class="adm-count">{{ filtered.length }} of {{ usersStore.users.length }} users</span>
    </div>

    <div v-if="selected.size" class="adm-bulkbar">
      <span>{{ selected.size }} selected</span>
      <button class="adm-btn" @click="runBulk('activate')">Activate</button>
      <button class="adm-btn" @click="runBulk('deactivate')">Deactivate</button>
      <button class="adm-btn" @click="runBulk('promote')">Make admin</button>
      <button class="adm-btn" @click="runBulk('demote')">Remove admin</button>
      <button class="adm-btn" @click="runBulk('logout')">Sign out</button>
      <button class="adm-btn danger" @click="runBulk('delete')">Delete</button>
      <button class="adm-btn" @click="selected = new Set()">Clear</button>
    </div>

    <div class="glass-panel adm-table-wrap">
      <table class="adm-table">
        <thead>
          <tr>
            <th><input type="checkbox" :checked="allSelected" @change="toggleAll" aria-label="Select all" /></th>
            <th class="sortable" @click="sortBy('name')">User{{ arrow('name') }}</th>
            <th class="sortable" @click="sortBy('role')">Role{{ arrow('role') }}</th>
            <th class="sortable" @click="sortBy('status')">Status{{ arrow('status') }}</th>
            <th class="sortable num" @click="sortBy('reputation')">Rep.{{ arrow('reputation') }}</th>
            <th class="sortable" @click="sortBy('joinDate')">Joined{{ arrow('joinDate') }}</th>
            <th class="num">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filtered" :key="user.id" :class="{ selected: selected.has(user.id) }">
            <td><input type="checkbox" :checked="selected.has(user.id)" @change="toggle(user.id)" :aria-label="`Select ${user.name}`" /></td>
            <td>
              <div class="adm-user">
                <img :src="user.avatar" alt="" />
                <div>
                  <strong>{{ user.name }} <span v-if="user.id === me?.id" class="adm-badge">You</span></strong>
                  <small>{{ user.email }}</small>
                </div>
              </div>
            </td>
            <td><span class="adm-badge" :class="user.role === 'Admin' ? 'indigo' : 'green'">{{ user.role }}</span></td>
            <td><span class="adm-badge" :class="user.status === 'Active' ? 'green' : 'red'">{{ user.status }}</span></td>
            <td class="num">{{ user.reputation }}</td>
            <td class="nowrap text-muted">{{ formatDate(user.joinDate) }}</td>
            <td>
              <div class="adm-cell-actions">
                <RouterLink :to="`/profile/${user.id}`" class="adm-icon-btn" title="View profile" aria-label="View profile">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </RouterLink>
                <button class="adm-icon-btn" title="Edit user" aria-label="Edit user" @click="openEdit(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                </button>
                <button class="adm-icon-btn" title="Reset password" aria-label="Reset password" @click="openReset(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </button>
                <button class="adm-icon-btn" :title="user.role === 'Admin' ? 'Remove admin' : 'Make admin'" :aria-label="user.role === 'Admin' ? 'Remove admin' : 'Make admin'"
                  :disabled="user.id === me?.id" @click="toggleRole(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </button>
                <button class="adm-icon-btn" :title="user.status === 'Active' ? 'Deactivate' : 'Activate'" :aria-label="user.status === 'Active' ? 'Deactivate' : 'Activate'"
                  :disabled="user.id === me?.id" @click="toggleStatus(user)">
                  <svg v-if="user.status === 'Active'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M4.9 4.9l14.2 14.2"/></svg>
                  <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>
                </button>
                <button class="adm-icon-btn" title="Sign out everywhere" aria-label="Sign out everywhere"
                  :disabled="user.id === me?.id" @click="forceLogout(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
                </button>
                <button class="adm-icon-btn danger" title="Delete user" aria-label="Delete user"
                  :disabled="user.id === me?.id" @click="removeUser(user)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="adm-empty">Loading users…</div>
      <div v-else-if="!filtered.length" class="adm-empty">No users match these filters.</div>
    </div>

    <!-- Create -->
    <div v-if="showCreate" class="adm-overlay" @click.self="showCreate = false">
      <div class="adm-modal" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <div class="adm-modal-head">
          <h2 id="create-title">Create user</h2>
          <button class="adm-icon-btn" aria-label="Close" @click="showCreate = false">✕</button>
        </div>
        <form class="adm-form" @submit.prevent="handleCreate">
          <label>Full name<input v-model="newUser.name" class="input-field" required maxlength="120" /></label>
          <label>Email<input v-model="newUser.email" type="email" class="input-field" required /></label>
          <label>Role
            <select v-model="newUser.role" class="input-field"><option>User</option><option>Admin</option></select>
          </label>
          <label>Initial password
            <div class="pw-row">
              <input v-model="newUser.password" class="input-field" minlength="8" maxlength="128" required />
              <button type="button" class="adm-btn" @click="newUser.password = randomPassword()">Generate</button>
              <button type="button" class="adm-btn" @click="copy(newUser.password)">Copy</button>
            </div>
            <span class="hint">Share it with the user privately. 8–128 characters.</span>
          </label>
          <div class="adm-form-foot">
            <button type="button" class="adm-btn" @click="showCreate = false">Cancel</button>
            <button type="submit" class="adm-btn primary">Create user</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit -->
    <div v-if="editing" class="adm-overlay" @click.self="editing = null">
      <div class="adm-modal" role="dialog" aria-modal="true" aria-labelledby="edit-title">
        <div class="adm-modal-head">
          <h2 id="edit-title">Edit {{ editing.original.name }}</h2>
          <button class="adm-icon-btn" aria-label="Close" @click="editing = null">✕</button>
        </div>
        <form class="adm-form" @submit.prevent="saveEdit">
          <label>Display name<input v-model.trim="editing.name" class="input-field" required maxlength="120" /></label>
          <label>Email<input v-model.trim="editing.email" type="email" class="input-field" required /></label>
          <div class="adm-form-row">
            <label>Account role
              <select v-model="editing.role" class="input-field" :disabled="editing.id === me?.id">
                <option>User</option><option>Admin</option>
              </select>
            </label>
            <label>Status
              <select v-model="editing.status" class="input-field" :disabled="editing.id === me?.id">
                <option>Active</option><option>Inactive</option>
              </select>
            </label>
          </div>
          <label>Reputation points<input v-model.number="editing.reputation" type="number" min="0" class="input-field" /></label>
          <div class="adm-form-foot">
            <button type="button" class="adm-btn" @click="editing = null">Cancel</button>
            <button type="submit" class="adm-btn primary">Save changes</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Reset password -->
    <div v-if="resetting" class="adm-overlay" @click.self="resetting = null">
      <div class="adm-modal" role="dialog" aria-modal="true" aria-labelledby="reset-title">
        <div class="adm-modal-head">
          <h2 id="reset-title">Reset password — {{ resetting.user.name }}</h2>
          <button class="adm-icon-btn" aria-label="Close" @click="resetting = null">✕</button>
        </div>
        <form class="adm-form" @submit.prevent="doReset">
          <label>New password
            <div class="pw-row">
              <input v-model="resetting.password" class="input-field" minlength="8" maxlength="128" required :readonly="resetting.done" />
              <button v-if="!resetting.done" type="button" class="adm-btn" @click="resetting.password = randomPassword()">Generate</button>
              <button type="button" class="adm-btn" @click="copy(resetting.password)">Copy</button>
            </div>
            <span class="hint">The user is signed out of every device and must log in with this password.</span>
          </label>
          <div class="adm-form-foot">
            <button type="button" class="adm-btn" @click="resetting = null">{{ resetting.done ? 'Done' : 'Cancel' }}</button>
            <button v-if="!resetting.done" type="submit" class="adm-btn primary">Set password</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pw-row { display: flex; gap: 0.4rem; }
.pw-row .input-field { flex: 1; min-width: 0; font-family: ui-monospace, monospace; }
.adm-icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
