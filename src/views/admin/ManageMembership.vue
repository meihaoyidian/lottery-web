<template>
  <div class="page">
    <div class="container">
      <div class="admin-header">
        <h2>用户管理</h2>
        <button class="btn btn-ghost" @click="$router.push('/admin/recommendations')">← 推荐管理</button>
      </div>

      <Loading v-if="loading" />

      <div v-else class="user-list">
        <div v-for="u in users" :key="u.id" class="user-item">
          <div class="user-info">
            <span class="user-name">{{ u.nickname || u.phone }}</span>
            <span class="user-phone">{{ u.phone }}</span>
            <span class="user-role">{{ u.role === 'admin' ? '管理员' : u.is_paid ? '付费' : u.is_trial_user ? '体验' : '免费' }}</span>
          </div>
          <div class="user-actions">
            <select v-model="u._tier" class="tier-select">
              <option value="">--</option>
              <option value="15">15天</option>
              <option value="30">30天</option>
              <option value="90">90天</option>
              <option value="365">365天</option>
            </select>
            <button class="btn-sm btn-primary" @click="setMembership(u)">设置</button>
          </div>
        </div>
        <div v-if="users.length === 0" class="empty">暂无用户数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const loading = ref(true)
const users = ref([])

async function load() {
  try {
    const res = await api.getUsers({ page: 1, page_size: 100 })
    users.value = (res.users || []).map(u => ({ ...u, _tier: '' }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function setMembership(u) {
  if (!u._tier) return
  try {
    await api.updateMembership(u.id, { days: parseInt(u._tier) })
    u._tier = ''
    alert('设置成功')
  } catch (e) {
    alert(e.message || '失败')
  }
}

onMounted(load)
</script>

<style scoped>
.container { max-width: 600px; margin: 0 auto; padding: 24px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.admin-header h2 { font-size: 24px; font-weight: 800; }
.btn { padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }
.btn-ghost { background: #f1f5f9; color: #475569; border: 1px solid #e8ecf2; }
.btn-sm { padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.user-list { display: flex; flex-direction: column; gap: 12px; }
.user-item { background: #fff; border-radius: 14px; padding: 16px 20px; border: 1px solid #e8ecf2; display: flex; justify-content: space-between; align-items: center; }
.user-info { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.user-name { font-size: 15px; font-weight: 600; color: #1a1a2e; }
.user-phone { font-size: 13px; color: #94a3b8; }
.user-role { font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; background: #f1f5f9; color: #64748b; }
.user-actions { display: flex; gap: 8px; align-items: center; }
.tier-select { padding: 6px 8px; border: 1px solid #e8ecf2; border-radius: 6px; font-size: 13px; }
.empty { text-align: center; padding: 60px; color: #94a3b8; font-size: 16px; }
</style>
