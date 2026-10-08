<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  members: Array
})

const emit = defineEmits(['close', 'create'])

const title = ref('')
const description = ref('')
const assigneeId = ref('')

const handleSubmit = () => {
  if (!title.value || !assigneeId.value) return

  emit('create', {
    title: title.value,
    description: description.value,
    assigneeId: assigneeId.value,
    status: 'todo'
  })

  // Reset form
  title.value = ''
  description.value = ''
  assigneeId.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Create New Task</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="task-form">
        <div class="form-group">
          <label>Task Title</label>
          <input 
            v-model="title" 
            type="text" 
            placeholder="What needs to be done?" 
            required 
            autoFocus
          />
        </div>

        <div class="form-group">
          <label>Description</label>
          <textarea 
            v-model="description" 
            placeholder="Add some details..."
            rows="3"
          ></textarea>
        </div>

        <div class="form-group">
          <label>Assignee</label>
          <select v-model="assigneeId" required>
            <option value="" disabled>Select a team member</option>
            <option v-for="member in members" :key="member.id" :value="member.id">
              {{ member.name }}
            </option>
          </select>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="$emit('close')">Cancel</button>
          <button type="submit" class="btn-submit" :disabled="!title || !assigneeId">Create Task</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  width: 90%;
  max-width: 500px;
  border-radius: 24px;
  padding: 2rem;
  box-shadow: none;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
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
  font-weight: 700;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #4b5563;
}

.task-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #374151;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #7c3aed;
  box-shadow: none;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
}

.btn-cancel {
  background: white;
  border: 1px solid #d1d5db;
  color: #4b5563;
  padding: 0.75rem 1.5rem;
  border-radius: 100px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: #f9fafb;
}

.btn-submit {
  background: #7c3aed;
  border: none;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 100px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: #6d28d9;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
