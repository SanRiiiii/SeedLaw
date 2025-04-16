import { createApp } from 'vue'
import axios from 'axios'
import './style.css'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia' 
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

// Create Vue app
const app = createApp(App)
const pinia = createPinia()

app.use(Antd)

// 使用路由
app.use(router)

// 使用 Pinia
app.use(pinia)

// Provide axios globally
app.config.globalProperties.$axios = axios

// Mount the app
app.mount('#app') 