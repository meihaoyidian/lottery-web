<template>
  <div class="page">
    <Loading v-if="loading" />

    <div v-else class="container">
      <!-- 未付费用户：好评率 Hero -->
      <div v-if="!isPaidUser">
        <div v-if="statistics" class="free-hero-card">
          <div class="free-hero-glow"></div>
          <div class="free-hero-inner">
            <div class="free-hero-top">
              <img class="free-hero-logo" src="/logo.png" alt="logo" />
              <span class="free-hero-brand">AI竞界</span>
              <div class="free-hero-rate-tag">好评率</div>
            </div>
            <div class="free-hero-stat">
              <span class="free-hero-value">{{ statistics.accuracy_rate }}%</span>
              <div class="free-hero-meta">
                <span>总场次 <span class="fhm-num">{{ statistics.total_count }}</span></span>
                <span class="fhm-sep">|</span>
                <span>好评 <span class="fhm-num fhm-hit">{{ statistics.accurate_count }}</span></span>
              </div>
            </div>
          </div>

          <!-- 月度趋势 -->
          <div v-if="monthlyStats.length > 0" class="free-hero-locked">
            <div class="locked-divider"></div>
            <span class="locked-heading">历史好评率</span>
            <div class="trend-chart">
              <div v-for="m in monthlyStats" :key="m.month" class="trend-bar-col">
                <span class="trend-bar-val">{{ m.hit_rate }}%</span>
                <div class="trend-bar" :style="{ height: (m.hit_rate * 2) + 'px' }"></div>
                <span class="trend-bar-label">{{ m.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 近期好评 -->
        <div v-if="highlights.length > 0" class="hits-section">
          <div class="hits-header">
            <span class="hits-header-title">近期好评场次</span>
          </div>
          <div class="hits-list">
            <div v-for="item in highlights" :key="item.match_id" class="hit-item">
              <div class="hit-item-left">
                <span class="hit-item-check">✓</span>
                <span v-if="item.is_key_match" class="hit-item-tag tag-key">重心</span>
                <span v-else class="hit-item-tag tag-feat">精选</span>
                <span class="hit-item-teams">{{ item.home_team }} vs {{ item.away_team }}</span>
              </div>
              <div class="hit-item-preds">
                <span v-if="item.total_points" class="hit-item-pred">{{ item.total_points }}</span>
                <span v-if="item.handicap" class="hit-item-pred">{{ item.handicap }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 付费用户：完整内容 -->
      <div v-else>
        <!-- Hero -->
        <div v-if="statistics" class="hero-card">
          <div class="hero-glow"></div>
          <div class="hero-top">
            <img class="hero-logo" src="/logo.png" alt="logo" />
            <span class="hero-brand">AI竞界</span>
          </div>
          <div class="hero-stat">
            <span class="hero-value">{{ statistics.accuracy_rate }}%</span>
            <span class="hero-label">总好评率</span>
          </div>
          <div class="hero-meta-row">
            <span class="hero-meta">总场次 <span class="hero-meta-num">{{ statistics.total_count }}</span></span>
            <div class="hero-meta-divider"></div>
            <span class="hero-meta">好评 <span class="hero-meta-num hero-meta-hit">{{ statistics.accurate_count }}</span></span>
          </div>
          <div class="hero-bd-section">
            <span class="hero-bd-label">整体好评</span>
            <div class="hero-breakdown">
              <div v-if="statistics.football_stats" class="hero-bd-item">
                <span class="hero-bd-sport">足球</span>
                <span class="hero-bd-rate">{{ statistics.football_stats.rate }}%</span>
                <span class="hero-bd-count">{{ statistics.football_stats.accurate }}/{{ statistics.football_stats.total }}</span>
              </div>
              <div v-if="statistics.basketball_stats" class="hero-bd-item">
                <span class="hero-bd-sport">篮球</span>
                <span class="hero-bd-rate">{{ statistics.basketball_stats.rate }}%</span>
                <span class="hero-bd-count">{{ statistics.basketball_stats.accurate }}/{{ statistics.basketball_stats.total }}</span>
              </div>
            </div>
          </div>
          <div v-if="statistics.key_match_stats?.total > 0" class="hero-bd-section">
            <span class="hero-bd-label">重心/精选核心</span>
            <div class="hero-breakdown">
              <div v-if="statistics.key_match_stats.football_total > 0" class="hero-bd-item hero-bd-keymatch">
                <span class="hero-bd-sport">足球</span>
                <span class="hero-bd-rate">{{ statistics.key_match_stats.football_rate }}%</span>
                <span class="hero-bd-count">{{ statistics.key_match_stats.football_accurate }}/{{ statistics.key_match_stats.football_total }}</span>
              </div>
              <div v-if="statistics.key_match_stats.basketball_total > 0" class="hero-bd-item hero-bd-keymatch">
                <span class="hero-bd-sport">篮球</span>
                <span class="hero-bd-rate">{{ statistics.key_match_stats.basketball_rate }}%</span>
                <span class="hero-bd-count">{{ statistics.key_match_stats.basketball_accurate }}/{{ statistics.key_match_stats.basketball_total }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 月度趋势 -->
        <div v-if="monthlyStats.length > 0" class="trend-section">
          <div class="trend-header">
            <span class="trend-title">历史好评率</span>
            <span class="trend-stable-tag">持续稳定</span>
          </div>
          <div class="trend-chart">
            <div v-for="m in monthlyStats" :key="m.month" class="trend-bar-col">
              <span class="trend-bar-val">{{ m.hit_rate }}%</span>
              <div class="trend-bar" :style="{ height: (m.hit_rate * 2) + 'px' }"></div>
              <span class="trend-bar-label">{{ m.label }}</span>
            </div>
          </div>
        </div>

        <!-- 筛选 + 列表 -->
        <div class="sport-filter-bar">
          <button :class="['filter-pill', { 'pill-active': sportIdx === 0 }]" @click="sportIdx = 0">全部</button>
          <button :class="['filter-pill', { 'pill-active': sportIdx === 1 }]" @click="sportIdx = 1">足球</button>
          <button :class="['filter-pill', { 'pill-active': sportIdx === 2 }]" @click="sportIdx = 2">篮球</button>
        </div>

        <div class="history-list">
          <div
            v-for="item in historyList"
            :key="item.id"
            class="history-item"
            :class="[
              item.hasKeyMatch ? 'key-match-card' : '',
              item.actual_outcome?.hit_status ? 'outcome-' + item.actual_outcome.hit_status : ''
            ]"
          >
            <div v-if="item.hasKeyMatch" class="key-match-corner"><span>重心</span></div>
            <div class="item-header">
              <div :class="['sport-badge', 'sport-' + item.prediction_type]">
                <span>{{ item.prediction_type === 'football' ? '足球' : '篮球' }}</span>
              </div>
              <div v-if="item.actual_outcome?.hit_status" class="mc-tag mc-tag-result" :class="'mc-result-' + item.actual_outcome.hit_status">
                <i class="mc-dot"></i>{{ item.actual_outcome.hit_status === 'hit' ? '好评' : item.actual_outcome.hit_status === 'partial' ? (item.actual_outcome.partial_detail || '部分') : item.actual_outcome.hit_status === 'push' ? '走水' : '蓄力' }}
              </div>
            </div>
            <div class="match-title-row" @click="toggleExpand(item.id)">
              <span class="match-title">{{ item.title }}</span>
              <span class="expand-arrow">{{ expanded[item.id] ? '▲' : '▼' }}</span>
            </div>
            <div v-if="expanded[item.id]" class="analysis-section-expand">
              <div v-if="item.actual_outcome?.notes" class="notes-section">
                <div class="notes-header"><span class="notes-label">总结说明</span></div>
                <span class="notes-text">{{ item.actual_outcome.notes }}</span>
              </div>
            </div>
          </div>
          <div v-if="!loading && historyList.length === 0" class="empty">
            <span class="empty-icon">📜</span>
            <span class="empty-text">暂无历史记录</span>
            <span class="empty-hint">已完成的推荐会在这里显示</span>
          </div>
        </div>

        <div v-if="!loading && hasMoreHistory" class="load-more">
          <button class="load-more-btn" @click="loadMoreHistory">加载更多</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import Loading from '../components/Loading.vue'

const auth = useAuthStore()
const loading = ref(true)
const statistics = ref(null)
const monthlyStats = ref([])
const highlights = ref([])
const historyList = ref([])
const expanded = ref({})
const hasMoreHistory = ref(false)
const pageNum = ref(1)
const sportIdx = ref(0)

const isPaidUser = computed(() => auth.isPaidUser())

function toggleExpand(id) {
  expanded.value[id] = !expanded.value[id]
}

async function loadData() {
  loading.value = true
  try {
    const [stats, monthly, hl, hist] = await Promise.all([
      api.getStatistics().catch(() => null),
      api.getMonthlyStatistics().catch(() => []),
      api.getHighlights().catch(() => []),
      api.getHistory({ page: 1, page_size: 20 }).catch(() => null)
    ])
    statistics.value = stats
    monthlyStats.value = monthly
    highlights.value = hl
    if (hist) {
      historyList.value = hist.recommendations || []
      hasMoreHistory.value = hist.total_pages > 1
    }
  } catch (e) {
    console.error('加载历史数据失败:', e)
  } finally {
    loading.value = false
  }
}

async function loadMoreHistory() {
  const res = await api.getHistory({ page: pageNum.value + 1, page_size: 20 })
  historyList.value = [...historyList.value, ...(res.recommendations || [])]
  pageNum.value++
  hasMoreHistory.value = pageNum.value < res.total_pages
}

onMounted(loadData)
</script>

<style scoped>
.container { max-width: 480px; margin: 0 auto; }

/* ===== FREE HERO ===== */
.free-hero-card {
  margin: 20px 24px; border-radius: 20px; background: #fff;
  position: relative; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.free-hero-inner {
  position: relative; z-index: 1;
  background: linear-gradient(160deg, #0f172a, #1e3a8a, #2563eb);
  padding: 36px 28px 28px;
}
.free-hero-glow {
  position: absolute; top: -20%; right: -8%; z-index: 0;
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
  border-radius: 50%;
}
.free-hero-top { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; position: relative; z-index: 1; }
.free-hero-logo { width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,0.15); border: 2px solid rgba(255,255,255,0.2); }
.free-hero-brand { font-size: 16px; font-weight: 700; color: rgba(255,255,255,0.9); flex: 1; }
.free-hero-rate-tag {
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);
  padding: 10px 22px; border-radius: 40px; font-size: 12px; font-weight: 700;
  color: #fff; letter-spacing: 1px;
  box-shadow: 0 0 20px rgba(251,191,36,0.15);
}
.free-hero-stat { display: flex; flex-direction: column; align-items: center; gap: 8px; margin-bottom: 20px; position: relative; z-index: 1; }
.free-hero-value { font-size: 68px; font-weight: 900; color: #fff; line-height: 1; }
.free-hero-meta { display: flex; align-items: baseline; gap: 16px; margin-top: 6px; }
.free-hero-meta span { font-size: 14px; color: rgba(255,255,255,0.55); }
.fhm-num { font-size: 20px; font-weight: 800; color: #fff; }
.fhm-hit { color: #4ade80; font-size: 24px; font-weight: 900; }
.fhm-sep { color: rgba(255,255,255,0.2); font-size: 16px; }

.free-hero-locked { position: relative; z-index: 1; padding: 24px 28px 28px; background: #fff; }
.locked-divider { height: 1px; background: #e8ecf2; margin-bottom: 20px; }
.locked-heading { font-size: 16px; font-weight: 700; color: #0F172A; display: block; margin-bottom: 16px; }

/* ===== TREND CHART ===== */
.trend-chart { display: flex; align-items: flex-end; justify-content: space-around; height: 160px; }
.trend-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; max-width: 100px; }
.trend-bar-val { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
.trend-bar {
  width: 48px; border-radius: 10px 10px 6px 6px;
  background: linear-gradient(180deg, #2563eb, #3b82f6);
  min-height: 4px;
}
.trend-bar-label { font-size: 12px; color: #94a3b8; font-weight: 500; margin-top: 10px; }

/* ===== HITS ===== */
.hits-section {
  margin: 0 24px 20px; background: #fff; border-radius: 20px; padding: 24px 28px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04); border: 1px solid #e8ecf2;
}
.hits-header { margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid #f1f5f9; }
.hits-header-title { font-size: 16px; font-weight: 700; color: #0F172A; }
.hit-item { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid #f5f5f5; }
.hit-item:last-child { border-bottom: none; }
.hit-item-left { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.hit-item-check { width: 36px; height: 36px; border-radius: 50%; background: #ECFDF5; color: #059669; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.hit-item-tag { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; flex-shrink: 0; }
.tag-key { color: #e8870a; background: #fffdf5; border: 1px solid #fde68a; }
.tag-feat { color: #7C3AED; background: #FAF8FF; }
.hit-item-teams { font-size: 15px; font-weight: 600; color: #0F172A; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hit-item-preds { display: flex; gap: 8px; flex-shrink: 0; margin-left: 16px; }
.hit-item-pred { font-size: 11px; font-weight: 600; color: #2563EB; background: #EFF6FF; border: 1px solid #BFDBFE; padding: 4px 12px; border-radius: 6px; }

/* ===== PAID HERO ===== */
.hero-card {
  margin: 20px 24px; padding: 36px 32px 28px; border-radius: 24px;
  position: relative; overflow: hidden;
  background: linear-gradient(160deg, #0f172a, #1e3a8a, #2563eb);
  box-shadow: 0 12px 32px rgba(37,99,235,0.25);
}
.hero-glow { position: absolute; top: -20%; right: -10%; width: 280px; height: 280px; background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%); border-radius: 50%; pointer-events: none; }
.hero-top { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; position: relative; z-index: 1; }
.hero-logo { width: 48px; height: 48px; border-radius: 50%; background: rgba(255,255,255,0.15); }
.hero-brand { font-size: 16px; font-weight: 700; color: rgba(255,255,255,0.85); }
.hero-stat { display: flex; flex-direction: column; align-items: center; gap: 6px; margin-bottom: 20px; position: relative; z-index: 1; }
.hero-value { font-size: 68px; font-weight: 900; color: #fff; line-height: 1; }
.hero-label { font-size: 15px; color: rgba(255,255,255,0.6); font-weight: 500; }
.hero-meta-row { display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 20px; position: relative; z-index: 1; }
.hero-meta { font-size: 14px; color: rgba(255,255,255,0.55); }
.hero-meta-num { font-size: 16px; font-weight: 700; color: rgba(255,255,255,0.9); }
.hero-meta-hit { color: #4ade80; }
.hero-meta-divider { width: 1px; height: 24px; background: rgba(255,255,255,0.15); }
.hero-bd-section { margin-bottom: 14px; position: relative; z-index: 1; }
.hero-bd-section:last-child { margin-bottom: 0; }
.hero-bd-label { display: block; font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.35); margin-bottom: 10px; }
.hero-breakdown { display: flex; gap: 12px; }
.hero-bd-item { flex: 1; padding: 16px 12px; background: rgba(255,255,255,0.12); border-radius: 14px; display: flex; flex-direction: column; align-items: center; gap: 4px; border: 1px solid rgba(255,255,255,0.1); }
.hero-bd-keymatch { background: rgba(251,191,36,0.12); border-color: rgba(251,191,36,0.25); }
.hero-bd-sport { font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.55); }
.hero-bd-rate { font-size: 20px; font-weight: 800; color: #fff; line-height: 1; }
.hero-bd-count { font-size: 11px; color: rgba(255,255,255,0.4); }
.hero-bd-keymatch .hero-bd-sport { color: #fbbf24; }
.hero-bd-keymatch .hero-bd-rate { color: #fbbf24; }

/* ===== TREND SECTION ===== */
.trend-section { margin: 0 24px 24px; background: #fff; border-radius: 20px; border: 1px solid #e8ecf2; padding: 24px 24px 20px; }
.trend-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; }
.trend-title { font-size: 16px; font-weight: 700; color: #1a1a2e; }
.trend-stable-tag { font-size: 12px; font-weight: 600; color: #059669; background: #ecfdf5; padding: 4px 16px; border-radius: 20px; }

/* ===== HISTORY LIST ===== */
.sport-filter-bar { margin: 16px 24px; display: flex; gap: 12px; justify-content: center; }
.filter-pill { padding: 10px 24px; background: #fff; border-radius: 32px; font-size: 14px; font-weight: 500; color: #666; border: 1px solid #e8ecf2; cursor: pointer; }
.filter-pill.pill-active { background: #2563eb; color: #fff; border-color: #2563eb; font-weight: 600; box-shadow: 0 4px 12px rgba(37,99,235,0.2); }

.history-list { padding: 0 24px 24px; }
.history-item {
  background: #fff; border-radius: 16px; padding: 24px 28px; margin-bottom: 16px;
  border: 1px solid #e8ecf2; position: relative; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.history-item::before { content: ''; position: absolute; left: 0; top: 16px; bottom: 16px; width: 6px; border-radius: 0 3px 3px 0; }
.history-item.key-match-card { border-color: #fde68a; }
.history-item.key-match-card::before { background: #f59e0b; }
.history-item.outcome-hit { border-color: #a7f3d0; box-shadow: 0 4px 20px rgba(16,185,129,0.1); }
.history-item.outcome-hit::before { background: #10b981; }
.history-item.outcome-miss { opacity: 0.7; border-color: #e8ecf2; box-shadow: none; }
.history-item.outcome-miss::before { background: #d1d5db; }
.history-item.outcome-partial { border-color: #fde68a; }
.history-item.outcome-partial::before { background: #f59e0b; }
.history-item.outcome-push { border-color: #e9d5ff; }
.history-item.outcome-push::before { background: #8b5cf6; }

.key-match-corner { position: absolute; top: 0; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #f59e0b, #e8870a); padding: 6px 24px; border-radius: 0 0 12px 12px; z-index: 1; }
.key-match-corner span { font-size: 12px; font-weight: 600; color: #fff; }

.item-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; position: relative; z-index: 5; flex-wrap: wrap; }
.sport-badge { display: flex; align-items: center; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 500; }
.sport-badge.sport-football { background: #e0f7fa; color: #0288d1; }
.sport-badge.sport-basketball { background: #fff3e0; color: #e65100; }

.match-title-row { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.match-title { font-size: 17px; font-weight: 700; color: #1a1a2e; line-height: 1.5; flex: 1; }
.expand-arrow { font-size: 14px; color: #94a3b8; margin-left: 16px; flex-shrink: 0; }

.notes-section { background: #fefce8; border-radius: 12px; padding: 16px 20px; border: 1px solid #fef08a; margin-top: 16px; }
.notes-header { display: flex; align-items: center; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #fef08a; }
.notes-label { font-size: 14px; font-weight: 600; color: #ca8a04; }
.notes-text { font-size: 14px; color: #555; line-height: 1.8; }

/* Result tags (shared) */
.mc-tag { font-size: 10px; font-weight: 600; padding: 4px 12px; border-radius: 6px; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.mc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; display: inline-block; }
.mc-result-hit {
  color: #fff; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 3px 10px rgba(5,150,105,0.35);
  transform: rotate(-3deg); position: relative;
}
.mc-result-hit::after {
  content: ''; position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px;
  border: 2px dashed rgba(255,255,255,0.3); border-radius: 8px; pointer-events: none;
}
.mc-result-push {
  color: #fff; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 3px 10px rgba(124,58,237,0.3);
  transform: rotate(-3deg); position: relative;
}
.mc-result-miss {
  color: #94a3b8; font-size: 11px; font-weight: 500; padding: 4px 12px; border-radius: 8px;
  background: #f1f5f9; border: 1px dashed #d1d5db; transform: rotate(-3deg); opacity: 0.7;
}
.mc-result-partial {
  color: #fff; font-size: 12px; font-weight: 800; padding: 4px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 3px 10px rgba(245,158,11,0.35);
  transform: rotate(-3deg); position: relative;
}

.empty { text-align: center; padding: 60px 40px; }
.empty-icon { font-size: 36px; margin-bottom: 16px; display: block; }
.empty-text { font-size: 16px; color: #666; margin-bottom: 16px; }
.empty-hint { font-size: 14px; color: #999; }
.load-more { padding: 24px; text-align: center; }
.load-more-btn { background: #fff; color: #666; font-size: 15px; border-radius: 12px; padding: 20px 48px; border: 1px solid #e8ecf2; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
</style>
