<script setup>
import { ref, computed, nextTick } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useUiStore } from '@/stores/ui'
import { useSettingsStore } from '@/stores/settings'

const store = usePostsStore()
const uiStore = useUiStore()
const t = useSettingsStore().t
const content = ref('')
const selectedTag = ref('#General')
const availableTags = ['#General', '#Bug', '#Review', '#Hardware', '#Software']
const showCodeInput = ref(false)
const codeSnippet = ref('')
const codeLanguage = ref('javascript')
const imageUrl = ref('')
const fileInput = ref(null)
const textarea = ref(null)
const posting = ref(false)
const canPost = computed(() => !posting.value && Boolean(content.value.trim() || codeSnippet.value.trim() || imageUrl.value))

// The textarea grows with the text, up to a limit, then scrolls.
function autoGrow() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 320) + 'px'
}

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
  if (!canPost.value) return
  posting.value = true
  try {
    const created = await store.addPost(content.value, selectedTag.value, codeSnippet.value, codeLanguage.value, false, imageUrl.value, '')
    if (!created) return
    content.value = ''
    codeSnippet.value = ''
    imageUrl.value = ''
    showCodeInput.value = false
    selectedTag.value = '#General'
    nextTick(autoGrow)
    uiStore.addToast(t('create.published'), 'success')
  } finally {
    posting.value = false
  }
}
</script>

<template>
  <section class="create-post glass-panel" :aria-label="t('create.label')">
    <div class="input-row">
      <img :src="store.currentUser.avatar" :alt="store.currentUser.name" class="avatar" />
      <textarea
        ref="textarea"
        v-model="content"
        class="post-input"
        :placeholder="t('create.placeholder')"
        :aria-label="t('create.text')"
        rows="2"
        @input="autoGrow"
      ></textarea>
    </div>

    <div v-if="showCodeInput" class="code-input-section">
      <div class="code-header">
        <span class="code-header-title">{{ t('create.codeTitle') }}</span>
        <button class="icon-btn" @click="showCodeInput = false" :title="t('create.removeCode')" :aria-label="t('create.removeCode')">✕</button>
      </div>
      <textarea
        v-model="codeSnippet"
        class="code-textarea"
        :placeholder="t('create.codePlaceholder')"
        aria-label="Code snippet"
        rows="5"
      ></textarea>
    </div>

    <div v-if="imageUrl" class="image-preview-section">
      <img :src="imageUrl" alt="Selected image preview" class="image-preview" />
      <button class="remove-image-btn" @click="imageUrl = ''" :title="t('create.removeImage')" :aria-label="t('create.removeImage')">✕</button>
    </div>

    <div class="action-row">
      <select v-model="selectedTag" class="tag-selector" :aria-label="t('create.topic')" :title="t('create.topic')">
        <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
      </select>
      <button class="tool-btn" :class="{ active: showCodeInput }" :aria-pressed="showCodeInput" :title="t('create.addCode')"
        @click="showCodeInput = !showCodeInput">
        <svg class="tool-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <polyline points="16 18 22 12 16 6"></polyline>
          <polyline points="8 6 2 12 8 18"></polyline>
        </svg>
        <span>{{ t('create.code') }}</span>
      </button>
      <button class="tool-btn" :title="t('create.addImage')" @click="fileInput.click()">
        <svg class="tool-icon image-icon" viewBox="0 0 256 256" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M216,40H40A16,16,0,0,0,24,56V200a16,16,0,0,0,16,16H216a16,16,0,0,0,16-16V56A16,16,0,0,0,216,40ZM216,56V158.33l-46.63-46.62a16,16,0,0,0-22.62,0L96,162.34,59.31,125.66a16,16,0,0,0-22.62,0L40,129V56ZM40,151.66l27.31-27.32L118,175.05,82.63,200H40ZM216,200H102.26l44.43-31.11,69.31-69.31L216,101.66V200ZM104,96A12,12,0,1,1,92,84,12,12,0,0,1,104,96Z"/></svg>
        <span>{{ t('create.image') }}</span>
      </button>
      <input type="file" ref="fileInput" accept="image/*" hidden @change="handleImageUpload" />
      <span class="spacer"></span>
      <button class="post-submit-btn" :disabled="!canPost" @click="submitPost">
        {{ posting ? t('create.posting') : t('create.post') }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.create-post {
  padding: 16px 18px 12px;
  margin-bottom: 16px;
  overflow: visible;
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background: var(--tint, #ede9fe);
}

.post-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  padding: 9px 0 6px;
  font-size: 15.5px;
  line-height: 1.6;
  color: var(--ink-strong, #0f172a);
  resize: none;
  overflow-y: auto;
  min-height: 52px;
  outline: none;
}

.post-input::placeholder { color: var(--ink-400, #94a3b8); }

.action-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--surface-3, #f1f2f6);
}

.spacer { flex: 1; }

.tag-selector {
  height: 32px;
  background: var(--brand-soft);
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--brand-ink, #6d28d9);
  cursor: pointer;
  transition: all 0.15s ease;
}

.tag-selector:hover { border-color: var(--tint-strong, #ddd6fe); }

.tool-btn {
  height: 32px;
  background: none;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-600, #475569);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0 10px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.tool-btn:hover { background: var(--tint, #f5f3ff); color: var(--brand); }
.tool-btn.active { background: var(--brand-soft); color: var(--brand); }

.tool-icon { width: 17px; height: 17px; color: var(--brand); }
.image-icon { color: #3b82f6; }

.post-submit-btn {
  height: 36px;
  padding: 0 20px;
  background: var(--brand);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.post-submit-btn:hover:not(:disabled) { background: var(--brand-hover); }
.post-submit-btn:active:not(:disabled) { transform: scale(0.98); }

.post-submit-btn:disabled {
  background: var(--tint-strong, #ddd6fe);
  cursor: not-allowed;
}

/* Code snippet */
.code-input-section {
  margin: 10px 0 0 52px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--surface-2, #f8fafc);
  border: 1px solid var(--line, #e2e8f0);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px 4px 12px;
  background: var(--surface-3, #f1f5f9);
  border-bottom: 1px solid var(--line, #e2e8f0);
}

.code-header-title { font-size: 12.5px; font-weight: 600; color: var(--ink-500, #64748b); }

.code-header .icon-btn {
  color: var(--ink-500, #64748b);
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: 6px;
  cursor: pointer;
}

.code-header .icon-btn:hover { color: #ef4444; background: var(--tint-red, #fee2e2); }

.code-textarea {
  width: 100%;
  display: block;
  background: transparent;
  border: none;
  padding: 12px;
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 13.5px;
  color: var(--ink-strong, #1e293b);
  resize: vertical;
  min-height: 110px;
  outline: none;
}

/* Image preview */
.image-preview-section {
  position: relative;
  margin: 10px 0 0 52px;
  border-radius: 12px;
  overflow: hidden;
  display: inline-block;
  max-width: calc(100% - 52px);
}

.image-preview {
  display: block;
  max-width: 100%;
  max-height: 280px;
  object-fit: contain;
  border-radius: 12px;
}

.remove-image-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(15, 23, 42, 0.65);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.8rem;
}

.remove-image-btn:hover { background: #ef4444; }

@media (max-width: 767px) {
  .create-post {
    padding: 12px 12px 10px;
    margin-bottom: 12px;
  }

  .avatar { width: 36px; height: 36px; }
  .post-input { padding-top: 7px; }
  .code-input-section,
  .image-preview-section { margin-left: 0; max-width: 100%; }
}

@media (max-width: 380px) {
  .tool-btn span { display: none; }
}
</style>
