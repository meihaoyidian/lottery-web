<template>
  <div class="card" :class="{ 'key-match-card': hasKeyMatch }">
    <!-- 角标 -->
    <div v-if="totalMatchesCount >= 2" class="corner corner-multi">
      <span>精选合集</span>
    </div>
    <div v-if="hasKeyMatch" class="corner corner-key">
      <span>重心</span>
    </div>

    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="sport-badge" :class="predictionType">
        <span>{{ sportName }}</span>
      </div>
    </div>

    <!-- 标题 -->
    <div class="card-title-section">
      <span class="card-title">{{ title }}</span>
    </div>

    <!-- 分析区域 -->
    <div v-if="singleMatches.length > 0 || parlay" class="analysis-section">
      <div class="analysis-content">
        <!-- 单场 -->
        <div v-if="singleMatches.length > 0" class="single-matches">
          <div
            v-for="match in singleMatches"
            :key="match.match_id"
            class="match-card"
            :class="{
              'mc-key': match.is_key_match,
              'mc-featured': match.is_featured,
              'mc-upset': match.is_upset_warning,
              'mc-blurred': match._blur,
              'mc-confirmed': isConfirmed
            }"
          >
            <!-- 已确认角标 -->
            <div v-if="isConfirmed" class="mc-confirmed-badge">
              <span>方案已确认</span>
            </div>

            <!-- 场次头部 -->
            <div class="mc-header">
              <div class="mc-header-left">
                <span class="mc-id">{{ match.match_id }}</span>
                <span v-if="match.is_key_match" class="mc-tag mc-tag-key"><i class="mc-dot"></i>重心</span>
                <span v-if="match.is_featured" class="mc-tag mc-tag-featured"><i class="mc-dot"></i>精选</span>
                <span v-if="match.is_public" class="mc-tag mc-tag-public">公开</span>
                <span v-if="match.is_upset_warning" class="mc-tag mc-tag-upset"><i class="mc-dot"></i>冷门预警</span>
                <span v-if="match.hit_status && match.hit_status !== 'pending'" class="mc-tag mc-tag-result" :class="`mc-result-${match.hit_status}`">
                  <i class="mc-dot"></i>{{ hitLabel(match.hit_status) }}
                </span>
              </div>
              <span v-if="match.prediction_rate" class="mc-tag mc-tag-confidence" :class="confidenceClass(match.prediction_rate)">
                <i class="mc-dot"></i>{{ match.prediction_rate }}% 置信度
              </span>
            </div>

            <!-- 对阵 -->
            <div class="mc-versus">
              <span class="mc-team">{{ match.home_team }}</span>
              <div class="mc-vs-divider"><span>VS</span></div>
              <span class="mc-team">{{ match.away_team }}</span>
            </div>

            <!-- 完整版 -->
            <template v-if="!match._blur">
              <div v-if="match.total_points || match.handicap" class="mc-prediction">
                <div class="mc-pred-items">
                  <span v-if="match.total_points" class="mc-pred-item">{{ match.total_points }}</span>
                  <span v-if="match.handicap" class="mc-pred-item">{{ match.handicap }}</span>
                </div>
              </div>
              <div v-if="match.prediction_basis" class="mc-summary">
                <span class="mc-summary-text">{{ match.prediction_basis }}</span>
              </div>
            </template>

            <!-- 锁定 -->
            <div v-else-if="isAnalysisPending" class="mc-locked mc-pending">
              <span class="mc-locked-text">模型数据实时更新中</span>
            </div>
            <div v-else class="mc-locked mc-member" @click="$emit('upgrade')">
              <svg class="mc-lock-icon" viewBox="0 0 24 24" fill="none">
                <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" stroke-width="1.8"/>
                <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
              <span class="mc-locked-text">开通会员查看 AI 预测</span>
            </div>
          </div>
        </div>

        <!-- 组合（完整版） -->
        <div v-if="parlay && parlay.length > 0 && !blurParlay" class="parlay-section">
          <div class="parlay-section-title">组合方案</div>
          <div v-for="(p, i) in parlay" :key="i" class="parlay-card">
            <span v-if="parlay.length > 1" class="parlay-card-num">#{{ i + 1 }} </span>
            <span class="parlay-bets">{{ p.bet_types.join(' · ') }}</span>
          </div>
        </div>

        <!-- 组合（锁定） -->
        <div v-else-if="parlay && parlay.length > 0 && blurParlay" class="parlay-section parlay-locked" @click="$emit('upgrade')">
          <div class="parlay-locked-header">
            <span class="parlay-locked-title">组合方案</span>
            <div class="parlay-locked-badge"><span>{{ isAnalysisPending ? '即将更新' : '开通会员查看' }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 预告条 -->
    <div v-if="isAnalysisPending && isFirst" class="mc-pending-bar">
      <span>模型数据实时更新中 · 预计晚7点同步更新</span>
    </div>
    <div v-else-if="isAnalysisPending && !isFirst" class="mc-pending-hint">
      <span>模型数据实时更新中</span>
    </div>

    <!-- 后续卡片轻量提示 -->
    <div v-if="!showAnalysis && !isAnalysisPending && !isFirst" class="mc-upgrade-hint" @click="$emit('upgrade')">
      <svg class="mc-hint-lock" viewBox="0 0 24 24" fill="none">
        <rect x="5" y="11" width="14" height="9" rx="2" stroke="currentColor" stroke-width="1.8"/>
        <path d="M8 11V8a4 4 0 0 1 8 0v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <span>开通会员解锁完整分析</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  recommendation: { type: Object, required: true },
  showAnalysis: { type: Boolean, default: false },
  isAnalysisPending: { type: Boolean, default: false },
  isFirst: { type: Boolean, default: false }
})

