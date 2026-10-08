<script setup>
import { computed } from 'vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css' // Import a nice dark theme

const props = defineProps({
  code: {
    type: String,
    required: true
  },
  language: {
    type: String,
    default: 'javascript'
  }
})

const highlightedCode = computed(() => {
  try {
    if (props.language && hljs.getLanguage(props.language)) {
      return hljs.highlight(props.code, { language: props.language }).value
    }
    return hljs.highlightAuto(props.code).value
  } catch (e) {
    return props.code.replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[char]))
  }
})

function copyToClipboard() {
  navigator.clipboard.writeText(props.code)
  // Optional: Add a toast notification here if desired
}
</script>

<template>
  <div class="code-block-container">
    <div class="code-header">
      <span class="language-badge">{{ language }}</span>
      <button class="copy-btn" @click="copyToClipboard" title="Copy code">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        Copy
      </button>
    </div>
    <pre><code class="hljs" :class="language" v-html="highlightedCode"></code></pre>
  </div>
</template>

<style scoped>
.code-block-container {
  background: #282c34;
  border-radius: 8px;
  overflow: hidden;
  margin: 1rem 0;
  box-shadow: none;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #1c1e22;
  border-bottom: 1px solid #3e4451;
}

.language-badge {
  font-family: monospace;
  font-size: 0.75rem;
  color: #abb2bf;
  text-transform: uppercase;
  font-weight: bold;
}

.copy-btn {
  background: transparent;
  border: none;
  color: #abb2bf;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

pre {
  margin: 0;
  padding: 1rem;
  overflow-x: auto;
}

code {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
}
</style>
