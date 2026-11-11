// Bootstrap first, so the app's own styles (colors, dark mode, layout) still win where they are set.
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './assets/main.css'
import './assets/animations.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { registerServiceWorker } from './services/push.js'
import { startReveal } from './utils/reveal.js'

const app = createApp(App)

app.use(createPinia())
app.use(router)

router.isReady().then(() => {
  app.mount('#app')
  startReveal(document.getElementById('app'))
})
registerServiceWorker()
