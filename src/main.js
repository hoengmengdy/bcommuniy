import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { registerServiceWorker } from './services/push.js'

const app = createApp(App)

app.use(createPinia())
app.use(router)

router.isReady().then(() => app.mount('#app'))
registerServiceWorker()
