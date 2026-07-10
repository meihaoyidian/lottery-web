<template>
  <div class="page">
    <Loading v-if="loading" />

    <div v-else class="container">
      <!-- 状态条 -->
      <div v-if="scheduleStatus" class="status-bar" :class="scheduleStatus.css">
        <div class="status-dot" :class="scheduleStatus.css"></div>
        <span class="status-text">
          <span class="status-text-full">{{ scheduleStatus.text }}</span>
          <span class="status-text-short">{{ scheduleStatus.short || scheduleStatus.text }}</span>
        </span>
        <span v-if="scheduleStatus.tag" class="status-tag" :class="scheduleStatus.css">{{ scheduleStatus.tag }}</span>
      </div>

      <!-- 实时热度 -->
      <div v-if="socialProof.totalUsers" class="heat-row">
        <span class="heat-live"><i class="heat-pulse"></i>实时</span>
        <span class="heat-num">{{ socialProof.todayViews }}</span>
        <span class="heat-label">次今日分析</span>
        <span class="heat-dot-sep">·</span>
        <span class="heat-num">{{ socialProof.totalUsers }}</span>
        <span class="heat-label">位会员在用</span>
      </div>

      <!-- 昨日战绩 Banner -->
      <div
        v-if="latestAchievement"
        class="achievement-banner"
        :class="{ 'is-admin': auth.isAdmin() }"
        @click="navigateToAchievement"
      >
        <!-- 背景光晕层 -->
        <div class="ach-atmosphere">
          <div class="ach-orb ach-orb--primary"></div>
          <div class="ach-orb ach-orb--secondary"></div>
        </div>

        <div class="ach-inner">
          <!-- 头部：标签 + 徽章 -->
          <div class="ach-header">
            <div class="ach-header-label">
              <span class="ach-dot"></span>
              <span class="ach-label-text">昨日 AI 战绩</span>
            </div>
            <div class="ach-badge">
              <svg class="ach-badge-icon" viewBox="0 0 16 16" fill="none">
                <path d="M3 13L13 3M13 3H5.5M13 3v7.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>昨日战绩</span>
            </div>
          </div>

          <!-- 主体：标题 + 副标题 -->
          <div class="ach-body">
            <h3 class="ach-title">{{ latestAchievement.title }}</h3>
            <p v-if="latestAchievement.subtitle" class="ach-subtitle">{{ latestAchievement.subtitle }}</p>
          </div>

          <!-- 亮点标签 -->
          <div v-if="latestAchievement.highlights?.length" class="ach-highlights">
            <span v-for="(h, i) in latestAchievement.highlights" :key="i" class="ach-highlight-tag">
              <span v-if="h.icon" class="ach-highlight-icon">{{ h.icon }}</span>
              <span>{{ h.text }}</span>
            </span>
          </div>

          <!-- 描述 -->
          <div v-if="latestAchievement.description" class="ach-footer">
            <p class="ach-desc">{{ latestAchievement.description }}</p>
          </div>

          <!-- 管理员入口暗示 -->
          <div v-if="auth.isAdmin()" class="ach-admin-hint">
            <svg viewBox="0 0 16 16" fill="none" class="ach-admin-icon">
              <path d="M3 8h10M8 3l5 5-5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>点击管理战绩</span>
          </div>
        </div>
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
        <button class="empty-action" @click="$router.push('/history')">查看历史战绩 →</button>
      </div>

      <!-- 推荐列表 -->
      <div v-else class="rec-list">
        <RecommendationCard
          v-for="(rec, index) in recommendations"
          :key="rec.id"
          :recommendation="rec"
          :showAnalysis="rec.showAnalysis"
          :isAnalysisPending="rec.isAnalysisPending"
          :isFirst="index === 0"
          @upgrade="openUpgrade"
          @share="openShare(rec)"
        />
        <div v-if="hasMore" class="load-more" @click="loadMore">
          <span>{{ loadingMore ? '加载中...' : '加载更多' }}</span>
        </div>
      </div>
    </div>

    <!-- 非会员：开通会员浮动按钮 + 二维码弹窗（共享组件） -->
    <UpgradeGuide ref="upgradeRef" :showFab="showUpgradeEntry" />

    <!-- 分享弹窗 -->
    <ShareModal :show="showShare" :data="shareData" @close="showShare=false" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import RecommendationCard from '../components/RecommendationCard.vue'
import UpgradeGuide from '../components/UpgradeGuide.vue'
import ShareModal from '../components/ShareModal.vue'
import Loading from '../components/Loading.vue'

