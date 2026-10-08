<script setup>
import { ref, onMounted } from 'vue'
import { useUsersStore } from '@/stores/users'
import { useUiStore } from '@/stores/ui'

const usersStore = useUsersStore()
const uiStore = useUiStore()

onMounted(() => usersStore.fetchUsers())

const showCreateModal = ref(false)
const newUser = ref({
  name: '',
  email: '',
  role: 'User',
  password: ''
})

const handleCreateUser = async () => {
  if (newUser.value.name && newUser.value.email) {
    const created = await usersStore.addUser(newUser.value)
    if (!created) return
    uiStore.addToast(`User ${newUser.value.name} created successfully`, 'success')
    showCreateModal.value = false
    newUser.value = { name: '', email: '', role: 'User', password: '' }
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="users-dashboard">
    <div class="dashboard-header">
      <div>
        <h1>User Management</h1>
        <p class="text-muted">Manage community members and roles</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18" style="margin-right: 8px;">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        Create User
      </button>
    </div>

    <div class="glass-panel table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Email</th>
            <th>Role</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in usersStore.users" :key="user.id">
            <td>
              <div class="user-info">
                <img :src="user.avatar" class="avatar-sm" alt="" />
                <span class="user-name">{{ user.name }}</span>
              </div>
            </td>
            <td class="text-muted">{{ user.email }}</td>
            <td>
              <span class="role-badge" :class="user.role.toLowerCase()">{{ user.role }}</span>
            </td>
            <td class="text-muted">{{ formatDate(user.joinDate) }}</td>
            <td>
              <button class="icon-btn delete-btn" @click="usersStore.deleteUser(user.id)" title="Delete User">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 6h18"></path>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="glass-panel modal-content animate-fade-in">
        <div class="modal-header">
          <h2>Create New User</h2>
          <button class="close-btn" @click="showCreateModal = false">✕</button>
        </div>
        
        <form @submit.prevent="handleCreateUser" class="create-form">
          <div class="input-group">
            <label>Full Name</label>
            <input type="text" v-model="newUser.name" class="input-field" placeholder="Jane Doe" required />
          </div>
          
          <div class="input-group">
            <label>Email Address</label>
            <input type="email" v-model="newUser.email" class="input-field" placeholder="jane@example.com" required />
          </div>
          
          <div class="input-group">
            <label>Role</label>
            <select v-model="newUser.role" class="input-field">
              <option value="User">User</option>
              <option value="Admin">Admin</option>
            </select>
          </div>
          
          <div class="input-group">
            <label>Initial Password</label>
            <input type="password" v-model="newUser.password" minlength="8" maxlength="128" class="input-field" placeholder="••••••••" required />
            <span style="font-size: 0.8rem; color: #6b7280; margin-top: 4px;">Use a unique password of at least 8 characters.</span>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
            <button type="submit" class="btn btn-primary">Create User</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.users-dashboard {
  animation: fadeIn 0.4s ease-out;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 2rem;
  margin: 0;
}

.table-container {
  overflow-x: auto;
  padding: 1rem;
}

.users-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 0.5rem;
}

.users-table th {
  text-align: left;
  padding: 1rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.users-table td {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(4px);
}

.users-table tr td:first-child {
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
}

.users-table tr td:last-child {
  border-top-right-radius: 12px;
  border-bottom-right-radius: 12px;
}

.users-table tr:hover td {
  background: rgba(255, 255, 255, 0.7);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.avatar-sm {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f1f5f9;
}

.user-name {
  font-weight: 600;
}

.role-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 100px;
  font-size: 0.8rem;
  font-weight: 700;
}

.role-badge.admin {
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.role-badge.user {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.icon-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  width: 100%;
  max-width: 500px;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.85);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #6b7280;
}

.close-btn:hover {
  color: #111827;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.input-group label {
  font-size: 0.9rem;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(0,0,0,0.05);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
