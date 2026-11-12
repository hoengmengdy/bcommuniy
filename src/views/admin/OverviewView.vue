<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const days = ref(14)
const loading = ref(false)
const hover = ref(null)

const load = async () => {
  loading.value = true
  await admin.fetchStats(days.value)
  loading.value = false
}
onMounted(load)

const t = computed(() => admin.stats?.totals ?? {})
const tiles = computed(() => [
  { label: 'Users', value: t.value.users, sub: `${t.value.activeUsers ?? 0} active · ${t.value.inactiveUsers ?? 0} inactive`, to: '/admin/users' },
  { label: 'Admins', value: t.value.admins, sub: `${t.value.sessions ?? 0} open sessions`, to: '/admin/users' },
  { label: 'Posts', value: t.value.posts, sub: `${t.value.likes ?? 0} likes`, to: '/admin/posts' },
  { label: 'Questions', value: t.value.questions, sub: `${t.value.solved ?? 0} solved`, to: '/admin/posts' },
  { label: 'Comments', value: t.value.comments, to: '/admin/comments' },
  { label: 'Messages', value: t.value.messages, sub: `${t.value.conversations ?? 0} chats · ${t.value.calls ?? 0} calls` },
  { label: 'Articles', value: t.value.articles, to: '/admin/content' },
  { label: 'Jobs · Events', value: `${t.value.jobs ?? 0} · ${t.value.events ?? 0}`, to: '/admin/content' },
])

const charts = computed(() => {
  const activity = admin.stats?.activity ?? {}
  return [
    { key: 'signups', title: 'New users' },
    { key: 'posts', title: 'New posts' },
    { key: 'comments', title: 'New comments' },
    { key: 'messages', title: 'Messages sent' },
  ].map(chart => {
    const series = activity[chart.key] ?? []
    const max = Math.max(1, ...series.map(point => point.count))
    return { ...chart, series, max, total: series.reduce((sum, point) => sum + point.count, 0) }
  })
})