const auth = useAuthStore()
const router = useRouter()

const loading = ref(true)
const loadingMore = ref(false)
const recommendations = ref([])
const viewedIds = new Set()
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

// 二维码升级弹窗（非会员引导，共享组件）
const upgradeRef = ref(null)
// 非会员（且非管理员）才显示升级入口，未登录也显示
const showUpgradeEntry = computed(() => !auth.isPaidUser() && !auth.isAdmin())
function openUpgrade() {
  upgradeRef.value?.open()
}

// 分享
const showShare = ref(false)
const shareData = ref({})
function openShare(rec) {
  const m = rec.prediction_data?.single_matches?.[0] || {}
  const preds = [m.total_points, m.handicap].filter(Boolean).join(' / ')
  shareData.value = {
    predictionType: rec.prediction_type || 'football',
    homeTeam: m.home_team || '',
    awayTeam: m.away_team || '',
    prediction: preds || '',
    resultLabel: '',
    resultStatus: '',
    date: ''
  }
  showShare.value = true
}
// 非会员进页面自动弹一次（同一会话不重复）
function maybeAutoPopup() {
  if (!showUpgradeEntry.value) return
  if (sessionStorage.getItem('upgrade_popup_shown')) return
  sessionStorage.setItem('upgrade_popup_shown', '1')
  upgradeRef.value?.open()
}

// 今日流程进度：场次(≤14点) → 推荐数据(16-18点) → 确认方案(19-20点)
// text 桌面完整文案；short 移动端精简文案
const statusMap = {
  pending:    { text: '今日场次更新中，预计下午 2 点前发布', short: '场次更新中 · 预计 14:00 前', tag: '待更新', css: 'st-pending' },
  delayed:    { text: '今日场次更新中，请稍候',                short: '场次更新中，请稍候',        tag: '待更新', css: 'st-pending' },
  created:    { text: '今日场次已更新，推荐数据分析中，预计下午 4–6 点', short: '数据分析中 · 预计 16–18 点', tag: '分析中', css: 'st-live' },
  analyzing:  { text: 'AI 推荐数据更新中，预计晚间完成',      short: '推荐数据更新中',            tag: '更新中', css: 'st-live' },
  analyzed:   { text: '推荐数据已更新，等待晚间确认方案',      short: '数据已更新 · 待确认',        tag: '已更新', css: 'st-live' },
  confirming: { text: '今日方案确认中，预计晚 7–8 点完成',    short: '方案确认中 · 预计 19–20 点', tag: '确认中', css: 'st-done' },
  confirmed:  { text: '今日方案已全部确认发布',              short: '方案已确认发布',            tag: '已确认', css: 'st-done' }
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
      const show = pending ? false : isPaidUser.value
      return { ...rec, showAnalysis: show, isAnalysisPending: pending }
    })

    recommendations.value = isLoadMore ? [...recommendations.value, ...processed] : processed
    page.value = p
    hasMore.value = p < res.total_pages
    // 记录浏览（异步，去重）
    processed.forEach(r => { if (!viewedIds.has(r.id)) { viewedIds.add(r.id); api.recordView(r.id).catch(()=>{}) } })
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
    const mapped = statusMap[res.status] || statusMap.pending
    scheduleStatus.value = { ...mapped, status: res.status || 'pending' }
  } catch {
    // 网络异常兜底：按时间猜测空态文案，不误导
    const fallback = new Date().getHours() < 14 ? statusMap.pending : statusMap.delayed
    scheduleStatus.value = { ...fallback, status: 'pending' }
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
    // 添加 _t 参数破坏浏览器 HTTP 缓存
    const achievement = await api.getLatestAchievement({ _t: Date.now() })
    if (achievement) {
      // 解析 highlights：后端 JSON 字段可能返回字符串
      if (achievement.highlights && typeof achievement.highlights === 'string') {
        try { achievement.highlights = JSON.parse(achievement.highlights) } catch { achievement.highlights = [] }
      }
      if (!Array.isArray(achievement.highlights)) {
        achievement.highlights = []
      }
      // trim 尾部换行，避免 white-space:pre-line 渲染多余空白行
      if (achievement.description) {
        achievement.description = achievement.description.replace(/\n+$/, '')
      }
      latestAchievement.value = achievement
    }
  } catch { /* ignore */ }
}

// 页面可见时静默刷新 banner 数据（等同小程序 onShow）
async function refreshBannerData() {
  await Promise.all([
    loadAchievement(),
    loadSocialProof(),
    loadScheduleStatus()
  ])
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    refreshBannerData()
  }
}

