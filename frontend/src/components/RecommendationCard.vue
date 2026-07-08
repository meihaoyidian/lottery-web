<template>
  <div class="card" :class="{ 'key-match-card': hasKeyMatch }">
    <!-- 角标 -->
    <div v-if="totalMatchesCount >= 2 && !reviewMode" class="corner corner-multi">
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
            <div v-else-if="match.is_trial_locked" class="mc-locked mc-trial-locked">
              <span class="mc-locked-text">—</span>
            </div>
            <div v-else-if="isAnalysisPending" class="mc-locked mc-pending">
              <span class="mc-locked-text">模型数据实时更新中</span>
            </div>
            <div v-else class="mc-locked">
              <span class="mc-locked-text">—</span>
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
        <div v-else-if="parlay && parlay.length > 0 && blurParlay" class="parlay-section parlay-locked">
          <div class="parlay-locked-header">
            <span class="parlay-locked-title">组合方案</span>
            <div class="parlay-locked-badge"><span>{{ isAnalysisPending ? '即将更新' : '—' }}</span></div>
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
    <div v-if="!showAnalysis && !isAnalysisPending && !isFirst" class="mc-upgrade-hint">
      <span>—</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  recommendation: { type: Object, required: true },
  showAnalysis: { type: Boolean, default: false },
  isAnalysisPending: { type: Boolean, default: false },
  reviewMode: { type: Boolean, default: false },
  isTrial: { type: Boolean, default: false },
  isFirst: { type: Boolean, default: false }
})

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
const hasTrialLocked = computed(() => singleMatches.value.some(m => m.is_trial_locked))

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
/* ========== CARD ========== */
.card {
  background: var(--surface); border-radius: var(--radius-lg); padding: 24px; margin-bottom: 16px;
  border: 1px solid var(--border); position: relative; overflow: hidden;
  box-shadow: var(--shadow);
}
.key-match-card {
  border: 2px solid #FBBF24; box-shadow: 0 4px 16px rgba(245,158,11,0.10);
}
@media (max-width: 767px) {
  .card { padding: 18px 16px; border-radius: var(--radius); }
}

