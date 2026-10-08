<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  initialName: String,
  initialBio: String,
  initialRole: String,
  initialSkills: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'save'])

const editName = ref(props.initialName)
const editBio = ref(props.initialBio)
const editRole = ref(props.initialRole || 'Beginner')
const editSkills = ref(props.initialSkills ? props.initialSkills.join(', ') : '')

function handleSave() {
  emit('save', {
    name: editName.value,
    bio: editBio.value,
    role: editRole.value,
    skills: editSkills.value.split(',').map(s => s.trim()).filter(s => s)
  })
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Edit Profile</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>
      
      <div class="modal-body">
        <div class="form-group">
          <label>Display Name</label>
          <input type="text" v-model="editName" class="form-input" />
        </div>
        
        <div class="form-group">
          <label>Bio</label>
          <textarea v-model="editBio" class="form-input" rows="4"></textarea>
        </div>
        
        <div class="form-group">
          <label>Role</label>
          <select v-model="editRole" class="form-input">
            <option value="Beginner">Beginner (សិស្សថ្មី)</option>
            <option value="Senior">Senior (សិស្សច្បង)</option>
            <option value="Teacher">Teacher (គ្រូ)</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Skills (comma separated)</label>
          <input type="text" v-model="editSkills" class="form-input" placeholder="e.g. Vue.js, Python, CSS" />
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button class="btn-save" @click="handleSave">Save Changes</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
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
  z-index: 9999;
}

.modal-content {
  background: #ffffff;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  box-shadow: none;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #0f172a;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #94a3b8;
  cursor: pointer;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #475569;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  outline: none;
}

.form-input:focus {
  border-color: #7c3aed;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-cancel, .btn-save {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.btn-cancel {
  background: #f1f5f9;
  border: none;
  color: #475569;
}

.btn-cancel:hover {
  background: #e2e8f0;
}

.btn-save {
  background: #7c3aed;
  border: none;
  color: white;
}

.btn-save:hover {
  background: #6d28d9;
}
</style>
