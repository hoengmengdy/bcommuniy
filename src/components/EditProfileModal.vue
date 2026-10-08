<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  isOpen: Boolean,
  initialName: String,
  initialAvatar: String,
  isSaving: Boolean,
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

const selectedAvatar = ref(undefined)
const previewAvatar = ref(props.initialAvatar)
const imageError = ref('')
const isReading = ref(false)
const photoInput = ref(null)
let selection = 0

watch(() => props.isOpen, open => {
  selection++
  if (!open) return
  editName.value = props.initialName
  editBio.value = props.initialBio
  editRole.value = props.initialRole || 'Beginner'
  editSkills.value = props.initialSkills.join(', ')
  selectedAvatar.value = undefined
  previewAvatar.value = props.initialAvatar
  imageError.value = ''
  isReading.value = false
})

async function choosePhoto(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const version = ++selection
  selectedAvatar.value = undefined
  previewAvatar.value = props.initialAvatar
  imageError.value = ''
  isReading.value = false
  if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    imageError.value = 'Choose a JPEG, PNG, WebP or GIF image under 5 MB.'
    event.target.value = ''
    return
  }
  isReading.value = true
  try {
    const value = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => reject(new Error('Unable to read this photo. Please choose it again.'))
      reader.readAsDataURL(file)
    })
    if (version !== selection) return
    selectedAvatar.value = value
    previewAvatar.value = value
  } catch (error) {
    if (version === selection) imageError.value = error.message
  } finally {
    if (version === selection) isReading.value = false
  }
}

function handleSave() {
  if (props.isSaving || isReading.value || imageError.value) return
  emit('save', {
    name: editName.value,
    avatar: selectedAvatar.value,
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
          <label for="profile-photo">Profile Photo</label>
          <div class="photo-editor">
            <img :src="previewAvatar" alt="Profile photo preview" class="photo-preview" />
            <div>
              <input id="profile-photo" ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif"
                class="photo-input" :disabled="isSaving" @change="choosePhoto" />
              <button type="button" class="btn-cancel" :disabled="isSaving || isReading" @click="photoInput?.click()">Upload Photo</button>
              <p class="photo-help">JPEG, PNG, WebP or GIF. Maximum 5 MB.</p>
            </div>
          </div>
          <p v-if="imageError" class="photo-error" role="alert">{{ imageError }}</p>
        </div>
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
        <button class="btn-save" :disabled="isSaving || isReading || !!imageError" @click="handleSave">{{ isSaving ? 'Saving...' : 'Save Changes' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.photo-editor { display: flex; align-items: center; gap: 1rem; }
.photo-preview { width: 76px; height: 76px; border-radius: 50%; object-fit: cover; }
.photo-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.photo-help { font-size: 0.8rem; color: #64748b; margin: 0.5rem 0 0; }
.photo-error { color: #b91c1c; font-size: 0.85rem; margin: 0; }
button:disabled { opacity: 0.6; cursor: wait; }

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
  max-height: 90vh;
  overflow-y: auto;
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
