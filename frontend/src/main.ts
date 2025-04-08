import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import './style.css'
import App from './App.vue'
import elementIcons from './plugins/element-icons'
import router from './router'
import { createPinia } from 'pinia' 

// Create Vue app
const app = createApp(App)
const pinia = createPinia()

// Use Element Plus
app.use(ElementPlus)

// Use Element Plus Icons
app.use(elementIcons)

// 使用路由
app.use(router)

// 使用 Pinia
app.use(pinia)

// Provide axios globally
app.config.globalProperties.$axios = axios

// Mount the app
app.mount('#app') 