function handlePageShow(event) {
  // bfcache 恢复：页面从浏览器往返缓存中恢复时重新拉取
  if (event.persisted) {
    refreshBannerData()
  }
}

// 管理员点击战绩 banner → 跳转编辑页
function navigateToAchievement() {
  if (!auth.isAdmin() || !latestAchievement.value) return
  router.push(`/admin/achievements/edit/${latestAchievement.value.id}`)
}

function onSportFilter(index) {
  if (index === sportTypeIndex.value) return
  sportTypeIndex.value = index
  page.value = 1
  recommendations.value = []
  loadRecommendations()
}

function loadMore() { loadRecommendations(true) }

// 登录/退出时重新加载页面数据
watch(() => auth.token, () => {
  page.value = 1
  recommendations.value = []
  loadRecommendations()
  loadScheduleStatus()
})

onMounted(async () => {
  // 已登录则拉取用户信息，未登录也能浏览赛事页
  if (auth.token) await auth.fetchUser()
  await Promise.all([loadScheduleStatus(), loadRecommendations(), loadSocialProof(), loadAchievement()])

  // 非会员（含未登录）自动弹一次二维码引导
  maybeAutoPopup()

  // 页面可见性监听：等同小程序 onShow，切换 tab 或从其他页面返回时自动刷新
  document.addEventListener('visibilitychange', handleVisibilityChange)
  window.addEventListener('pageshow', handlePageShow)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('pageshow', handlePageShow)
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
.status-bar.st-done {
  background: linear-gradient(135deg, #ECFDF5, #F0FDF4);
  border-color: #A7F3D0;
  overflow: hidden; position: relative;
}
.status-bar.st-done::after {
  content: ''; position: absolute; top: 0; left: -60%; width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(16,185,129,0.06), transparent);
  animation: shimmer 3s ease-in-out infinite; pointer-events: none;
}
@keyframes shimmer { 0% { left: -60%; } 100% { left: 120%; } }

.status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.status-dot.st-pending { background: #F59E0B; animation: pulse-dot 2s ease-in-out infinite; }
.status-dot.st-live { background: #6366F1; animation: pulse-dot 2s ease-in-out infinite; }
.status-dot.st-done { background: #10B981; animation: pulse-dot 2s ease-in-out infinite; }
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-text {
  flex: 1; min-width: 0; font-size: 15px; font-weight: 600; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* 桌面显示完整文案，移动端显示精简文案 */
.status-text-short { display: none; }
.status-tag {
  padding: 4px 14px; border-radius: 20px; font-size: 13px; font-weight: 700;
  flex-shrink: 0;
}
.status-tag.st-pending { background: #FEF3C7; color: #92400E; }
.status-tag.st-live { background: #C7D2FE; color: #3730A3; }
.status-tag.st-done { background: #D1FAE5; color: #065F46; }

/* ===========================
   实时热度
   =========================== */
.heat-row {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 10px 16px; margin-bottom: 12px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); font-size: 14px;
}
.heat-live { display: inline-flex; align-items: center; gap: 6px; margin-right: 8px; font-weight: 600; color: #059669; font-size: 13px; }
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
   昨日战绩 Banner
   =========================== */
.achievement-banner {
  position: relative;
  margin-bottom: 18px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  cursor: default;
  transition: box-shadow 0.35s ease, transform 0.35s ease;
  /* 渐变底色 — 比纯白更有层次，保持亮色调 */
  background: linear-gradient(160deg, #FFFFFF 0%, #FAFBFF 40%, #F5F3FF 100%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-md);
  animation: ach-enter 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}

.achievement-banner.is-admin {
  cursor: pointer;
}
.achievement-banner.is-admin:hover {
  border-color: #C7D2FE;
  box-shadow:
    0 8px 30px rgba(99,102,241,0.12),
    0 2px 8px rgba(99,102,241,0.06);
  transform: translateY(-1px);
}
.achievement-banner.is-admin:active {
  transform: translateY(0);
  box-shadow: var(--shadow-md);
}

/* ---- 背景光晕层 ---- */
.ach-atmosphere {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.ach-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.5;
}
.ach-orb--primary {
  width: 220px; height: 220px;
  top: -80px; left: -60px;
  background: rgba(99,102,241,0.12);
  animation: ach-orb-breathe 6s ease-in-out infinite;
}
.ach-orb--secondary {
  width: 180px; height: 180px;
  bottom: -60px; right: -40px;
  background: rgba(167,139,250,0.10);
  animation: ach-orb-breathe 6s ease-in-out 3s infinite;
}

@keyframes ach-orb-breathe {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50%      { transform: scale(1.25); opacity: 0.75; }
}

/* ---- 内容层 ---- */
.ach-inner {
  position: relative;
  z-index: 1;
  padding: 22px 24px 16px;
}

/* ---- 头部 ---- */
.ach-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.ach-header-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.ach-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 6px var(--primary-glow);
  animation: ach-dot-pulse 2s ease-in-out infinite;
}
@keyframes ach-dot-pulse {
  0%, 100% { box-shadow: 0 0 4px var(--primary-glow); }
  50%      { box-shadow: 0 0 12px rgba(99,102,241,0.4); }
}
.ach-label-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* 徽章 */
.ach-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #fff;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  box-shadow: 0 2px 8px rgba(99,102,241,0.25);
  flex-shrink: 0;
}
.ach-badge-icon {
  width: 12px; height: 12px;
  flex-shrink: 0;
}

/* ---- 主体 ---- */
.ach-body {
  min-width: 0;
}
.ach-title {
  font-size: 21px;
  font-weight: 800;
  color: var(--text);
  line-height: 1.3;
  letter-spacing: -0.01em;
}
.ach-subtitle {
  margin-top: 6px;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* ---- 亮点标签 ---- */
.ach-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid var(--border-light);
}
.ach-highlight-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 15px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-hover);
  background: var(--primary-light);
  border: 1px solid rgba(99,102,241,0.08);
  transition: all 0.2s ease;
}
.ach-highlight-tag:hover {
  background: #E0E7FF;
  border-color: #C7D2FE;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99,102,241,0.12);
}
.ach-highlight-icon {
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
}

/* ---- 描述 ---- */
.ach-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}
.ach-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  white-space: pre-line;
}

/* ---- 管理员暗示 ---- */
.ach-admin-hint {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 5px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
  font-size: 12px;
  color: var(--muted);
  opacity: 0;
  transform: translateY(4px);
  transition: all 0.3s ease;
}
.achievement-banner.is-admin:hover .ach-admin-hint {
  opacity: 1;
  transform: translateY(0);
}
.ach-admin-icon {
  width: 13px; height: 13px;
  flex-shrink: 0;
}

/* ---- 入场动画 ---- */
@keyframes ach-enter {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---- 响应式 ---- */
@media (max-width: 767px) {
  .ach-inner { padding: 18px 16px 12px; }
  .ach-title { font-size: 19px; }
  .ach-subtitle { font-size: 15px; }
  .ach-label-text { font-size: 14px; }
  .ach-badge { padding: 5px 12px; font-size: 12px; }
  .ach-highlight-tag { font-size: 14px; padding: 5px 12px; }
  .ach-highlight-icon { font-size: 16px; }
  .ach-desc { font-size: 15px; }
  .ach-orb--primary { width: 140px; height: 140px; top: -50px; left: -40px; }
  .ach-orb--secondary { width: 120px; height: 120px; bottom: -40px; right: -30px; }
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
  font-size: 15px; font-weight: 500; color: var(--muted);
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
.empty-title { font-size: 17px; font-weight: 600; color: var(--text-secondary); }
.empty-desc { font-size: 15px; color: var(--muted); margin-top: 8px; display: block; }
.empty-action {
  margin-top: 20px; padding: 10px 28px;
  background: var(--primary-light); color: var(--primary);
  border: 1px solid #C7D2FE; border-radius: 24px;
  font-size: 15px; font-weight: 600; cursor: pointer;
  transition: all 0.15s;
}
.empty-action:hover { background: #E0E7FF; }

/* ===========================
   列表
   =========================== */
.rec-list { padding-bottom: 40px; }
.load-more {
  text-align: center; padding: 32px 0; cursor: pointer;
  font-size: 16px; font-weight: 600; color: var(--primary);
  transition: color 0.15s;
}
.load-more:hover { color: var(--primary-hover); }

@media (max-width: 767px) {
  .status-bar { padding: 12px 14px; gap: 10px; }
  .status-text { font-size: 15px; }
  .status-text-full { display: none; }
  .status-text-short { display: inline; }
  .status-tag { padding: 5px 12px; font-size: 13px; }
  .filter-btn { padding: 10px 22px; font-size: 16px; min-height:40px; }
  .empty-title { font-size: 18px; }
  .empty-desc { font-size: 16px; }
}

</style>
