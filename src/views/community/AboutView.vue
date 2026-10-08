<script setup>
</script>

<template>
  <div class="about-view animate-fade-in">
    <div class="hero-section glass-panel">
      <h1 class="hero-title">About Bcommunity</h1>
      <p class="hero-subtitle">Empowering IT professionals and developers to share knowledge, connect, and grow together.</p>
    </div>

    <div class="mission-grid">
      <div class="mission-card glass-panel">
        <div class="card-icon">🚀</div>
        <h2>Our Mission</h2>
        <p>To create a centralized hub for IT operations where teams can share technical knowledge.</p>
      </div>
      
      <div class="mission-card glass-panel">
        <div class="card-icon">🤝</div>
        <h2>Connect</h2>
        <p>Find collaborators, join tech events, and build a network that accelerates your career.</p>
      </div>

      <div class="mission-card glass-panel">
        <div class="card-icon">📚</div>
        <h2>Learn</h2>
        <p>Access shared documentation, get advice from senior engineers, and collaborate on exciting new projects.</p>
      </div>
    </div>
    
    <div class="team-section glass-panel">
      <h2>Join the Community</h2>
      <p class="text-muted" style="margin-bottom: 1.5rem;">Ready to start your journey? Jump in and introduce yourself.</p>
      <router-link to="/community" class="btn btn-primary">Go to Feed</router-link>
    </div>
  </div>
</template>

<style scoped>
.about-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.hero-section {
  padding: 4rem 2rem;
  text-align: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 1rem;
  letter-spacing: -0.03em;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

.mission-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.mission-card {
  padding: 2.5rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.mission-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent-color);
}

.card-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
}

.mission-card h2 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}

.mission-card p {
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.5;
}

.team-section {
  padding: 3rem 2rem;
  text-align: center;
  background: #ffffff;
}

.team-section h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
</style>
