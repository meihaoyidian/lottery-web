<template>
  <div class="page">
    <div class="container">
      <div class="admin-header">
        <h2>标记结果</h2>
        <button class="btn btn-ghost" @click="$router.back()">← 返回</button>
      </div>

      <Loading v-if="loading" />

      <div v-else class="form-card">
        <div class="rec-title">{{ rec?.title || '加载中...' }}</div>
        <div class="status-picker">
          <button v-for="opt in statusOptions" :key="opt.value" class="status-btn" :class="{ active: hitStatus === opt.value }" @click="hitStatus = opt.value">
            {{ opt.label }}
          </button>
        </div>
        <div v-if="hitStatus === 'partial'" class="form-item">
          <label>部分好评详情</label>
          <input v-model="partialDetail" class="input" placeholder="如 2✓1" maxlength="20" />
        </div>
        <div class="form-item">
          <label>总结说明</label>
          <textarea v-model="notes" class="textarea" rows="3" placeholder="选填"></textarea>
        </div>
        <button class="btn btn-primary btn-block" :disabled="saving" @click="submit">
          {{ saving ? '保存中...' : '保存结果' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const rec = ref(null)
const hitStatus = ref('hit')
const partialDetail = ref('')
const notes = ref('')

const statusOptions = [
  { value: 'hit', label: '✓ 好评' },
  { value: 'miss', label: '✗ 蓄力' },
  { value: 'partial', label: '◐ 部分好评' },
  { value: 'push', label: '⇄ 走水' }
]

async function load() {
  try {
    const res = await api.getRecommendations({ page: 1, page_size: 50 })
    const id = parseInt(route.params.id)
    rec.value = (res.recommendations || []).find(r => r.id === id)
  } catch (e) {
    error.value = '加载失败'
  } finally {
    loading.value = false
  }
}

async function submit() {
  saving.value = true
  error.value = ''
  try {
    await api.markResult(rec.value.id, {
      hit_status: hitStatus.value,
      partial_detail: partialDetail.value || undefined,
      notes: notes.value || undefined
    })
    router.push('/admin/recommendations')
  } catch (e) {
    error.value = e.message || '保存失败'
  } finally {
    saving.value = false
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
.btn-primary { background: #2563eb; color: #fff; }
.btn-block { width: 100%; padding: 16px; margin-top: 16px; }
.form-card { background: #fff; border-radius: 14px; padding: 24px; border: 1px solid #e8ecf2; }
.rec-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin-bottom: 20px; }
.status-picker { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.status-btn { padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; background: #f8fafc; border: 1px solid #e8ecf2; color: #475569; cursor: pointer; }
.status-btn.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.form-item { margin-bottom: 16px; }
.form-item label { display: block; font-size: 14px; font-weight: 600; color: #475569; margin-bottom: 8px; }
.input, .textarea { width: 100%; padding: 12px; border: 1px solid #e8ecf2; border-radius: 8px; font-size: 14px; box-sizing: border-box; }
.textarea { resize: vertical; font-family: inherit; }
.error { color: #dc2626; font-size: 14px; text-align: center; margin-top: 8px; }
</style>
