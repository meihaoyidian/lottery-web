<template>
  <div class="page">
    <router-view />
    <nav v-if="showTabBar" class="tab-bar">
      <router-link to="/" class="tab-item" :class="{ active: $route.name === 'Recommendations' }">
        <span class="tab-icon">📋</span>
        <span class="tab-label">今日赛事</span>
      </router-link>
      <router-link to="/history" class="tab-item" :class="{ active: $route.name === 'History' }">
        <span class="tab-icon">📊</span>
        <span class="tab-label">历史战绩</span>
      </router-link>
      <router-link to="/profile" class="tab-item" :class="{ active: $route.name === 'Profile' }">
        <span class="tab-icon">👤</span>
        <span class="tab-label">个人中心</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const showTabBar = computed(() => {
  const name = route.name
  const path = route.path
  if (name === 'Login') return false
  if (path.startsWith('/admin')) return false
  return true
})
</script>

<style scoped>
.page { padding-bottom: 70px; }
.tab-bar {
  position: fixed; bottom: 0; left: 0; right: 0; height: 56px;
  background: #fff; border-top: 1px solid #e8ecf2;
  display: flex; align-items: center; justify-content: space-around;
  z-index: 100; padding-bottom: env(safe-area-inset-bottom);
  box-shadow: 0 -2px 12px rgba(0,0,0,0.04);
}
.tab-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  text-decoration: none; color: #94a3b8; font-size: 11px;
  padding: 4px 16px; transition: color 0.2s;
}
.tab-item.active { color: #2563eb; }
.tab-icon { font-size: 20px; }
.tab-label { font-weight: 500; }
</style>
