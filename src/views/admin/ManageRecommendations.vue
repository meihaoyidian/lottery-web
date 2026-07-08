<template>
  <div class="page">
    <div class="container">
      <div class="admin-header">
        <h2>推荐管理</h2>
        <div class="header-actions">
          <button class="btn btn-primary" @click="$router.push('/admin/recommendations/create')">+ 创建</button>
          <button class="btn btn-ghost" @click="$router.push('/admin/membership')">用户管理</button>
          <button class="btn btn-ghost" @click="$router.push('/')">← 首页</button>
        </div>
      </div>

      <Loading v-if="loading" />

      <div v-else class="rec-list">
        <div v-for="rec in list" :key="rec.id" class="rec-item">
          <div class="rec-top">
            <span class="rec-sport">{{ rec.prediction_type === 'football' ? '足球' : '篮球' }}</span>
            <span class="rec-title">{{ rec.title }}</span>
            <span v-if="rec.actual_outcome?.hit_status" class="outcome-badge" :class="'outcome-' + rec.actual_outcome.hit_status">
              {{ rec.actual_outcome.hit_status === 'hit' ? '好评' : rec.actual_outcome.hit_status === 'partial' ? '部分好评' : rec.actual_outcome.hit_status === 'push' ? '走水' : '蓄力' }}
            </span>
          </div>
          <div class="rec-actions">
            <button class="btn-sm" @click="$router.push(`/admin/recommendations/${rec.id}/edit`)">编辑</button>
            <button class="btn-sm" @click="$router.push(`/admin/recommendations/${rec.id}/result`)">标记结果</button>
            <button class="btn-sm" :class="{ 'btn-confirmed': rec.is_confirmed }" @click="toggleConfirm(rec)">
              {{ rec.is_confirmed ? '✓ 已确认' : '确认' }}
            </button>
          </div>
        </div>
        <div v-if="list.length === 0" class="empty">暂无推荐</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const loading = ref(true)
const list = ref([])

async function load() {
  loading.value = true
  try {
    const res = await api.getRecommendations({ page: 1, page_size: 50 })
    list.value = res.recommendations || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function toggleConfirm(rec) {
  try {
    const res = await api.toggleConfirm(rec.id)
    rec.is_confirmed = res.is_confirmed
  } catch (e) {
    console.error(e)
  }
}

onMounted(load)
</script>

<style scoped>
.container { max-width: 600px; margin: 0 auto; padding: 24px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.admin-header h2 { font-size: 24px; font-weight: 800; color: #1a1a2e; }
.header-actions { display: flex; gap: 8px; }
.btn { padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-ghost { background: #f1f5f9; color: #475569; border: 1px solid #e8ecf2; }
.rec-list { display: flex; flex-direction: column; gap: 12px; }
.rec-item { background: #fff; border-radius: 14px; padding: 18px 20px; border: 1px solid #e8ecf2; }
.rec-top { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.rec-sport { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px; background: #eff6ff; color: #2563eb; }
.rec-title { font-size: 15px; font-weight: 600; color: #1a1a2e; flex: 1; }
.outcome-badge { font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 6px; }
.outcome-hit { background: #ecfdf5; color: #059669; }
.outcome-miss { background: #f1f5f9; color: #94a3b8; }
.outcome-partial { background: #fef3c7; color: #b45309; }
.outcome-push { background: #f5f3ff; color: #7c3aed; }
.rec-actions { display: flex; gap: 8px; }
.btn-sm { padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; background: #f8fafc; border: 1px solid #e8ecf2; color: #475569; cursor: pointer; }
.btn-confirmed { background: #ecfdf5; color: #059669; border-color: #a7f3d0; }
.empty { text-align: center; padding: 60px; color: #94a3b8; font-size: 16px; }
</style>