/* ========== CORNER ========== */
.corner {
  position: absolute; top: 0; left: 50%; transform: translateX(-50%);
  padding: 6px 24px; border-radius: 0 0 12px 12px; z-index: 1;
  font-size: 12px; font-weight: 600; color: #fff; letter-spacing: 0.5px;
}
.corner-multi { background: linear-gradient(135deg, #6366F1, #7C3AED); }
.corner-key { background: linear-gradient(135deg, #f59e0b, #e8870a); }

/* ========== HEADER ========== */
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.sport-badge { display: flex; align-items: center; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: 500; }
.sport-badge.football { background: #e0f7fa; color: #0288d1; }
.sport-badge.basketball { background: #fff3e0; color: #e65100; }

.card-title-section { margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border-light); }
.card-title { font-size: 17px; font-weight: 700; color: var(--text); line-height: 1.5; display: block; }

/* ========== ANALYSIS ========== */
.analysis-section { background: var(--bg); border-radius: var(--radius); padding: 20px; border: 1px solid var(--border); }
.single-matches { display: flex; flex-direction: column; gap: 14px; }

/* ========== MATCH CARD ========== */
.match-card {
  background: #fff; border-radius: var(--radius); padding: 20px 22px;
  border: 1px solid var(--border); position: relative;
  box-shadow: var(--shadow-sm);
}
@media (max-width: 767px) {
  .match-card { padding: 16px 14px; }
}
.match-card::before {
  content: ''; position: absolute; left: 0; top: 16px; bottom: 16px;
  width: 6px; border-radius: 0 3px 3px 0;
}
.match-card.mc-key { border: 2px solid #fde68a; background: #fffdf5; box-shadow: 0 4px 12px rgba(245,158,11,0.12); }
.match-card.mc-key::before { background: #f59e0b; }
.match-card.mc-featured { border: 2px solid #DDD6FE; background: #FAFAFE; box-shadow: 0 4px 12px rgba(99,102,241,0.08); }
.match-card.mc-featured::before { background: #8B5CF6; }
.match-card.mc-confirmed { padding-top: 44px; }

.mc-confirmed-badge {
  position: absolute; top: 0; left: 0;
  background: linear-gradient(135deg, #0d9488, #0f766e); color: #fff;
  font-size: 11px; font-weight: 600; padding: 6px 20px;
  border-radius: 0 0 10px 0; z-index: 2;
}

/* ========== MC HEADER ========== */
.mc-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 18px; min-height: 36px; }
.mc-header-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }
.mc-id { font-size: 11px; font-weight: 500; color: #94a3b8; margin-right: 6px; }

.mc-tag { font-size: 10px; font-weight: 600; padding: 4px 12px; border-radius: 6px; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.mc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; display: inline-block; }
.mc-tag-key { color: #e8870a; background: #fffdf5; border: 1px solid #fde68a; }
.mc-tag-key .mc-dot { background: #f59e0b; }
.mc-tag-featured { color: #6D28D9; background: #FAFAFE; border: 1px solid #DDD6FE; }
.mc-tag-featured .mc-dot { background: #8B5CF6; }
.mc-tag-public { color: #059669; background: #ECFDF5; border: 1px solid #a7f3d0; }
.mc-tag-upset { color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }
.mc-tag-upset .mc-dot { background: #ef4444; }

/* Confidence tag */
.mc-tag-confidence { margin-left: 8px; }
.mc-tag-confidence.rate-high { color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; }
.mc-tag-confidence.rate-high .mc-dot { background: #10b981; }
.mc-tag-confidence.rate-normal { color: #4F46E5; background: #EEF2FF; border: 1px solid #C7D2FE; }
.mc-tag-confidence.rate-normal .mc-dot { background: #6366F1; }
.mc-tag-confidence.rate-cold { color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; }
.mc-tag-confidence.rate-cold .mc-dot { background: #ef4444; }

/* Result tag */
.mc-result-hit {
  color: #fff; font-size: 12px; font-weight: 800;
  padding: 4px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 3px 10px rgba(5,150,105,0.35);
  transform: rotate(-3deg); letter-spacing: 1px; position: relative;
}
.mc-result-hit::after {
  content: ''; position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px;
  border: 2px dashed rgba(255,255,255,0.3); border-radius: 8px; pointer-events: none;
}
.mc-result-push {
  color: #fff; font-size: 12px; font-weight: 800;
  padding: 4px 12px; border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  box-shadow: 0 3px 10px rgba(124,58,237,0.3);
  transform: rotate(-3deg); letter-spacing: 1px; position: relative;
}
.mc-result-push::after {
  content: ''; position: absolute; top: 4px; left: 4px; right: 4px; bottom: 4px;
  border: 2px dashed rgba(255,255,255,0.25); border-radius: 8px; pointer-events: none;
}
.mc-result-miss {
  color: #94a3b8; font-size: 11px; font-weight: 500;
  padding: 4px 12px; border-radius: 8px;
  background: #f1f5f9; border: 1px dashed #d1d5db;
  transform: rotate(-3deg); letter-spacing: 1px; opacity: 0.7;
}

/* ========== VERSUS ========== */
.mc-versus { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 18px; }
.mc-team { flex: 1; text-align: center; font-size: 18px; font-weight: 800; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.mc-vs-divider { width: 56px; height: 40px; display: flex; align-items: center; justify-content: center; background: var(--border-light); border-radius: 10px; flex-shrink: 0; }
.mc-vs-divider span { font-size: 11px; font-weight: 700; color: var(--muted); }
@media (max-width: 767px) {
  .mc-team { font-size: 16px; }
}

/* ========== PREDICTION ========== */
.mc-prediction { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 12px 0; margin-bottom: 14px; }
.mc-pred-items { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }
.mc-pred-item {
  font-size: 14px; font-weight: 700;
  color: #B45309; background: #FFFBEB;
  padding: 10px 20px; border-radius: 10px;
  border: 1px solid #FDE68A;
}

/* ========== SUMMARY ========== */
.mc-summary {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 16px 18px; background: var(--bg);
  border-radius: var(--radius); border-left: 4px solid var(--primary);
}
.mc-summary-icon { font-size: 15px; flex-shrink: 0; margin-top: 2px; }
.mc-summary-text { font-size: 13px; color: #475569; line-height: 1.7; }

/* ========== LOCKED ========== */
.mc-locked { display: flex; align-items: center; justify-content: center; padding: 10px 0 2px; }
.mc-locked-text { font-size: 14px; color: #cbd5e1; font-weight: 500; }
.mc-locked.mc-pending .mc-locked-text { color: #10b981; font-weight: 600; }
.mc-locked.mc-trial-locked .mc-locked-text { color: #f59e0b; font-weight: 600; }

.mc-pending-bar {
  display: flex; align-items: center; justify-content: center;
  margin-top: 20px; padding: 14px 24px;
  background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
  border: 1px solid #a7f3d0; border-radius: 12px;
  font-size: 14px; color: #059669; font-weight: 600;
}
.mc-pending-hint { margin-top: 16px; text-align: center; font-size: 12px; color: #10b981; font-weight: 500; }

.mc-upgrade-hint {
  display: flex; align-items: center; justify-content: center;
  padding: 14px 0 4px; border-top: 1px solid var(--border-light); margin-top: 8px;
  font-size: 18px; color: var(--muted);
}

/* ========== PARLAY ========== */
.parlay-section {
  margin-top: 20px; padding: 16px;
  background: #fffdf5; border-radius: 12px;
  border: 1px solid #fde68a; border-left: 5px solid #f59e0b;
}
.parlay-section-title { font-size: 12px; font-weight: 700; color: #d97706; margin-bottom: 10px; text-align: center; }
.parlay-card { background: #fff; border-radius: 10px; border: 1px solid #eef0f5; margin-bottom: 8px; padding: 14px 16px; }
.parlay-card:last-child { margin-bottom: 0; }
.parlay-card-num { font-size: 11px; font-weight: 600; color: #94a3b8; margin-right: 8px; }
.parlay-bets { font-size: 15px; font-weight: 500; color: #1e293b; line-height: 1.6; text-align: center; display: block; }

.parlay-locked {
  background: linear-gradient(135deg, #fffdf5, #fffbeb);
  border: 1px solid #fde68a; border-left: 5px solid #f59e0b;
  border-radius: 12px; padding: 16px;
}
.parlay-locked-header { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.parlay-locked-title { font-size: 14px; font-weight: 600; color: #b45309; }
.parlay-locked-badge { padding: 4px 12px; background: #fef3c7; border-radius: 6px; border: 1px solid #fde68a; }
.parlay-locked-badge span { font-size: 11px; font-weight: 600; color: #b45309; }
</style>