const tagMax = computed(() => Math.max(1, ...(admin.stats?.topTags ?? []).map(tag => tag.count)))
const shortDate = iso => new Date(iso + 'T00:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
const formatDate = iso => (iso ? new Date(iso).toLocaleDateString() : '')
</script>

<template>
  <div class="adm-page">
    <div class="adm-header">
      <div>
        <h1>Dashboard</h1>
        <p class="text-muted">Live summary of the whole community</p>
      </div>
      <div class="adm-actions">
        <select v-model.number="days" class="input-field range-select" aria-label="Time range" @change="load">
          <option :value="7">Last 7 days</option>
          <option :value="14">Last 14 days</option>
          <option :value="30">Last 30 days</option>
          <option :value="90">Last 90 days</option>
        </select>
        <button class="adm-btn" :disabled="loading" @click="load">{{ loading ? 'Loading…' : 'Refresh' }}</button>
      </div>
    </div>

    <div class="tiles">
      <component :is="tile.to ? RouterLink : 'div'" v-for="tile in tiles" :key="tile.label" :to="tile.to"
        class="tile glass-panel">
        <span class="tile-label">{{ tile.label }}</span>
        <span class="tile-value">{{ tile.value ?? '–' }}</span>
        <span v-if="tile.sub" class="tile-sub">{{ tile.sub }}</span>
      </component>
    </div>

    <div class="charts">
      <section v-for="chart in charts" :key="chart.key" class="chart glass-panel">
        <header>
          <h2>{{ chart.title }}</h2>
          <span class="chart-total">{{ chart.total }}</span>
        </header>
        <div class="bars" role="img" :aria-label="`${chart.title}: ${chart.total} in the last ${days} days`">
          <div v-for="point in chart.series" :key="point.date" class="bar-slot"
            @mouseenter="hover = { chart: chart.key, ...point }" @mouseleave="hover = null">
            <div class="bar" :style="{ height: (point.count / chart.max) * 100 + '%' }"
              :class="{ zero: !point.count }"></div>
            <div v-if="hover?.chart === chart.key && hover.date === point.date" class="tip">
              <strong>{{ point.count }}</strong> · {{ shortDate(point.date) }}
            </div>
          </div>
        </div>
        <div v-if="chart.series.length" class="axis">
          <span>{{ shortDate(chart.series[0].date) }}</span>
          <span>{{ shortDate(chart.series.at(-1).date) }}</span>
        </div>
      </section>
    </div>

    <div class="lists">
      <section class="glass-panel list-card">
        <h2>Top tags</h2>
        <div v-if="!admin.stats?.topTags?.length" class="adm-empty">No posts yet.</div>
        <div v-for="tag in admin.stats?.topTags" :key="tag.tag" class="hbar-row">
          <span class="hbar-label">{{ tag.tag }}</span>
          <div class="hbar-track"><div class="hbar" :style="{ width: (tag.count / tagMax) * 100 + '%' }"></div></div>
          <span class="hbar-value">{{ tag.count }}</span>
        </div>
      </section>

      <section class="glass-panel list-card">
        <h2>Top contributors</h2>
        <div v-if="!admin.stats?.topContributors?.length" class="adm-empty">No posts yet.</div>
        <RouterLink v-for="user in admin.stats?.topContributors" :key="user.id" :to="`/profile/${user.id}`"
          class="person-row">
          <div class="adm-user">
            <img :src="user.avatar" alt="" />
            <div><strong>{{ user.name }}</strong><small>{{ user.reputation }} reputation</small></div>
          </div>
          <span class="adm-badge indigo">{{ user.posts }} posts</span>
        </RouterLink>
      </section>

      <section class="glass-panel list-card">
        <h2>Newest members</h2>
        <RouterLink v-for="user in admin.stats?.recentUsers" :key="user.id" :to="`/profile/${user.id}`"
          class="person-row">
          <div class="adm-user">
            <img :src="user.avatar" alt="" />
            <div><strong>{{ user.name }}</strong><small>{{ user.email }}</small></div>
          </div>
          <span class="text-muted small-date">{{ formatDate(user.joinDate) }}</span>
        </RouterLink>
      </section>
    </div>
  </div>
</template>

<style scoped>
.range-select { width: auto; padding: 0.45rem 0.8rem; }

.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 1rem; }
.tile {
  display: flex; flex-direction: column; gap: 0.2rem; padding: 1.1rem 1.2rem;
  text-decoration: none; color: inherit;
}
a.tile:hover { border-color: var(--accent-color); }
.tile-label { font-size: 0.8rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }
.tile-value { font-size: 1.9rem; font-weight: 800; line-height: 1.15; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.tile-sub { font-size: 0.8rem; color: var(--text-secondary); }

.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.chart { padding: 1.1rem 1.2rem; }
.chart header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.8rem; }
.chart h2 { font-size: 0.95rem; margin: 0; color: var(--text-secondary); font-weight: 600; }
.chart-total { font-size: 1.3rem; font-weight: 800; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.bars {
  display: flex; align-items: flex-end; gap: 2px; height: 110px;
  border-bottom: 1px solid var(--card-border);
}
.bar-slot { flex: 1; height: 100%; display: flex; align-items: flex-end; position: relative; cursor: default; }
.bar { width: 100%; background: var(--accent-color); border-radius: 4px 4px 0 0; min-height: 2px; transition: opacity var(--transition-fast); }
.bar.zero { background: var(--card-border); }
.bars:hover .bar { opacity: 0.55; }
.bar-slot:hover .bar { opacity: 1; }
.tip {
  position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%); z-index: 2;
  background: var(--text-primary); color: var(--card-bg); padding: 0.25rem 0.55rem; border-radius: 6px;
  font-size: 0.75rem; white-space: nowrap; pointer-events: none;
}
.axis { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-secondary); margin-top: 0.35rem; }

.lists { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.list-card { padding: 1.1rem 1.2rem; display: flex; flex-direction: column; gap: 0.6rem; }
.list-card h2 { font-size: 1rem; margin: 0 0 0.3rem; }
.hbar-row { display: grid; grid-template-columns: minmax(70px, 110px) 1fr auto; gap: 0.6rem; align-items: center; font-size: 0.85rem; }
.hbar-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary); }
.hbar-track { height: 10px; }
.hbar { height: 100%; background: var(--accent-color); border-radius: 0 4px 4px 0; min-width: 2px; }
.hbar-value { font-weight: 700; font-variant-numeric: tabular-nums; }
.person-row {
  display: flex; justify-content: space-between; align-items: center; gap: 0.6rem;
  padding: 0.4rem; border-radius: var(--radius-sm); text-decoration: none; color: inherit;
}
.person-row:hover { background: var(--accent-glow); }
.person-row .adm-user { min-width: 0; }
.person-row small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.small-date { font-size: 0.8rem; white-space: nowrap; }

@media (max-width: 480px) {
  .tiles { grid-template-columns: 1fr 1fr; }
  .tile-value { font-size: 1.5rem; }
}
</style>
