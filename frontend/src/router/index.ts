import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import SettingPage from '../views/SettingPage.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'Chat',
        component: ChatView,
        meta: { title: '对话' }
      },
      {
        path: '/settings',
        name: 'Settings',
        component: SettingPage,
        meta: { title: '设置' }
      }
    ]
  },
  // 添加404路由重定向
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫，可以用于修改页面标题等
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - AI助手` : 'AI助手'
  next()
})

export default router 