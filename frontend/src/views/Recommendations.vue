<template>
  <div class="page">
    <Loading v-if="loading" />

    <div v-else class="container">
      <!-- 状态条 -->
      <div v-if="scheduleStatus" class="status-bar" :class="scheduleStatus.css">
        <div class="status-dot" :class="scheduleStatus.css"></div>
        <span class="status-text">{{ scheduleStatus.text }}</span>
        <span v-if="scheduleStatus.tag" class="status-tag" :class="scheduleStatus.css">{{ scheduleStatus.tag }}</span>
      </div>

      <!-- 实时热度 -->
      <div v-if="socialProof.totalUsers" class="heat-row">
        <span class="heat-live"><i class="heat-pulse"></i>实时</span>
        <span class="heat-num">{{ socialProof.todayViews }}</span>
        <span class="heat-label">次今日分析</span>
        <span class="heat-dot-sep">·</span>
        <span class="heat-num">{{ socialProof.totalUsers }}</span>
        <span class="heat-label">位用户使用</span>
      </div>

      <!-- 体验提示 -->
      <div v-if="isTrial" class="trial-banner">
        <div class="trial-banner-inner">
          <span class="trial-icon"></span>
          <div class="trial-body">
            <span class="trial-title">AI 体验专享已激活</span>
            <span class="trial-sub">1 天全量 AI 分析权益生效中</span>
          </div>
        </div>
      </div>

      <!-- 昨日战绩 -->
      <div v-if="latestAchievement" class="achievement-card">
        <div class="ach-top">
          <div class="ach-left">
            <span class="ach-label">昨日 AI 分析成绩</span>
            <span class="ach-title">{{ latestAchievement.title }}</span>
            <span v-if="latestAchievement.subtitle" class="ach-sub">{{ latestAchievement.subtitle }}</span>
          </div>
          <div class="ach-right">
            <svg class="ach-ring" viewBox="0 0 72 72">
              <circle cx="36" cy="36" r="30" fill="none" stroke="#E2E8F0" stroke-width="6" />
              <circle
                cx="36" cy="36" r="30" fill="none"
                stroke="url(#achGrad)" stroke-width="6"
                stroke-linecap="round"
                :stroke-dasharray="achDasharray"
                stroke-dashoffset="0"
                transform="rotate(-90 36 36)"
              />
              <defs>
                <linearGradient id="achGrad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#6366F1" />
                  <stop offset="100%" stop-color="#8B5CF6" />
                </linearGradient>
              </defs>
            </svg>
            <div class="ach-ring-text">
              <span class="ach-ring-val">{{ achPercent }}%</span>
              <span class="ach-ring-label">好评率</span>
            </div>
          </div>
        </div>
        <!-- highlights -->
        <div v-if="latestAchievement.highlights?.length" class="ach-tags">
          <span v-for="(h, i) in latestAchievement.highlights" :key="i" class="ach-tag">
            <span v-if="h.icon" class="ach-tag-icon">{{ h.icon }}</span>{{ h.text }}
          </span>
        </div>
        <p v-if="latestAchievement.description" class="ach-desc">{{ latestAchievement.description }}</p>
      </div>

      <!-- 筛选 -->
      <div class="filter-row">
        <button
          v-for="(s, i) in sportTypes"
          :key="s.value"
          class="filter-btn"
          :class="{ on: sportTypeIndex === i }"
          @click="onSportFilter(i)"
        >{{ s.name }}</button>
      </div>

      <!-- 空状态 -->
      <div v-if="recommendations.length === 0" class="empty-state">
        <span class="empty-icon"></span>
        <span class="empty-title">今日场次更新中</span>
        <span class="empty-desc">每日下午 2 点至 6 点之间更新，敬请关注</span>
      </div>

      <!-- 推荐列表 -->
      <div v-else class="rec-list">
        <RecommendationCard
          v-for="(rec, index) in recommendations"
          :key="rec.id"
          :recommendation="rec"
          :showAnalysis="rec.showAnalysis"
          :isAnalysisPending="rec.isAnalysisPending"
          :reviewMode="false"
          :isTrial="isTrial"
          :isFirst="index === 0"
        />
        <div v-if="hasMore" class="load-more" @click="loadMore">
          <span>{{ loadingMore ? '加载中...' : '加载更多' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import RecommendationCard from '../components/RecommendationCard.vue'
import Loading from '../components/Loading.vue'

const auth = useAuthStore()

const loading = ref(true)
const loadingMore = ref(false)
const recommendations = ref([])
const latestAchievement = ref(null)
const page = ref(1)
const pageSize = 20
const hasMore = ref(false)
const sportTypeIndex = ref(0)
const sportTypes = [
  { value: '', name: '全部' },
  { value: 'football', name: '足球' },
  { value: 'basketball', name: '篮球' }
]

const scheduleStatus = ref(null)
const socialProof = reactive({ todayViews: 0, totalUsers: 0 })

const isPaidUser = computed(() => auth.isPaidUser())
const isTrial = computed(() => auth.isTrial())

// 成就环形图
const achPercent = computed(() => {
  const raw = latestAchievement.value?.accuracy_rate
  return raw != null ? Math.ceil(Number(raw)) : 0
})
const achDasharray = computed(() => {
  const pct = achPercent.value
  const len = 2 * Math.PI * 30 // ~188.5
  return `${(pct / 100) * len} ${len}`
})

const statusMap = {
  settling:  { text: '昨日场次待结束，数据结算中', tag: '结算中', css: 'st-pending' },
  empty:     { text: '今日 AI 分析方案生成中，预计 14:00 发布', tag: '待更新', css: 'st-pending' },
  created:   { text: '今日方案已创建，AI 模型分析中', tag: '分析中', css: 'st-live' },
  analyzed:  { text: '今日 AI 分析方案已就绪', tag: '已更新', css: 'st-live' }
}

function recHasAnalysis(rec) {
  const pd = rec.prediction_data
  if (!pd || !pd.single_matches) return false
  return pd.single_matches.some(m => m.total_points != null || m.handicap != null)
}

async function loadRecommendations(isLoadMore = false) {
  if (isLoadMore && (loadingMore.value || !hasMore.value)) return
  if (isLoadMore) { loadingMore.value = true } else { loading.value = true }

  try {
    const p = isLoadMore ? page.value + 1 : 1
    const params = { page: p, page_size: pageSize }
    const sportType = sportTypes[sportTypeIndex.value]
    if (sportType?.value) params.prediction_type = sportType.value

    const res = await api.getRecommendations(params)
    const hasFullAccess = isPaidUser.value || auth.isAdmin()

    const processed = res.recommendations.map(rec => {
      const ok = recHasAnalysis(rec)
      const pending = hasFullAccess && !ok
      const show = pending ? false : (isPaidUser.value || isTrial.value)
      return { ...rec, showAnalysis: show, isAnalysisPending: pending }
    })

    recommendations.value = isLoadMore ? [...recommendations.value, ...processed] : processed
    page.value = p
    hasMore.value = p < res.total_pages
  } catch (e) {
    console.error('加载推荐失败:', e)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadScheduleStatus() {
  try {
    const res = await api.getTodayStatus()
    scheduleStatus.value = { ...(statusMap[res.status] || statusMap.empty), status: res.status || 'empty' }
  } catch {
    scheduleStatus.value = { ...statusMap.empty, status: 'empty' }
  }
}

async function loadSocialProof() {
  try {
    const data = await api.getSocialProof()
    if (data) {
      socialProof.todayViews = data.today_views || 0
      socialProof.totalUsers = data.total_users || 0
    }
  } catch { /* ignore */ }
}

async function loadAchievement() {
  try { latestAchievement.value = await api.getLatestAchievement() } catch { /* ignore */ }
}

function onSportFilter(index) {
  if (index === sportTypeIndex.value) return
  sportTypeIndex.value = index
  page.value = 1
  recommendations.value = []
  loadRecommendations()
}

function loadMore() { loadRecommendations(true) }

onMounted(async () => {
  await auth.fetchUser()
  await Promise.all([loadScheduleStatus(), loadRecommendations(), loadSocialProof(), loadAchievement()])
})
</script>

<style scoped>
.container {
  max-width: 1100px; margin: 0 auto; padding: 16px 16px 0;
}
@media (min-width: 768px) {
  .container { padding: 24px 24px 0; }
}

/* ===========================
   状态条
   =========================== */
.status-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 18px; border-radius: 12px;
  margin-bottom: 12px; border: 1px solid transparent;
}
.status-bar.st-pending { background: #FFFBEB; border-color: #FDE68A; }
.status-bar.st-live {
  background: linear-gradient(135deg, #EEF2FF, #F5F3FF);
  border-color: #C7D2FE;
  overflow: hidden; position: relative;
}
.status-bar.st-live::after {
  content: ''; position: absolute; top: 0; left: -60%; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.05), transparent);
  animation: shimmer 3s ease-in-out infinite; pointer-events: none;
}
@keyframes shimmer { 0% { left: -60%; } 100% { left: 120%; } }

.status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.status-dot.st-pending { background: #F59E0B; animation: pulse-dot 2s ease-in-out infinite; }
.status-dot.st-live { background: #6366F1; animation: pulse-dot 2s ease-in-out infinite; }
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-text { flex: 1; font-size: 14px; font-weight: 600; color: var(--text-secondary); }
.status-tag {
  padding: 4px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;
  flex-shrink: 0;
}
.status-tag.st-pending { background: #FEF3C7; color: #92400E; }
.status-tag.st-live { background: #C7D2FE; color: #3730A3; }

/* ===========================
   实时热度
   =========================== */
.heat-row {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 16px; margin-bottom: 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); font-size: 13px;
}
.heat-live { display: inline-flex; align-items: center; gap: 6px; margin-right: 8px; font-weight: 600; color: #059669; font-size: 12px; }
.heat-pulse {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #10B981; animation: heat-pulse 2s ease-in-out infinite;
}
@keyframes heat-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.6); }
}
.heat-num { font-weight: 700; color: var(--text); }
.heat-label { color: var(--muted); }
.heat-dot-sep { color: #CBD5E1; margin: 0 4px; }

/* ===========================
   体验提示
   =========================== */
.trial-banner {
  margin-bottom: 14px; padding: 16px 18px;
  background: linear-gradient(135deg, #ECFDF5, #F0FDF4);
  border: 1px solid #A7F3D0; border-radius: var(--radius);
}
.trial-banner-inner { display: flex; align-items: center; gap: 14px; }
.trial-icon { font-size: 22px; flex-shrink: 0; }
.trial-body { display: flex; flex-direction: column; gap: 2px; }
.trial-title { font-size: 15px; font-weight: 700; color: #065F46; }
.trial-sub { font-size: 12px; color: #10B981; font-weight: 500; }

/* ===========================
   昨日战绩卡片
   =========================== */
.achievement-card {
  margin-bottom: 16px; padding: 24px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.ach-top { display: flex; align-items: center; justify-content: space-between; }
.ach-left { display: flex; flex-direction: column; gap: 4px; }
.ach-label { font-size: 11px; font-weight: 600; color: var(--primary); letter-spacing: 0.06em; }
.ach-title { font-size: 18px; font-weight: 800; color: var(--text); line-height: 1.3; }
.ach-sub { font-size: 13px; color: var(--muted); }

.ach-right { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.ach-ring { width: 72px; height: 72px; }
.ach-ring-text {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.ach-ring-val { font-size: 18px; font-weight: 800; color: var(--text); line-height: 1; }
.ach-ring-label { font-size: 10px; color: var(--muted); margin-top: 2px; }

.ach-tags {
  display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px;
  padding-top: 16px; border-top: 1px solid var(--border-light);
}
.ach-tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; background: var(--primary-light);
  border-radius: 20px; font-size: 13px; font-weight: 600; color: var(--primary-hover);
}
.ach-tag-icon { font-size: 14px; }

.ach-desc {
  margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border-light);
  font-size: 13px; color: var(--text-secondary); line-height: 1.7;
}

/* ===========================
   筛选
   =========================== */
.filter-row {
  display: flex; justify-content: center; gap: 10px; margin-bottom: 16px;
}
.filter-btn {
  padding: 10px 24px; border-radius: 24px;
  background: var(--surface); border: 1px solid var(--border);
  font-size: 14px; font-weight: 500; color: var(--muted);
  transition: all 0.2s;
}
.filter-btn.on {
  background: var(--primary); color: #fff; border-color: var(--primary);
  font-weight: 600; box-shadow: var(--shadow);
}

/* ===========================
   空状态
   =========================== */
.empty-state {
  text-align: center; padding: 80px 20px;
}
.empty-icon { font-size: 40px; display: block; margin-bottom: 16px; }
.empty-title { font-size: 16px; font-weight: 600; color: var(--text-secondary); }
.empty-desc { font-size: 14px; color: var(--muted); margin-top: 8px; display: block; }

/* ===========================
   列表
   =========================== */
.rec-list { padding-bottom: 40px; }
.load-more {
  text-align: center; padding: 32px 0; cursor: pointer;
  font-size: 15px; font-weight: 600; color: var(--primary);
  transition: color 0.15s;
}
.load-more:hover { color: var(--primary-hover); }

@media (max-width: 767px) {
  .status-bar { padding: 12px 14px; }
  .status-text { font-size: 13px; }
  .achievement-card { padding: 20px; }
  .ach-title { font-size: 16px; }
  .filter-btn { padding: 8px 20px; font-size: 13px; }
}
</style>
