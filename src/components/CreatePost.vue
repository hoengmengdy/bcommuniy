<script setup>
import { ref } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'

const store = usePostsStore()
const uiStore = useUiStore()
const content = ref('')
const selectedTag = ref('#General')
const availableTags = ['#General', '#Bug', '#Review', '#Hardware', '#Software']
const showCodeInput = ref(false)
const codeSnippet = ref('')
const codeLanguage = ref('javascript')
const imageUrl = ref('')
const fileInput = ref(null)

function handleImageUpload(event) {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      imageUrl.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

async function submitPost() {
  if (content.value.trim() || codeSnippet.value.trim() || imageUrl.value) {
    const created = await store.addPost(content.value, selectedTag.value, codeSnippet.value, codeLanguage.value, false, imageUrl.value, '')
    if (!created) return
    content.value = ''
    codeSnippet.value = ''
    imageUrl.value = ''
    showCodeInput.value = false
    selectedTag.value = '#General'
    uiStore.addToast('Post published successfully!', 'success')
  }
}
</script>

<template>
  <div class="create-post glass-panel">
    <div class="input-row">
      <img :src="store.currentUser.avatar" alt="Avatar" class="avatar" />
      <div class="input-wrapper">
        <textarea 
          v-model="content" 
          class="post-input" 
          placeholder="Share something with the community..."
          rows="3"
        ></textarea>
      </div>
    </div>
    
    <div v-if="showCodeInput" class="code-input-section animate-fade-in">
      <div class="code-header">
        <span class="code-header-title" style="font-size: 0.85rem; font-weight: 600; color: #64748b;">Code Snippet</span>
        <button class="icon-btn" @click="showCodeInput = false" title="Remove Code">✕</button>
      </div>
      <textarea 
        v-model="codeSnippet" 
        class="code-textarea" 
        placeholder="Paste your code here..."
        rows="5"
      ></textarea>
    </div>

    <div v-if="imageUrl" class="image-preview-section animate-fade-in">
      <img :src="imageUrl" alt="Preview" class="image-preview" />
      <button class="remove-image-btn" @click="imageUrl = ''" title="Remove Image">✕</button>
    </div>
    
    <div class="action-row">
      <div class="left-actions">
        <select v-model="selectedTag" class="tag-selector">
          <option v-for="tag in availableTags" :key="tag" :value="tag">
            {{ tag }}
          </option>
        </select>
        <button class="action-btn" @click="showCodeInput = !showCodeInput" :class="{ active: showCodeInput }">
          <svg class="action-icon" style="color: #8b5cf6;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 18 22 12 16 6"></polyline>
            <polyline points="8 6 2 12 8 18"></polyline>
          </svg>
          Code
        </button>
        <button class="action-btn" @click="fileInput.click()">
          <svg class="action-icon" style="color: #3b82f6;" viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM216,56V158.33l-46.63-46.62a16,16,0,0,0-22.62,0L96,162.34,59.31,125.66a16,16,0,0,0-22.62,0L40,129V56ZM40,151.66l27.31-27.32L118,175.05,82.63,200H40ZM216,200H102.26l44.43-31.11,69.31-69.31L216,101.66V200ZM104,96A12,12,0,1,1,92,84,12,12,0,0,1,104,96Z"/></svg>
          Image
        </button>
        <input type="file" ref="fileInput" accept="image/*" style="display: none" @change="handleImageUpload" />
      </div>
      
      <div class="right-actions">
        <button class="post-submit-btn" @click="submitPost" :disabled="!content.trim() && !codeSnippet.trim() && !imageUrl">
          Post
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.create-post {
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  margin-top: 0.2rem;
}

.input-wrapper {
  position: relative;
  flex: 1;
}

.post-input {
  width: 100%;
  background: transparent;
  border: none;
  padding: 0.5rem 0;
  font-family: inherit;
  font-size: 1.05rem;
  line-height: 1.5;
  color: #1a1a1a;
  transition: all var(--transition-fast);
  resize: vertical;
  min-height: 80px;
  box-shadow: none;
  outline: none;
}

.post-input::placeholder {
  color: #9ca3af;
}

.action-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.left-actions {
  display: flex;
  gap: 0.8rem;
  align-items: center;
  flex-wrap: wrap;
}

.action-btn {
  background: none;
  border: none;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #4b5563;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  border-radius: 8px;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: rgba(255,255,255,0.8);
  color: var(--accent-color);
  transform: translateY(-2px);
  box-shadow: none;
}

.action-icon {
  width: 18px;
  height: 18px;
}

.tag-selector {
  background: rgba(255,255,255,0.5);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255,255,255,0.8);
  border-radius: 8px;
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  outline: none;
  transition: all var(--transition-fast);
}
.tag-selector:hover {
  background: white;
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.post-submit-btn {
  background: var(--accent-gradient);
  color: #ffffff;
  border: 1px solid rgba(255,255,255,0.1);
  padding: 0.5rem 1.25rem;
  border-radius: 100px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: none;
}

.post-submit-btn:hover:not(:disabled) {
  box-shadow: none;
  transform: translateY(-2px);
  filter: brightness(1.1);
}

.post-submit-btn:disabled {
  background: #c4b5fd;
  cursor: not-allowed;
}

/* Code Section styling for soft theme */
.code-input-section {
  margin: 1rem 0 1.5rem 0;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(248, 250, 252, 0.7);
  backdrop-filter: blur(8px);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(203, 213, 225, 0.8);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: rgba(226, 232, 240, 0.6);
  border-bottom: 1px solid rgba(203, 213, 225, 0.6);
}

.code-header .tag-selector {
  background: rgba(255, 255, 255, 0.8);
  color: #334155;
  border: 1px solid rgba(203, 213, 225, 0.8);
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.code-header .tag-selector:hover {
  background: #ffffff;
}

.code-header .icon-btn {
  color: #64748b;
  width: 28px;
  height: 28px;
}

.code-header .icon-btn:hover {
  color: #ef4444;
  background: rgba(254, 226, 226, 0.8);
  border-color: rgba(252, 165, 165, 0.5);
}

.code-textarea {
  width: 100%;
  background: transparent;
  border: none;
  padding: 1rem;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.9rem;
  color: #1e293b;
  resize: vertical;
  min-height: 120px;
}

.code-textarea:focus {
  outline: none;
}

/* Image Preview Section */
.image-preview-section {
  position: relative;
  margin: 1rem 0;
  border-radius: 12px;
  overflow: hidden;
  display: inline-block;
  max-width: 100%;
}

.image-preview {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.4);
}

.remove-image-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.8rem;
}

.remove-image-btn:hover {
  background: #ef4444;
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .create-post {
    padding: 1rem;
    margin-bottom: 1.5rem;
  }
  
  .avatar {
    width: 36px;
    height: 36px;
  }
  
  .post-input {
    font-size: 1rem;
  }
}

/* Extra Input Sections (Image & Link) */
.extra-input-section {
  margin: 1rem 0 1.5rem 0;
  padding: 0.8rem 1rem;
  display: flex;
  gap: 0.8rem;
  align-items: center;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  transition: all var(--transition-normal);
}

.extra-input-section:focus-within {
  background: #ffffff;
  border-color: var(--accent-color);
  box-shadow: 0 4px 16px rgba(124, 58, 237, 0.1);
}

.extra-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 0.95rem;
  color: #1a1a1a;
}

.extra-input::placeholder {
  color: #9ca3af;
}

.close-btn {
  width: 28px;
  height: 28px;
  background: rgba(0,0,0,0.05);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: #6b7280;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #fee2e2;
  color: #ef4444;
  border-color: #fca5a5;
  transform: none;
}
</style>
