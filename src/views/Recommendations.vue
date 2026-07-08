<template>
  <div class="page">
    <Loading v-if="loading" />

    <div v-else class="container">
      <!-- 状态条 -->
      <div v-if="scheduleStatus" class="schedule-bar" :class="scheduleStatus.css">
        <img class="schedule-logo" src="/logo.png" alt="logo" />
        <span class="schedule-text">{{ scheduleStatus.text }}</span>
        <div v-if="scheduleStatus.tag" class="schedule-tag" :class="scheduleStatus.css">
          <span>{{ scheduleStatus.tag }}</span>
        </div>
      </div>

      <!-- 热度条 -->
      <div v-if="socialProof.totalUsers" class="heat-bar">
        <div class="heat-inner">
          <div class="heat-live">
            <div class="heat-dot"></div>
            <span class="heat-live-text">实时</span>
          </div>
          <span class="heat-num">{{ socialProof.todayViews }}</span>
          <span class="heat-text">次今日分析</span>
          <span class="heat-sep">·</span>
          <span class="heat-num">{{ socialProof.totalUsers }}</span>
          <span class="heat-text">位用户使用</span>
        </div>
      </div>

      <!-- 体验提示 -->
      <div v-if="isTrial" class="trial-tip">
        <img class="trial-tip-logo" src="/logo.png" alt="logo" />
        <div class="trial-tip-body">
          <span class="trial-tip-text">已为您开通 1 天体验专享</span>
          <span class="trial-tip-sub">体验专享权益已生效</span>
        </div>
      </div>

      <!-- 昨日战绩 -->
      <div v-if="latestAchievement" class="achievement-banner">
        <div class="banner-glow"></div>
        <div class="banner-header">
          <div class="banner-left">
            <div class="banner-content">
              <div class="banner-title">{{ latestAchievement.title }}</div>
              <div v-if="latestAchievement.subtitle" class="banner-subtitle">{{ latestAchievement.subtitle }}</div>
            </div>
          </div>
          <div class="banner-right">
            <div class="accuracy-badge">
              <span>↗ 昨日成绩</span>
            </div>
          </div>
        </div>
        <div v-if="latestAchievement.highlights?.length" class="highlights-container">
          <div v-for="(h, i) in latestAchievement.highlights" :key="i" class="highlight-tag">
            <span v-if="h.icon" class="highlight-icon">{{ h.icon }}</span>
            <span class="highlight-text">{{ h.text }}</span>
          </div>
        </div>
        <div v-if="latestAchievement.description" class="description-container">
          <span class="description-text">{{ latestAchievement.description }}</span>
        </div>
      </div>

      <!-- 筛选条 -->
      <div class="filter">
        <button
          v-for="(s, i) in sportTypes"
          :key="s.value"
          class="filter-item"
          :class="{ 'filter-on': sportTypeIndex === i }"
          @click="onSportFilter(i)"
        >{{ s.name }}</button>
      </div>

      <!-- 空状态 -->
      <div v-if="recommendations.length === 0" class="empty">
        <span class="empty-icon">📋</span>
        <span class="empty-text">今日场次更新中</span>
        <span class="empty-hint">每日下午2点-6点之间更新，敬请关注</span>
      </div>

      <!-- 列表 -->
      <div v-else class="list">
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
        <div v-if="hasMore" class="more" @click="loadMore">
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

// 状态映射
const statusMap = {
  settling:  { text: '昨日场次待结束，待更新赛果', tag: '更新中', css: 'tag-pending' },
  empty:     { text: '今日场次更新中，预计14:00发布', tag: '待更新', css: 'tag-pending' },
  created:   { text: '今日场次已更新，数据模型更新中', tag: '更新中', css: 'tag-live' },
  analyzed:  { text: '今日方案已更新', tag: '已更新', css: 'tag-live' }
}

function recHasAnalysis(rec) {
  const pd = rec.prediction_data
  if (!pd || !pd.single_matches) return false
  return pd.single_matches.some(m => m.total_points != null || m.handicap != null)
}

async function loadRecommendations(isLoadMore = false) {
  if (isLoadMore && (loadingMore.value || !hasMore.value)) return

  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

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

    recommendations.value = isLoadMore
      ? [...recommendations.value, ...processed]
      : processed

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
  try {
    latestAchievement.value = await api.getLatestAchievement()
  } catch { /* ignore */ }
}

function onSportFilter(index) {
  if (index === sportTypeIndex.value) return
  sportTypeIndex.value = index
  page.value = 1
  recommendations.value = []
  loadRecommendations()
}

function loadMore() {
  loadRecommendations(true)
}

onMounted(async () => {
  await auth.fetchUser()
  await Promise.all([
    loadScheduleStatus(),
    loadRecommendations(),
    loadSocialProof(),
    loadAchievement()
  ])
})
</script>

<style scoped>
.container { max-width: 480px; margin: 0 auto; }

