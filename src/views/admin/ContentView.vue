<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useUiStore } from '@/stores/ui'
import { useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const ui = useUiStore()

// Field lists mirror backend/routes/resources.py SCHEMAS.
const KINDS = {
  articles: {
    label: 'Articles', singular: 'article',
    columns: ['title', 'readTime', 'likes'],
    fields: [
      { key: 'title', label: 'Title', required: true },
      { key: 'excerpt', label: 'Excerpt', type: 'textarea', rows: 2 },
      { key: 'content', label: 'Content', type: 'textarea', rows: 8, required: true },
      { key: 'coverImage', label: 'Cover image URL', type: 'url' },
      { key: 'readTime', label: 'Read time', placeholder: '5 min read' },
      { key: 'tags', label: 'Tags', type: 'list', placeholder: 'vue, javascript' },
    ],
  },
  jobs: {
    label: 'Jobs', singular: 'job',
    columns: ['title', 'company', 'location', 'type'],
    fields: [
      { key: 'title', label: 'Job title', required: true },
      { key: 'company', label: 'Company', required: true },
      { key: 'location', label: 'Location', required: true, half: true },
      { key: 'type', label: 'Type', required: true, half: true, placeholder: 'Full-time' },
      { key: 'salary', label: 'Salary', placeholder: '$800 – $1,200 / month' },
      { key: 'logo', label: 'Logo URL', type: 'url' },
      { key: 'description', label: 'Description', type: 'textarea', rows: 6, required: true },
      { key: 'tags', label: 'Tags', type: 'list', placeholder: 'remote, python' },
    ],
  },
  events: {
    label: 'Events', singular: 'event',
    columns: ['title', 'date', 'location', 'price'],
    fields: [
      { key: 'title', label: 'Event title', required: true },
      { key: 'date', label: 'Date', required: true, half: true, placeholder: 'Dec 20, 2026' },
      { key: 'time', label: 'Time', required: true, half: true, placeholder: '6:00 PM – 8:00 PM' },
      { key: 'location', label: 'Location', required: true, half: true },
      { key: 'type', label: 'Type', required: true, half: true, placeholder: 'Workshop' },
      { key: 'price', label: 'Price', half: true, placeholder: 'Free' },
      { key: 'attendeesCount', label: 'Attendees', type: 'number', half: true },
      { key: 'coverImage', label: 'Cover image URL', type: 'url' },
      { key: 'speakers', label: 'Speakers', type: 'list', placeholder: 'Dara, Sophea' },
      { key: 'description', label: 'Description', type: 'textarea', rows: 6, required: true },
    ],
  },
}
const LABELS = { title: 'Title', readTime: 'Read time', likes: 'Likes', company: 'Company', location: 'Location',
                 type: 'Type', date: 'Date', price: 'Price' }

const tab = ref('articles')
const kind = computed(() => KINDS[tab.value])
const loading = ref(false)
const load = async () => {
  loading.value = true
  await admin.fetchContent(tab.value)
  loading.value = false
}
onMounted(load)
watch(tab, load)

const search = ref('')
const rows = computed(() => {
  const q = search.value.trim().toLowerCase()
  return admin.content[tab.value].filter(item => !q || JSON.stringify(item).toLowerCase().includes(q))
})

// Create / edit form
const form = ref(null)
const openForm = item => {
  const values = {}
  for (const field of kind.value.fields) {
    const value = item?.[field.key]
    values[field.key] = field.type === 'list' ? (value || []).join(', ') : (value ?? (field.type === 'number' ? 0 : ''))
  }
  form.value = { id: item?.id ?? null, values }
}
const save = async () => {
  const payload = {}
  for (const field of kind.value.fields) {
    let value = form.value.values[field.key]
    if (field.type === 'list') value = String(value).split(',').map(s => s.trim()).filter(Boolean)
    else if (field.type === 'number') value = Math.max(0, Number(value) || 0)
    else if (field.type === 'url') value = value.trim() || null
    else if (!field.required && form.value.id === null && !value.trim()) continue
    payload[field.key] = value
  }
  const saved = form.value.id === null
    ? await admin.createContent(tab.value, payload)
    : await admin.updateContent(tab.value, form.value.id, payload)
  if (!saved) return
  ui.addToast(`${kind.value.singular[0].toUpperCase() + kind.value.singular.slice(1)} saved`, 'success')
  form.value = null
}
const remove = async item => {
  if (!window.confirm(`Delete “${item.title}”?`)) return
  if (await admin.deleteContent(tab.value, item.id)) ui.addToast('Deleted', 'success')
}
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Articles, Jobs &amp; Events</h1>
        <p class="text-muted">Publish and maintain the knowledge base and opportunities</p>
      </div>
      <button class="adm-btn primary" @click="openForm(null)">+ New {{ kind.singular }}</button>
    </div>

    <div class="adm-tabs" role="tablist">
      <button v-for="(info, key) in KINDS" :key="key" role="tab" :aria-selected="tab === key"
        class="adm-tab" :class="{ active: tab === key }" @click="tab = key">
        {{ info.label }}
      </button>
    </div>

    <div class="glass-panel adm-toolbar">
      <input v-model="search" type="search" class="input-field adm-search" :placeholder="`Search ${kind.label.toLowerCase()}…`" :aria-label="`Search ${kind.label}`" />
      <span class="adm-count">{{ rows.length }} {{ kind.label.toLowerCase() }}</span>
    </div>

    <div class="glass-panel adm-table-wrap">
      <table class="adm-table">
        <thead>
          <tr>
            <th v-for="column in kind.columns" :key="column" :class="{ num: column === 'likes' }">{{ LABELS[column] }}</th>
            <th class="num">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rows" :key="item.id">
            <td v-for="column in kind.columns" :key="column" :class="{ num: column === 'likes' }">
              <div :class="column === 'title' ? 'adm-clip' : 'nowrap'">
                <strong v-if="column === 'title'">{{ item.title }}</strong>
                <template v-else>{{ item[column] }}</template>
              </div>
            </td>
            <td>
              <div class="adm-cell-actions">
                <button class="adm-icon-btn" title="Edit" aria-label="Edit" @click="openForm(item)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
                </button>
                <button class="adm-icon-btn danger" title="Delete" aria-label="Delete" @click="remove(item)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="adm-empty">Loading…</div>
      <div v-else-if="!rows.length" class="adm-empty">Nothing here yet. Use “New {{ kind.singular }}” to add one.</div>
    </div>

    <div v-if="form" class="adm-overlay" @click.self="form = null">
      <div class="adm-modal wide" role="dialog" aria-modal="true" aria-labelledby="content-title">
        <div class="adm-modal-head">
          <h2 id="content-title">{{ form.id === null ? 'New' : 'Edit' }} {{ kind.singular }}</h2>
          <button class="adm-icon-btn" aria-label="Close" @click="form = null">✕</button>
        </div>
        <form class="adm-form field-grid" @submit.prevent="save">
          <label v-for="field in kind.fields" :key="field.key" :class="{ half: field.half }">
            {{ field.label }}<span v-if="field.required" aria-hidden="true"> *</span>
            <textarea v-if="field.type === 'textarea'" v-model="form.values[field.key]" class="input-field"
              :rows="field.rows" :required="field.required"></textarea>
            <input v-else v-model="form.values[field.key]" class="input-field"
              :type="field.type === 'number' ? 'number' : field.type === 'url' ? 'url' : 'text'"
              :min="field.type === 'number' ? 0 : undefined" :placeholder="field.placeholder" :required="field.required" />
            <span v-if="field.type === 'list'" class="hint">Separate with commas</span>
          </label>
          <div class="adm-form-foot full">
            <button type="button" class="adm-btn" @click="form = null">Cancel</button>
            <button type="submit" class="adm-btn primary">Save</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wide { max-width: 720px; }
.field-grid { display: grid; grid-template-columns: 1fr 1fr; }
.field-grid > label { grid-column: 1 / -1; }
.field-grid > label.half { grid-column: auto; }
.field-grid > .full { grid-column: 1 / -1; }
@media (max-width: 640px) {
  .field-grid > label.half { grid-column: 1 / -1; }
}
</style>
