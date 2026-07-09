<template>
  <div class="app">

    <!-- 桌面端：顶部导航 -->
    <header v-if="showNav" class="top-nav">
      <div class="nav-inner">
        <div class="nav-brand" @click="$router.push('/')">
          <img src="/logo.png" alt="logo" class="nav-logo" />
          <span class="nav-title">AI竞界</span>
        </div>
        <nav class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: $route.name === 'Recommendations' }">今日赛事</router-link>
          <router-link to="/history" class="nav-link" :class="{ active: $route.name === 'History' }">历史战绩</router-link>
          <router-link to="/profile" class="nav-link" :class="{ active: $route.name === 'Profile' }">个人中心</router-link>
        </nav>
        <div class="nav-user" v-if="auth.user">
          <span class="user-name">{{ auth.user.nickname || auth.user.phone }}</span>
          <button class="logout-btn" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>

    <!-- 页面内容 -->
    <main :class="mainClass">
      <router-view />
    </main>

    <!-- 移动端：底部标签栏 -->
    <nav v-if="showNav" class="bottom-tab">
      <router-link to="/" class="tab-item" :class="{ active: $route.name === 'Recommendations' }">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 16 14"/>
        </svg>
        <span class="tab-label">赛事</span>
      </router-link>
      <router-link to="/history" class="tab-item" :class="{ active: $route.name === 'History' }">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M3 3v18h18"/><polyline points="7 16 11 10 15 14 21 6"/>
        </svg>
        <span class="tab-label">战绩</span>
      </router-link>
      <router-link to="/profile" class="tab-item" :class="{ active: $route.name === 'Profile' }">
        <svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 12 0v1"/>
        </svg>
        <span class="tab-label">我的</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const showNav = computed(() => {
  if (route.name === 'Login') return false
  if (route.path.startsWith('/admin')) return false
  return true
})

const mainClass = computed(() => ({
  'has-top-nav': showNav.value,
  'has-bottom-tab': showNav.value,
  'no-nav': !showNav.value,
}))

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--bg);
}

/* ==============================
   桌面端：顶部导航 (≥768px)
   ============================== */
.top-nav {
  display: none;
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
}

.nav-inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
}

.nav-brand { display: flex; align-items: center; gap: 8px; cursor: pointer; margin-right: 40px; }
.nav-logo { width: 32px; height: 32px; border-radius: 50%; }
.nav-title { font-size: 16px; font-weight: 700; color: var(--text); }

.nav-links { display: flex; gap: 4px; flex: 1; }

.nav-link {
  padding: 8px 16px; border-radius: 8px;
  font-size: 14px; font-weight: 500;
  color: var(--muted); text-decoration: none;
  transition: all 0.15s;
}
.nav-link:hover { color: var(--primary); background: var(--primary-light); }
.nav-link.active { color: var(--primary); background: var(--primary-light); font-weight: 600; }

.nav-user { display: flex; align-items: center; gap: 12px; }
.user-name { font-size: 14px; color: var(--text-secondary); }
.logout-btn {
  padding: 6px 14px; background: var(--border-light); color: var(--muted);
  border-radius: 6px; font-size: 13px;
}
.logout-btn:hover { background: #FEF2F2; color: var(--error); }

main.has-top-nav { padding-top: 0; }
main.no-nav { /* 登录/admin 全屏 */ }

/* ==============================
   移动端：底部标签栏 (<768px)
   ============================== */
.bottom-tab {
  display: flex;
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 56px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom, 0);
  box-shadow: 0 -2px 12px rgba(0,0,0,0.04);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-decoration: none;
  color: var(--muted);
  padding: 6px 20px;
  min-width: 60px;
  min-height: 44px;
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.tab-item.active { color: var(--primary); }

.tab-icon { width: 24px; height: 24px; }
.tab-label { font-size: 11px; font-weight: 500; letter-spacing: 0.03em; }

main.has-bottom-tab {
  padding-bottom: calc(56px + env(safe-area-inset-bottom, 0px));
}

/* ==============================
   响应式切换
   ============================== */
@media (min-width: 768px) {
  .top-nav { display: block; }
  .bottom-tab { display: none; }
  main.has-bottom-tab { padding-bottom: 0; }
  main.has-top-nav { /* 桌面无需额外 padding */ }
}

@media (max-width: 767px) {
  .top-nav { display: none; }
  .bottom-tab { display: flex; }
}
</style>