defineEmits(['upgrade'])

const title = computed(() => props.recommendation.title || '')
const sportName = computed(() => ({
  football: '足球', basketball: '篮球'
}[props.recommendation.prediction_type] || props.recommendation.prediction_type || ''))
const predictionType = computed(() => props.recommendation.prediction_type || '')
const hasKeyMatch = computed(() => props.recommendation.prediction_data?.single_matches?.some(m => m.is_key_match))
const totalMatchesCount = computed(() => props.recommendation.prediction_data?.single_matches?.length || 0)
const isConfirmed = computed(() => props.recommendation.is_confirmed)
const singleMatches = computed(() => props.recommendation.prediction_data?.single_matches || [])
const parlay = computed(() => props.recommendation.prediction_data?.parlays || props.recommendation.prediction_data?.parlay || null)
const blurParlay = computed(() => props.recommendation._blur_parlay)

function hitLabel(status) {
  if (status === 'hit') return '好评'
  if (status === 'push') return '走水'
  return '蓄力'
}

function confidenceClass(rate) {
  if (rate >= 75) return 'rate-high'
  if (rate >= 50) return 'rate-normal'
  return 'rate-cold'
}
</script>

<style scoped>
.card { background:var(--surface); border-radius:var(--radius-lg); padding:22px 24px; margin-bottom:14px; border:1px solid var(--border); box-shadow:var(--shadow-sm); position:relative; overflow:hidden; }
.key-match-card { border-color:#FDE68A; }
@media (max-width:767px) { .card { padding:18px 16px; border-radius:var(--radius); } }

/* 重心场次左边金色条 */
.key-match-card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; background:#F59E0B; }

.corner { position:absolute; top:0; left:50%; transform:translateX(-50%); padding:4px 20px; border-radius:0 0 8px 8px; font-size:12px; font-weight:600; color:#fff; z-index:1; }
.corner-multi { background:#6366F1; }
.corner-key { background:#F59E0B; }

.card-header { margin-bottom:12px; }
.sport-badge { display:inline-flex; padding:5px 14px; border-radius:20px; font-size:13px; font-weight:600; }
.sport-badge.football { background:#E0F7FA; color:#0288D1; }
.sport-badge.basketball { background:#FFF3E0; color:#E65100; }

.card-title-section { margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--border-light); }
.card-title { font-size:17px; font-weight:700; color:var(--text); line-height:1.5; display:block; }

.analysis-section { background:var(--bg); border-radius:var(--radius); padding:18px; border:1px solid var(--border-light); }
.single-matches { display:flex; flex-direction:column; gap:12px; }

/* 场次卡片 -- 和历史战绩页统一风格 */
.match-card { background:#fff; border-radius:var(--radius-sm); padding:16px 18px; border:1px solid var(--border-light); position:relative; }
.match-card::before { content:''; position:absolute; left:0; top:12px; bottom:12px; width:4px; border-radius:0 2px 2px 0; }
.match-card.mc-key { border-color:#FDE68A; background:#FFFDF5; }
.match-card.mc-key::before { background:#F59E0B; }
.match-card.mc-featured { border-color:#DDD6FE; background:#FAFAFE; }
.match-card.mc-featured::before { background:#8B5CF6; }
.match-card.mc-confirmed { border-color:#A7F3D0; }
@media (max-width:767px) { .match-card { padding:14px 14px; } }

/* 已确认角标 — 左上方折叠角标，与小程序一致 */
.match-card.mc-confirmed { padding-top: 36px; }
.mc-confirmed-badge {
  position:absolute; top:0; left:0; z-index:2;
  background:linear-gradient(135deg,#0d9488,#0f766e); color:#fff;
  font-size:11px; font-weight:600; padding:3px 16px;
  border-radius:0 0 8px 0; letter-spacing:0.5px;
}

.mc-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:6px; }
.mc-header-left { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.mc-id { font-size:12px; font-weight:600; color:var(--muted); }
.mc-tag { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; }
.mc-tag-key { color:#B45309; background:#FFFDF5; border:1px solid #FDE68A; }
.mc-tag-featured { color:#6D28D9; background:#FAFAFE; border:1px solid #DDD6FE; }
.mc-tag-public { color:#059669; background:#ECFDF5; }
.mc-tag-upset { color:#DC2626; background:#FEF2F2; }
.mc-tag-result { font-size:11px; font-weight:700; padding:2px 8px; border-radius:10px; color:#fff; }
.mc-result-hit { background:#10B981; }
.mc-result-push { background:#8B5CF6; }
.mc-result-miss { background:#E2E8F0; color:#94A3B8; }
.mc-tag-confidence { font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px; }
.rate-high { color:#059669; background:#ECFDF5; }
.rate-normal { color:#4F46E5; background:#EEF2FF; }
.rate-cold { color:#DC2626; background:#FEF2F2; }

.mc-versus { display:flex; align-items:center; justify-content:center; gap:14px; margin-bottom:12px; }
.mc-team { font-size:17px; font-weight:700; color:var(--text); }
.mc-vs-divider { font-size:12px; font-weight:600; color:var(--muted); }
@media (max-width:767px) { .mc-team { font-size:16px; } }

.mc-prediction { text-align:center; margin-bottom:10px; }
.mc-pred-items { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
.mc-pred-item { font-size:14px; font-weight:600; color:#B45309; background:#FFFBEB; padding:6px 14px; border-radius:6px; border:1px solid #FDE68A; }

.mc-summary { padding:12px 14px; background:var(--bg); border-radius:6px; }
.mc-summary-text { font-size:14px; color:var(--text-secondary); line-height:1.6; white-space:pre-line; }

.mc-locked { text-align:center; padding:8px 0; }
.mc-locked-text { font-size:14px; color:var(--muted); }
.mc-locked.mc-member { padding:12px 0; cursor:pointer; }
.mc-locked.mc-member .mc-locked-text { color:var(--primary); font-weight:600; }
.mc-locked.mc-pending .mc-locked-text { color:#10B981; }
.mc-lock-icon { width:16px; height:16px; color:var(--primary); vertical-align:middle; margin-right:4px; }

.mc-pending-bar { text-align:center; margin-top:14px; padding:10px; background:#ECFDF5; border-radius:8px; font-size:14px; color:#059669; }
.mc-pending-hint { text-align:center; margin-top:10px; font-size:13px; color:#10B981; }

.mc-upgrade-hint { display:flex; align-items:center; justify-content:center; gap:6px; padding:12px 0 2px; border-top:1px solid var(--border-light); margin-top:6px; font-size:14px; color:var(--primary); font-weight:600; cursor:pointer; }
.mc-hint-lock { width:14px; height:14px; flex-shrink:0; }

.parlay-section { margin-top:14px; padding:14px; background:#FFFDF5; border-radius:8px; border:1px solid #FDE68A; }
.parlay-section-title { font-size:13px; font-weight:700; color:#B45309; margin-bottom:8px; text-align:center; }
.parlay-card { padding:8px 12px; background:#fff; border-radius:6px; border:1px solid #FDE68A; margin-bottom:6px; }
.parlay-card:last-child { margin-bottom:0; }
.parlay-card-num { font-size:12px; color:var(--muted); margin-right:6px; }
.parlay-bets { font-size:15px; font-weight:500; color:var(--text); }

.parlay-locked { padding:14px; background:#FFFDF5; border-radius:8px; border:1px solid #FDE68A; cursor:pointer; }
.parlay-locked-header { text-align:center; }
.parlay-locked-title { font-size:13px; font-weight:600; color:#B45309; }
.parlay-locked-badge { margin-top:4px; }
.parlay-locked-badge span { font-size:11px; color:var(--primary); font-weight:600; }
</style>