/* ===== SCHEDULE BAR ===== */
.schedule-bar {
  margin: 16px 24px; padding: 18px 24px; border-radius: 16px;
  display: flex; align-items: center; gap: 14px; border-left: 6px solid #94a3b8;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05); position: relative; overflow: hidden;
}
.schedule-bar.tag-pending { background: linear-gradient(135deg, #fffbeb, #fff7ed); border-left-color: #f59e0b; }
.schedule-bar.tag-live { background: linear-gradient(135deg, #eff6ff, #f8faff); border-left-color: #3b82f6; }
.schedule-bar.tag-live::after {
  content: ''; position: absolute; top: 0; left: -60%; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.06), transparent);
  animation: shimmer 3s ease-in-out infinite; pointer-events: none;
}
.schedule-logo { width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0; }
.schedule-text { flex: 1; font-size: 15px; color: #1e293b; font-weight: 600; }
.schedule-tag { padding: 8px 20px; border-radius: 20px; flex-shrink: 0; }
.schedule-tag span { font-size: 12px; font-weight: 700; }
.schedule-tag.tag-pending { background: #fef3c7; }
.schedule-tag.tag-pending span { color: #b45309; }
.schedule-tag.tag-live { background: #dbeafe; }
.schedule-tag.tag-live span { color: #1d4ed8; }

@keyframes shimmer {
  0% { left: -60%; } 100% { left: 120%; }
}

/* ===== HEAT BAR ===== */
.heat-bar { margin: 0 24px 12px; }
.heat-inner {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 14px 24px; background: #f8fafc; border-radius: 12px;
  border: 1px solid #e8ecf2;
}
.heat-live { display: flex; align-items: center; gap: 6px; margin-right: 10px; }
.heat-dot {
  width: 12px; height: 12px; border-radius: 50%; background: #22c55e;
  animation: heat-pulse 2s ease-in-out infinite;
}
.heat-live-text { font-size: 11px; font-weight: 600; color: #16a34a; }
.heat-num { font-size: 15px; font-weight: 700; color: #1e293b; }
.heat-text { font-size: 12px; color: #94a3b8; }
.heat-sep { font-size: 12px; color: #cbd5e1; margin: 0 4px; }

@keyframes heat-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.7); }
}

/* ===== TRIAL TIP ===== */
.trial-tip {
  margin: 16px 24px; padding: 20px 24px;
  background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
  border-radius: 14px; border: 1px solid #a7f3d0;
  border-left: 6px solid #10b981;
  display: flex; align-items: center; gap: 16px;
}
.trial-tip-logo { width: 48px; height: 48px; border-radius: 50%; }
.trial-tip-body { display: flex; flex-direction: column; gap: 4px; }
.trial-tip-text { font-size: 16px; font-weight: 700; color: #065f46; }
.trial-tip-sub { font-size: 12px; color: #10b981; font-weight: 500; }

/* ===== ACHIEVEMENT BANNER ===== */
.achievement-banner {
  margin: 20px 24px; padding: 36px 28px;
  background: linear-gradient(160deg, #0f172a, #1e3a8a, #2563eb);
  border-radius: 20px; position: relative; overflow: hidden;
}
.banner-glow {
  position: absolute; top: -20%; right: -8%; width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
  border-radius: 50%;
}
.banner-header { display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }
.banner-left { flex: 1; min-width: 0; margin-right: 16px; }
.banner-title { color: #fff; font-size: 16px; font-weight: 800; margin-bottom: 8px; }
.banner-subtitle { color: rgba(255,255,255,0.85); font-size: 12px; }
.accuracy-badge {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  padding: 10px 20px; border-radius: 40px; flex-shrink: 0;
}
.accuracy-badge span { color: #fff; font-size: 13px; font-weight: 700; }
.highlights-container { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 24px; position: relative; z-index: 1; }
.highlight-tag {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15); border-radius: 24px;
}
.highlight-icon { font-size: 15px; }
.highlight-text { color: #fff; font-size: 12px; font-weight: 600; }
.description-container { margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.15); position: relative; z-index: 1; }
.description-text { color: rgba(255,255,255,0.9); font-size: 13px; line-height: 1.8; display: block; }

/* ===== FILTER ===== */
.filter { margin: 16px 24px; display: flex; justify-content: center; gap: 12px; }
.filter-item {
  padding: 12px 28px; background: #fff; border: 1px solid #e8ecf2;
  border-radius: 32px; font-size: 15px; font-weight: 500; color: #64748b;
  cursor: pointer; transition: all 0.2s;
}
.filter-on { background: #2563eb; color: #fff; border-color: #2563eb; font-weight: 600; }

/* ===== EMPTY ===== */
.empty { text-align: center; padding: 80px 40px; }
.empty-icon { font-size: 36px; margin-bottom: 16px; display: block; }
.empty-text { font-size: 16px; color: #64748b; font-weight: 600; }
.empty-hint { font-size: 14px; color: #94a3b8; margin-top: 8px; display: block; }

/* ===== LIST ===== */
.list { padding: 0 24px 40px; }
.more { text-align: center; padding: 40px 0; font-size: 16px; color: #2563eb; font-weight: 500; cursor: pointer; }
</style>
