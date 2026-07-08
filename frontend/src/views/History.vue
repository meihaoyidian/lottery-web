<template>
  <div class="page">
    <Loading v-if="loading" />
    <div v-else class="container">
      <template v-if="!isPaidUser">
        <div v-if="statistics" class="stat-hero">
          <div class="hero-main">
            <div class="hero-left"><span class="hero-eyebrow">整体好评率</span><div class="hero-meta-row"><span>总场次 <em>{{ statistics.total_count }}</em></span><span class="hero-meta-dot">·</span><span>好评 <em class="em-hit">{{ statistics.accurate_count }}</em></span></div></div>
            <div class="hero-right"><svg class="hero-gauge" viewBox="0 0 120 120"><defs><linearGradient id="hrGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#6366F1"/><stop offset="100%" stop-color="#8B5CF6"/></linearGradient><filter id="hrGlow"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g v-for="i in 36" :key="i" :transform="'rotate('+((i-1)*10)+' 60 60)'"><line x1="60" y1="14" x2="60" y2="18" stroke="#E2E8F0" stroke-width="1.5" :opacity="i%3===1?0.6:0.25"/></g><circle cx="60" cy="60" r="42" fill="none" stroke="#E2E8F0" stroke-width="5"/><circle cx="60" cy="60" r="42" fill="none" stroke="url(#hrGrad)" stroke-width="5" stroke-linecap="round" filter="url(#hrGlow)" :stroke-dasharray="ringDash" transform="rotate(-90 60 60)"/></svg><div class="hero-gauge-text"><span class="gauge-num">{{ ceil(statistics.accuracy_rate) }}<small>%</small></span><span class="gauge-label">好评率</span></div></div>
          </div>
          <div v-if="monthlyStats.length>0" class="hero-trend"><div class="trend-head"><span class="trend-title">历史好评率趋势</span><span class="trend-badge">持续稳定</span></div><div class="trend-scroll"><div v-for="m in monthlyStats" :key="m.month" class="trend-card"><span class="tc-month">{{ Number(m.month.split('-')[1]) }}月</span><span class="tc-rate">{{ ceil(m.hit_rate) }}%</span><div class="tc-bar-track"><div class="tc-bar" :style="{width:ceil(m.hit_rate)+'%'}"></div></div><span class="tc-count">{{ m.hit_count }}/{{ m.total_count }} 场</span></div></div></div>
        </div>
        <div v-if="highlights.length>0" class="section-card"><h3 class="section-title">近期好评场次</h3><div class="highlight-list"><div v-for="item in highlights" :key="item.match_id" class="hl-item"><div class="hl-left"><span class="hl-check">✓</span><span :class="['hl-tag',item.is_key_match?'tag-km':'tag-ft']">{{ item.is_key_match?'重心':'精选' }}</span><span class="hl-teams">{{ item.home_team }} vs {{ item.away_team }}</span></div><div class="hl-preds"><span v-if="item.total_points" class="hl-pred">{{ item.total_points }}</span><span v-if="item.handicap" class="hl-pred">{{ item.handicap }}</span></div></div></div></div>
      </template>
      <template v-else>
        <div v-if="statistics" class="stat-hero">
          <div class="hero-main"><div class="hero-left"><span class="hero-eyebrow">整体好评率</span><div class="hero-meta-row"><span>总场次 <em>{{ statistics.total_count }}</em></span><span class="hero-meta-dot">·</span><span>好评 <em class="em-hit">{{ statistics.accurate_count }}</em></span></div></div>
            <div class="hero-right"><svg class="hero-gauge" viewBox="0 0 120 120"><defs><linearGradient id="hrGrad2" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#6366F1"/><stop offset="100%" stop-color="#8B5CF6"/></linearGradient><filter id="hrGlow2"><feGaussianBlur stdDeviation="2" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><g v-for="i in 36" :key="i" :transform="'rotate('+((i-1)*10)+' 60 60)'"><line x1="60" y1="14" x2="60" y2="18" stroke="#E2E8F0" stroke-width="1.5" :opacity="i%3===1?0.6:0.25"/></g><circle cx="60" cy="60" r="42" fill="none" stroke="#E2E8F0" stroke-width="5"/><circle cx="60" cy="60" r="42" fill="none" stroke="url(#hrGrad2)" stroke-width="5" stroke-linecap="round" filter="url(#hrGlow2)" :stroke-dasharray="ringDash" transform="rotate(-90 60 60)"/></svg><div class="hero-gauge-text"><span class="gauge-num">{{ ceil(statistics.accuracy_rate) }}<small>%</small></span><span class="gauge-label">好评率</span></div></div>
          </div>
          <div class="hero-grid">
            <div v-if="statistics.football_stats" class="hsc"><div class="hsc-head"><span class="hsc-sport">足球</span><span class="hsc-tag">整体</span></div><span class="hsc-rate">{{ ceil(statistics.football_stats.rate) }}%</span><span class="hsc-count">{{ statistics.football_stats.accurate }}/{{ statistics.football_stats.total }}</span></div>
            <div v-if="statistics.key_match_stats?.football_total>0" class="hsc hsc-gold"><div class="hsc-head"><span class="hsc-sport">足球</span><span class="hsc-tag">重心</span></div><span class="hsc-rate">{{ ceil(statistics.key_match_stats.football_rate) }}%</span><span class="hsc-count">{{ statistics.key_match_stats.football_accurate }}/{{ statistics.key_match_stats.football_total }}</span></div>
            <div v-if="statistics.basketball_stats" class="hsc"><div class="hsc-head"><span class="hsc-sport">篮球</span><span class="hsc-tag">整体</span></div><span class="hsc-rate">{{ ceil(statistics.basketball_stats.rate) }}%</span><span class="hsc-count">{{ statistics.basketball_stats.accurate }}/{{ statistics.basketball_stats.total }}</span></div>
            <div v-if="statistics.key_match_stats?.basketball_total>0" class="hsc hsc-gold"><div class="hsc-head"><span class="hsc-sport">篮球</span><span class="hsc-tag">重心</span></div><span class="hsc-rate">{{ ceil(statistics.key_match_stats.basketball_rate) }}%</span><span class="hsc-count">{{ statistics.key_match_stats.basketball_accurate }}/{{ statistics.key_match_stats.basketball_total }}</span></div>
          </div>
          <div v-if="monthlyStats.length>0" class="hero-trend"><div class="trend-head"><span class="trend-title">历史好评率趋势</span></div><div class="trend-scroll"><div v-for="m in monthlyStats" :key="m.month" class="trend-card"><span class="tc-month">{{ Number(m.month.split('-')[1]) }}月</span><span class="tc-rate">{{ ceil(m.hit_rate) }}%</span><div class="tc-bar-track"><div class="tc-bar" :style="{width:ceil(m.hit_rate)+'%'}"></div></div><span class="tc-count">{{ m.hit_count }}/{{ m.total_count }} 场</span></div></div></div>
        </div>
        <div class="filter-row"><button :class="['filter-btn',{on:sportIdx===0}]" @click="onFilter(0)">全部</button><button :class="['filter-btn',{on:sportIdx===1}]" @click="onFilter(1)">足球</button><button :class="['filter-btn',{on:sportIdx===2}]" @click="onFilter(2)">篮球</button></div>
        <div class="history-list">
          <div v-for="item in historyList" :key="item.id" class="hist-card" :class="[item.hasKeyMatch?'hc-km':'',item.actual_outcome?.hit_status?'outcome-'+item.actual_outcome.hit_status:'']">
            <div v-if="item.hasKeyMatch" class="hc-km-badge">重心</div>
            <div class="hc-top"><span :class="['hc-sport','sport-'+item.prediction_type]">{{ item.prediction_type==='football'?'足球':'篮球' }}</span><span v-if="item.actual_outcome?.hit_status" class="hc-stamp" :class="'stamp-'+item.actual_outcome.hit_status">{{ item.actual_outcome.hit_status==='partial'&&item.actual_outcome.partial_detail?item.actual_outcome.partial_detail:resultLabel(item.actual_outcome.hit_status) }}</span></div>
            <div class="hc-title-row" @click="toggleExpand(item.id)"><span class="hc-title">{{ item.title }}</span><span class="hc-arrow">{{ expanded[item.id]?'▲':'▼' }}</span></div>
            <div v-if="expanded[item.id]" class="hc-detail">
              <div v-if="item.prediction_data?.single_matches?.length" class="hc-matches"><div v-for="m in item.prediction_data.single_matches" :key="m.match_id" class="hc-match" :class="[m.is_key_match?'hcm-km':'',m.is_featured?'hcm-ft':'',m.hit_status==='hit'?'hcm-hit':m.hit_status==='miss'?'hcm-miss':'']"><div class="hcm-head"><span class="hcm-id">{{ m.match_id }}</span><span v-if="m.is_key_match" class="hcm-tag tag-km">重心</span><span v-else-if="m.is_featured" class="hcm-tag tag-ft">精选</span><span v-if="m.is_upset_warning" class="hcm-tag tag-up">冷门预警</span><span v-if="m.hit_status&&m.hit_status!=='pending'" class="hcm-result-tag" :class="'hcmr-'+m.hit_status">{{ m.hit_status==='hit'?'好评':m.hit_status==='push'?'走水':'未中' }}</span></div><div class="hcm-vs"><span class="hcm-team">{{ m.home_team }}</span><span class="hcm-vs-text">vs</span><span class="hcm-team">{{ m.away_team }}</span></div><div v-if="m.total_points||m.handicap" class="hcm-preds"><span v-if="m.total_points" class="hcm-pred">{{ m.total_points }}</span><span v-if="m.handicap" class="hcm-pred">{{ m.handicap }}</span></div><p v-if="m.prediction_basis" class="hcm-basis">{{ m.prediction_basis }}</p></div></div>
              <div v-if="item.prediction_data?.parlays?.length" class="hc-parlays"><span class="hc-parlays-title">组合方案</span><div v-for="(p,i) in item.prediction_data.parlays" :key="i" class="hc-parlay"><span v-if="item.prediction_data.parlays.length>1" class="hc-parlay-num">#{{ i+1 }}</span><span class="hc-parlay-bets">{{ p.bet_types?.join(' · ') }}</span></div></div>
            </div>
            <div v-if="item.actual_outcome?.notes" class="hc-notes"><span class="hc-notes-label">总结说明</span><p class="hc-notes-text">{{ item.actual_outcome.notes }}</p></div>
          </div>
          <div v-if="historyList.length===0" class="empty-state"><span class="empty-icon"></span><span class="empty-title">暂无历史记录</span><span class="empty-desc">已完成的推荐会在这里显示</span></div>
        </div>
        <div v-if="hasMoreHistory" class="load-more-wrap"><button class="load-more-btn" @click="loadMoreHistory">加载更多</button></div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import Loading from '../components/Loading.vue'

