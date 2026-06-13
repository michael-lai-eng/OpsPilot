import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as Icons from '@element-plus/icons-vue'
import 'nprogress/nprogress.css'
import App from './App.vue'
import router from './router'
import '@/styles/main.scss'

const app = createApp(App)

// Register all Element Plus icons globally
Object.entries(Icons).forEach(([name, comp]) => app.component(name, comp))

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
