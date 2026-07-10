import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    name: 'Recommendations',
    component: () => import('../views/Recommendations.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue')
  },
  {
    path: '/admin/recommendations',
    name: 'ManageRecommendations',
    component: () => import('../views/admin/ManageRecommendations.vue'),
    meta: { admin: true }
  },
  {
    path: '/admin/recommendations/create',
    name: 'CreateRecommendation',
    component: () => import('../views/admin/CreateRecommendation.vue'),
    meta: { admin: true }
  },
  {
    path: '/admin/recommendations/:id/edit',
    name: 'EditRecommendation',
    component: () => import('../views/admin/CreateRecommendation.vue'),
    meta: { admin: true }
  },
  {
    path: '/admin/recommendations/:id/result',
    name: 'MarkResult',
    component: () => import('../views/admin/MarkResult.vue'),
    meta: { admin: true }
  },
  {
    path: '/admin/membership',
    name: 'ManageMembership',
    component: () => import('../views/admin/ManageMembership.vue'),
    meta: { admin: true }
  },
  {
    path: '/admin/achievements/edit/:id?',
    name: 'EditAchievement',
    component: () => import('../views/admin/EditAchievement.vue'),
    meta: { admin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // 尝试恢复登录态
  if (!auth.token) {
    auth.restore()
  }

  // 已登录用户访问登录页，跳首页
  if (auth.token && to.name === 'Login') {
    next({ name: 'Recommendations' })
    return
  }

  // 管理后台需要管理员权限（未登录跳登录页）
  if (to.meta.admin) {
    if (!auth.token) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    if (auth.user?.role !== 'admin') {
      next({ name: 'Recommendations' })
      return
    }
  }

  next()
})

export default router