const auth = useAuthStore()
const loading = ref(true), statistics = ref(null), monthlyStats = ref([]), highlights = ref([]), historyList = ref([])
const expanded = ref({}), hasMoreHistory = ref(false), pageNum = ref(1), sportIdx = ref(0)
const sportTypes = ['', 'football', 'basketball']
const isPaidUser = computed(() => auth.isPaidUser())
const ceil = (n) => n != null ? Math.ceil(Number(n)) : 0
const ringDash = computed(() => { const p = Math.min(statistics.value?.accuracy_rate||0,100), l = 2*Math.PI*42; return `${(p/100)*l} ${l}` })
function resultLabel(s) { const m = { hit:'好评', push:'走水', partial:'部分', miss:'蓄力' }; return m[s]||s }
function toggleExpand(id) { expanded.value[id] = !expanded.value[id] }
function onFilter(idx) { if (sportIdx.value===idx) return; sportIdx.value=idx; loadData() }

async function loadData() {
  loading.value=true
  try {
    const s = sportTypes[sportIdx.value], p = { page:1, page_size:20 }; if(s) p.prediction_type=s
    const [stats, monthly, hl, hist] = await Promise.all([
      api.getStatistics(s?{prediction_type:s}:undefined).catch(()=>null),
      api.getMonthlyStatistics(s?{prediction_type:s}:undefined).catch(()=>[]),
      api.getHighlights().catch(()=>[]),
      api.getHistory(p).catch(()=>null)
    ])
    statistics.value=stats; monthlyStats.value=monthly?.monthly_stats||[]; highlights.value=hl?.highlights||[]
    if(hist) { historyList.value=hist.items||[]; hasMoreHistory.value=hist.has_more }
  } catch(e) { console.error(e) } finally { loading.value=false }
}

