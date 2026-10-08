<script setup>
import { ref, onMounted } from 'vue'
import { apiAction, apiList } from '@/services/api'
const leaders = ref([])
onMounted(() => apiAction(async () => { leaders.value = await apiList('/leaderboard') }))
</script>

<template>
  <div class="leaderboard-container animate-fade-in">
    <div class="header-section text-center">
      <h1 class="page-title">Community Leaderboard</h1>
      <p class="text-muted">Top contributors who make this community great.</p>
    </div>

    <div class="podium-section">
      <!-- 2nd Place -->
      <div class="podium-spot second-place glass-panel">
        <div class="rank-badge">2</div>
        <img v-if="leaders[1]" :src="leaders[1].avatar" class="podium-avatar" />
        <h3 class="name">{{ leaders[1]?.name || 'No contributor yet' }}</h3>
        <p class="points text-muted">{{ leaders[1]?.reputation || 0 }} pts</p>
      </div>

      <!-- 1st Place -->
      <div class="podium-spot first-place glass-panel">
        <div class="crown">
          <svg viewBox="0 0 256 256" fill="#fbbf24" width="32" height="32"><path d="M232,192a8,8,0,0,1-8,8H32a8,8,0,0,1-8-8V104a8,8,0,0,1,14.61-4.52l41.6,60.52L123,45.42a8,8,0,0,1,13.9,0l42.66,114.58,41.6-60.52A8,8,0,0,1,232,104Z"></path></svg>
        </div>
        <div class="rank-badge">1</div>
        <img v-if="leaders[0]" :src="leaders[0].avatar" class="podium-avatar" />
        <h3 class="name">{{ leaders[0]?.name || 'No contributor yet' }}</h3>
        <p class="points highlight-points">{{ leaders[0]?.reputation || 0 }} pts</p>
      </div>

      <!-- 3rd Place -->
      <div class="podium-spot third-place glass-panel">
        <div class="rank-badge">3</div>
        <img v-if="leaders[2]" :src="leaders[2].avatar" class="podium-avatar" />
        <h3 class="name">{{ leaders[2]?.name || 'No contributor yet' }}</h3>
        <p class="points text-muted">{{ leaders[2]?.reputation || 0 }} pts</p>
      </div>
    </div>

    <div class="list-section glass-panel">
      <div class="list-header">
        <div class="col-rank">Rank</div>
        <div class="col-user">User</div>
        <div class="col-badges">Badges</div>
        <div class="col-points">Points</div>
      </div>
      
      <div class="list-body">
        <div v-for="leader in leaders.slice(3)" :key="leader.id" class="list-row">
          <div class="col-rank font-bold">{{ leader.rank }}</div>
          <div class="col-user">
            <img :src="leader.avatar" class="list-avatar" />
            <span class="font-medium">{{ leader.name }}</span>
          </div>
          <div class="col-badges">
            
            
            
          </div>
          <div class="col-points font-mono text-muted">{{ leader.reputation }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.leaderboard-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 2rem 3rem;
}

.header-section {
  padding: 3rem 0 4rem;
}

.text-center {
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.podium-section {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 1.5rem;
  margin-bottom: 4rem;
  height: 250px;
}

.podium-spot {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  position: relative;
  width: 180px;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: none;
}

.podium-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: white;
  border: 4px solid var(--surface-bg);
  margin-bottom: 1rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  z-index: 10;
}

.rank-badge {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: white;
  z-index: 11;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.first-place {
  height: 220px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(253, 230, 138, 0.3) 100%);
  border-color: #fde68a;
  transform: translateY(-20px);
}
.first-place .rank-badge { background: #fbbf24; }
.first-place .podium-avatar { width: 100px; height: 100px; border-color: #fbbf24; }
.first-place .name { font-size: 1.3rem; }

.second-place {
  height: 180px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(226, 232, 240, 0.4) 100%);
  border-color: #e2e8f0;
}
.second-place .rank-badge { background: #94a3b8; }
.second-place .podium-avatar { border-color: #cbd5e1; }

.third-place {
  height: 160px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(254, 215, 170, 0.3) 100%);
  border-color: #fed7aa;
}
.third-place .rank-badge { background: #d97706; }
.third-place .podium-avatar { border-color: #fbd38d; }

.crown {
  position: absolute;
  top: -55px;
  left: 50%;
  transform: translateX(-50%);
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translate(-50%, 0); }
  50% { transform: translate(-50%, -10px); }
  100% { transform: translate(-50%, 0); }
}

.name {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.points {
  font-size: 0.9rem;
}

.highlight-points {
  color: #d97706;
  font-weight: 700;
}

.list-section {
  padding: 0;
  overflow: hidden;
}

.list-header {
  display: flex;
  padding: 1rem 1.5rem;
  background: rgba(0,0,0,0.02);
  border-bottom: 1px solid rgba(0,0,0,0.05);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.85rem;
  text-transform: uppercase;
}

.list-body {
  display: flex;
  flex-direction: column;
}

.list-row {
  display: flex;
  padding: 1rem 1.5rem;
  align-items: center;
  border-bottom: 1px solid rgba(0,0,0,0.03);
  transition: background 0.2s;
}

.list-row:hover {
  background: rgba(255,255,255,0.5);
}

.list-row:last-child {
  border-bottom: none;
}

.col-rank {
  width: 60px;
  color: var(--text-secondary);
}

.col-user {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.col-badges {
  width: 150px;
  display: flex;
  gap: 0.5rem;
}

.col-points {
  width: 100px;
  text-align: right;
}

.list-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1f5f9;
}

.font-bold { font-weight: 700; }
.font-medium { font-weight: 500; }
.font-mono { font-family: monospace; font-size: 1.05rem; }

.badge {
  font-size: 1.2rem;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.1));
}

@media (max-width: 640px) {
  .podium-section {
    flex-direction: column;
    align-items: center;
    height: auto;
    gap: 3rem;
    margin-bottom: 3rem;
  }
  .first-place { transform: translateY(0); order: -1; }
  .col-badges { display: none; }
}
</style>