async function loadMoreHistory() {
  const s = sportTypes[sportIdx.value], p = { page:pageNum.value+1, page_size:20 }; if(s) p.prediction_type=s
  const res = await api.getHistory(p); historyList.value=[...historyList.value,...(res.items||[])]; pageNum.value++; hasMoreHistory.value=res.has_more
}

onMounted(loadData)
</script>

<style scoped>
.container { max-width:1100px; margin:0 auto; padding:16px; }
@media (min-width:768px) { .container { padding:24px; } }

.stat-hero { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); box-shadow:var(--shadow); overflow:hidden; position:relative; }
.stat-hero::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg,var(--primary),#8B5CF6); }
.hero-main { display:flex; align-items:center; justify-content:space-between; padding:32px 28px 24px; }
.hero-left { display:flex; flex-direction:column; gap:6px; }
.hero-eyebrow { font-size:15px; font-weight:700; color:var(--text); }
.hero-meta-row { display:flex; align-items:baseline; gap:12px; font-size:15px; color:var(--text-secondary); margin-top:2px; }
.hero-meta-row em { font-size:24px; font-weight:800; color:var(--text); font-style:normal; }
.em-hit { color:var(--success)!important; }
.hero-meta-dot { color:#CBD5E1; font-size:14px; }
.hero-right { position:relative; width:120px; height:120px; flex-shrink:0; }
.hero-gauge { width:120px; height:120px; }
.hero-gauge-text { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.gauge-num { font-size:32px; font-weight:900; color:var(--text); line-height:1; letter-spacing:-0.03em; }
.gauge-num small { font-size:15px; font-weight:700; }
.gauge-label { font-size:10px; font-weight:600; color:var(--muted); margin-top:4px; letter-spacing:0.06em; }
.hero-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; padding:0 28px 24px; }
.hsc { display:flex; flex-direction:column; align-items:center; gap:4px; padding:18px 12px; background:#EEF2FF; border:1px solid #C7D2FE; border-radius:var(--radius); transition:transform 0.15s,box-shadow 0.15s; }
.hsc:hover { transform:translateY(-2px); box-shadow:var(--shadow); }
.hsc-head { display:flex; align-items:center; gap:6px; }
.hsc-sport { font-size:13px; font-weight:600; color:#4338CA; }
.hsc-tag { font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; background:#C7D2FE; color:#4338CA; }
.hsc-rate { font-size:26px; font-weight:800; color:var(--text); line-height:1.2; }
.hsc-count { font-size:12px; color:var(--text-secondary); font-weight:500; }
.hsc-gold { border-color:#FDE68A; background:#FFFDF5; }
.hsc-gold .hsc-tag { background:#FEF3C7; color:#B45309; }
.hsc-gold .hsc-sport { color:#92400E; }
@media (min-width:768px) { .hero-grid { grid-template-columns:repeat(4,1fr); } }
.hero-trend { padding:20px 28px 6px; border-top:1px solid var(--border-light); }
.trend-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
.trend-title { font-size:15px; font-weight:700; color:var(--text); }
.trend-badge { font-size:12px; font-weight:600; color:var(--success); background:#ECFDF5; padding:4px 14px; border-radius:20px; }
.trend-scroll { display:flex; gap:12px; overflow-x:auto; padding-bottom:16px; -webkit-overflow-scrolling:touch; }
.trend-scroll::-webkit-scrollbar { height:4px; } .trend-scroll::-webkit-scrollbar-thumb { background:#E2E8F0; border-radius:2px; }
.trend-card { display:flex; flex-direction:column; align-items:center; gap:8px; min-width:92px; padding:14px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); flex-shrink:0; box-shadow:var(--shadow-sm); }
.tc-month { font-size:13px; font-weight:600; color:var(--text-secondary); }
.tc-rate { font-size:22px; font-weight:800; color:var(--text); line-height:1.1; }
.tc-bar-track { width:100%; height:4px; background:var(--border); border-radius:2px; overflow:hidden; }
.tc-bar { height:100%; border-radius:2px; background:linear-gradient(90deg,#6366F1,#8B5CF6); transition:width 0.5s ease; }
.tc-count { font-size:12px; color:var(--text-secondary); font-weight:500; white-space:nowrap; }
.section-card { margin-top:14px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:24px 28px; box-shadow:var(--shadow-sm); }
.section-title { font-size:15px; font-weight:700; color:var(--text); margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border-light); }
.highlight-list { display:flex; flex-direction:column; }
.hl-item { display:flex; align-items:center; justify-content:space-between; padding:14px 0; border-bottom:1px solid var(--border-light); }
.hl-item:last-child { border-bottom:none; }
.hl-left { display:flex; align-items:center; gap:12px; flex:1; min-width:0; }
.hl-check { width:32px; height:32px; border-radius:50%; background:#ECFDF5; color:var(--success); font-size:12px; font-weight:800; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.hl-tag { font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; flex-shrink:0; }
.tag-km { color:#B45309; background:#FFFDF5; border:1px solid #FDE68A; }
.tag-ft { color:#6D28D9; background:#FAFAFE; border:1px solid #DDD6FE; }
.hl-teams { font-size:15px; font-weight:600; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.hl-preds { display:flex; gap:8px; flex-shrink:0; margin-left:16px; }
.hl-pred { font-size:12px; font-weight:600; color:var(--primary); background:var(--primary-light); border:1px solid #C7D2FE; padding:4px 12px; border-radius:6px; }
.filter-row { display:flex; justify-content:center; gap:10px; margin:16px 0 18px; }
.filter-btn { padding:10px 24px; border-radius:24px; min-height:42px; background:var(--surface); border:1px solid var(--border); font-size:14px; font-weight:500; color:var(--text-secondary); transition:all 0.2s; }
.filter-btn:hover { border-color:var(--primary); color:var(--primary); }
.filter-btn.on { background:var(--primary); color:#fff; border-color:var(--primary); font-weight:600; box-shadow:var(--shadow); }
.history-list { padding-bottom:24px; }
.hist-card { background:var(--surface); border-radius:var(--radius-lg); padding:22px 24px; margin-bottom:14px; border:1px solid var(--border); box-shadow:var(--shadow-sm); position:relative; overflow:hidden; transition:box-shadow 0.15s; }
.hist-card:hover { box-shadow:var(--shadow); }
.hist-card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; }
.hist-card.outcome-hit { border-color:#A7F3D0; } .hist-card.outcome-hit::before { background:var(--success); }
.hist-card.outcome-push { border-color:#DDD6FE; } .hist-card.outcome-push::before { background:#8B5CF6; }
.hist-card.outcome-partial { border-color:#FDE68A; } .hist-card.outcome-partial::before { background:var(--warning); }
.hist-card.outcome-miss { opacity:0.78; } .hist-card.outcome-miss::before { background:#CBD5E1; }
.hist-card.hc-km { border-color:#FDE68A; }
.hc-km-badge { position:absolute; top:0; left:50%; transform:translateX(-50%); background:linear-gradient(135deg,#F59E0B,#E8870A); padding:4px 18px; border-radius:0 0 8px 8px; z-index:1; font-size:11px; font-weight:600; color:#fff; }
.hc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:12px; }
.hc-sport { display:inline-flex; padding:5px 14px; border-radius:20px; font-size:12px; font-weight:600; }
.sport-football { background:#E0F7FA; color:#0288D1; } .sport-basketball { background:#FFF3E0; color:#E65100; }
.hc-stamp { display:inline-flex; align-items:center; padding:5px 18px; border-radius:40px; font-size:13px; font-weight:800; letter-spacing:0.06em; position:relative; }
.hc-stamp::after { content:''; position:absolute; inset:3px; border-radius:38px; border:1.5px dashed rgba(255,255,255,0.35); pointer-events:none; }
.stamp-hit { background:linear-gradient(135deg,#10B981,#059669); color:#fff; box-shadow:0 3px 12px rgba(5,150,105,0.3),inset 0 1px 0 rgba(255,255,255,0.2); }
.stamp-push { background:linear-gradient(135deg,#8B5CF6,#7C3AED); color:#fff; box-shadow:0 3px 12px rgba(124,58,237,0.3),inset 0 1px 0 rgba(255,255,255,0.2); }
.stamp-partial { background:linear-gradient(135deg,#F59E0B,#D97706); color:#fff; box-shadow:0 3px 12px rgba(245,158,11,0.3),inset 0 1px 0 rgba(255,255,255,0.2); }
.stamp-miss { background:#F1F5F9; color:#64748B; box-shadow:inset 0 0 0 1.5px solid #CBD5E1; }
.stamp-miss::after { border-color:rgba(100,116,139,0.2); }
.hc-title-row { display:flex; align-items:center; justify-content:space-between; cursor:pointer; }
.hc-title { font-size:15px; font-weight:700; color:var(--text); line-height:1.5; flex:1; }
.hc-arrow { font-size:12px; color:var(--muted); margin-left:16px; flex-shrink:0; }
.hc-detail { margin-top:16px; padding-top:16px; border-top:1px solid var(--border-light); }
.hc-matches { display:flex; flex-direction:column; gap:12px; }
.hc-match { padding:14px 16px; background:var(--bg); border-radius:var(--radius-sm); border:1px solid var(--border-light); }
.hc-match.hcm-hit { border-left:3px solid var(--success); }
.hc-match.hcm-miss { border-left:3px solid #CBD5E1; opacity:0.7; }
.hcm-head { display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.hcm-id { font-size:11px; font-weight:600; color:var(--muted); }
.hcm-tag { font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; }
.hcm-result-tag { font-size:10px; font-weight:700; padding:2px 10px; border-radius:10px; color:#fff; margin-left:auto; }
.hcmr-hit { background:linear-gradient(135deg,#10B981,#059669); }
.hcmr-push { background:linear-gradient(135deg,#8B5CF6,#7C3AED); }
.hcmr-miss { background:#F1F5F9; color:#94A3B8; border:1px solid #E2E8F0; }
.hcm-vs { display:flex; align-items:center; justify-content:center; gap:14px; margin-bottom:10px; }
.hcm-team { font-size:16px; font-weight:700; color:var(--text); }
.hcm-vs-text { font-size:12px; font-weight:600; color:var(--muted); }
.hcm-preds { display:flex; gap:10px; justify-content:center; margin-bottom:10px; }
.hcm-pred { font-size:13px; font-weight:700; color:#B45309; background:#FFFBEB; border:1px solid #FDE68A; padding:6px 16px; border-radius:8px; }
.hcm-basis { font-size:13px; color:var(--text-secondary); line-height:1.7; text-align:center; }
.hc-parlays { margin-top:14px; padding:14px 16px; background:#FFFDF5; border-radius:var(--radius-sm); border:1px solid #FDE68A; }
.hc-parlays-title { font-size:12px; font-weight:700; color:#B45309; display:block; text-align:center; margin-bottom:10px; }
.hc-parlay { text-align:center; padding:8px 0; }
.hc-parlay-num { font-size:11px; font-weight:600; color:var(--muted); margin-right:8px; }
.hc-parlay-bets { font-size:14px; font-weight:600; color:var(--text); }
.hc-notes { margin-top:14px; padding:14px 16px; background:#FFFBEB; border-radius:var(--radius-sm); border:1px solid #FDE68A; }
.hc-notes-label { font-size:13px; font-weight:600; color:#B45309; display:block; margin-bottom:6px; }
.hc-notes-text { font-size:14px; color:var(--text-secondary); line-height:1.7; }
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:40px; display:block; margin-bottom:14px; }
.empty-title { font-size:16px; font-weight:600; color:var(--text-secondary); }
.empty-desc { font-size:14px; color:var(--muted); margin-top:8px; display:block; }
.load-more-wrap { text-align:center; padding:8px 0 32px; }
.load-more-btn { padding:14px 48px; background:var(--surface); color:var(--text-secondary); font-size:15px; border-radius:var(--radius); border:1px solid var(--border); box-shadow:var(--shadow-sm); }
@media (max-width:767px) {
  .hero-main { padding:24px 18px 20px; } .hero-eyebrow { font-size:14px; }
  .hero-meta-row { font-size:14px; } .hero-meta-row em { font-size:20px; }
  .hero-right { width:100px; height:100px; } .hero-gauge { width:100px; height:100px; }
  .gauge-num { font-size:26px; } .gauge-num small { font-size:12px; }
  .hero-grid { gap:8px; padding:0 18px 20px; } .hsc { padding:14px 8px; } .hsc-rate { font-size:22px; }
  .hero-trend { padding:16px 18px 6px; } .trend-card { min-width:84px; padding:12px 10px; } .tc-rate { font-size:20px; }
  .hist-card { padding:18px 16px; } .hc-title { font-size:14px; }
  .hc-stamp { padding:4px 14px; font-size:12px; } .hc-match { padding:12px 12px; } .hcm-team { font-size:14px; }
  .section-card { padding:20px 18px; } .filter-btn { padding:8px 20px; font-size:13px; min-height:38px; }
}
</style>
