<template>
  <div class="page">
    <div class="container">
      <div class="top-bar">
        <div><button class="back-btn" @click="$router.push('/profile')">← 返回</button><h2>推荐管理</h2><span class="hint">管理所有推荐内容</span></div>
        <button class="create-btn" @click="$router.push('/admin/recommendations/create')">+ 创建</button>
      </div>

      <div class="filter-row">
        <button v-for="(f,i) in filters" :key="f.value" :class="['fbtn', { on: fi === i }]" @click="onFilter(i)">{{ f.name }}</button>
      </div>

      <Loading v-if="loading && !recs.length" />
      <div v-else class="list">
        <div v-for="r in recs" :key="r.id" class="card" :class="cardClass(r)">
          <!-- badges -->
          <div class="badges" v-if="r.is_confirmed || r.hasKeyMatch || r.hasFeatured">
            <span v-if="r.is_confirmed" class="bdg bdg-ok">已确认</span>
            <span v-if="r.hasKeyMatch" class="bdg bdg-km">重心</span>
            <span v-if="r.hasFeatured" class="bdg bdg-ft">精选</span>
          </div>
          <!-- header -->
          <div class="chd">
            <span :class="['sport', 'sp-'+r.prediction_type]">{{ r.prediction_type === 'football' ? '足球' : '篮球' }}</span>
            <span :class="['stag', 'st-'+r.status]">{{ statusMap[r.status] || r.status }}</span>
            <span class="time">{{ fmt(r.created_at) }}</span>
            <span v-if="r.actual_outcome?.hit_status" :class="['otag', 'ot-'+r.actual_outcome.hit_status]">
              {{ outcomeLabel(r.actual_outcome.hit_status) }}
            </span>
          </div>
          <div class="title">{{ r.title }}</div>

          <!-- 场次预览 -->
          <div v-if="r.prediction_data?.single_matches?.length" class="preview">
            <div class="pv-label">单场</div>
            <div v-for="(m, mi) in r.prediction_data.single_matches" :key="mi" class="match-row">
              <div class="mr-top">
                <span class="mr-id">{{ m.match_id }}</span>
                <span v-if="m.is_key_match" class="mr-tag mr-km">重心</span>
                <span v-if="m.is_featured" class="mr-tag mr-ft">精选</span>
                <button class="mr-toggle" :class="msClass(m.hit_status)" @click="toggleMatch(r, mi)">{{ msLabel(m.hit_status) }}</button>
              </div>
              <span class="mr-vs">{{ m.home_team }} vs {{ m.away_team }}</span>
              <div v-if="m.total_points || m.handicap" class="mr-preds">
                <span v-if="m.total_points" class="mr-pred">{{ m.total_points }}</span>
                <span v-if="m.handicap" class="mr-pred">{{ m.handicap }}</span>
              </div>
              <div v-if="m.prediction_basis" class="mr-basis">
                <span class="mr-basis-text">{{ m.prediction_basis }}</span>
              </div>
            </div>
          </div>

          <!-- 组合 -->
          <div v-if="r.prediction_data?.parlays?.length" class="preview">
            <div class="pv-label">组合</div>
            <div v-for="(p, pi) in r.prediction_data.parlays" :key="pi" class="parlay-row">
              {{ p.bet_types?.join(' × ') }}
            </div>
          </div>

          <!-- 操作 -->
          <div class="actions">
            <button class="act act-ok" @click="toggleConfirm(r)">{{ r.is_confirmed ? '取消确认' : '确认发布' }}</button>
            <div class="actions-row">
              <button class="act act-view" @click="openViewers(r)">浏览</button>
              <button class="act act-edit" @click="$router.push('/admin/recommendations/'+r.id+'/edit')">编辑</button>
              <button class="act act-result" @click="openResult(r)">{{ r.actual_outcome?.hit_status ? '改结果' : '标结果' }}</button>
              <button class="act act-del" @click="delRec(r)">删除</button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="hasMore" class="more" @click="loadMore">加载更多</div>
    </div>

    <!-- 结果弹窗 -->
    <div v-if="showResult" class="modal-mask" @click.self="showResult=false">
      <div class="modal">
        <h3>更新实际结果</h3>
        <p class="msub">{{ rf.title }}</p>
        <div class="mbtns">
          <button v-for="(o,i) in hitOpts" :key="o.value" :class="['mbtn', { on: hi===i }]" @click="hi=i;rf.hitStatus=o.value">{{ o.name }}</button>
        </div>
        <input v-if="rf.hitStatus==='partial'" v-model="rf.partialDetail" class="minp" placeholder="如 2✓1" />
        <textarea v-model="rf.notes" class="mta" placeholder="备注（可选）" rows="3"></textarea>
        <div class="mact">
          <button class="msubmit" :disabled="submitting" @click="submitResult">{{ submitting?'提交中...':'确认' }}</button>
          <button class="mcancel" @click="showResult=false">取消</button>
        </div>
      </div>
    </div>

    <!-- 浏览弹窗 -->
    <div v-if="showViewers" class="modal-mask" @click.self="showViewers=false">
      <div class="modal modal-xl">
        <div class="vw-head">
          <h3>浏览记录</h3>
          <p class="msub">{{ vTitle }}</p>
        </div>

        <!-- 汇总统计卡片 -->
        <div class="vw-stats">
          <div class="vw-stat">
            <span class="vw-stat-num">{{ vTotal }}</span>
            <span class="vw-stat-label">总浏览次数</span>
          </div>
          <div class="vw-stat vw-stat--user">
            <span class="vw-stat-num">{{ vUnique }}</span>
            <span class="vw-stat-label">登录用户</span>
          </div>
          <div class="vw-stat vw-stat--guest">
            <span class="vw-stat-num">{{ vGuest }}</span>
            <span class="vw-stat-label">游客浏览</span>
          </div>
          <div class="vw-stat vw-stat--avg">
            <span class="vw-stat-num">{{ vAvg }}</span>
            <span class="vw-stat-label">人均次数</span>
          </div>
        </div>

        <!-- 用户明细列表 -->
        <div class="vw-list">
          <div class="vw-list-head">
            <span class="vw-col-phone">用户</span>
            <span class="vw-col-role">身份</span>
            <span class="vw-col-count">次数</span>
            <span class="vw-col-first">首次浏览</span>
            <span class="vw-col-last">最近浏览</span>
          </div>
          <p v-if="!viewers.length" class="vw-empty">暂无登录用户浏览记录</p>
          <div v-for="(v,i) in viewers" :key="i" class="vw-row">
            <span class="vw-col-phone">
              <span class="vw-nickname">{{ v.user_nickname || v.user_phone }}</span>
              <span v-if="v.user_nickname" class="vw-phone-sub">{{ v.user_phone }}</span>
            </span>
            <span class="vw-col-role">
              <span :class="['vw-tag', v._roleClass]">{{ v._roleLabel }}</span>
            </span>
            <span class="vw-col-count">
              <span class="vw-count-badge">{{ v.view_count || 1 }}</span>
            </span>
            <span class="vw-col-first">{{ v._firstAt }}</span>
            <span class="vw-col-last">{{ v._viewedAt }}</span>
          </div>
        </div>

        <button class="mcancel vw-close" @click="showViewers=false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const recs = ref([]), loading = ref(false), hasMore = ref(false), page = ref(1), fi = ref(0)
const filters = [{ value:'all', name:'全部' },{ value:'football', name:'足球' },{ value:'basketball', name:'篮球' }]
const statusMap = { active:'进行中', completed:'已完成', inactive:'已删除' }
const hitOpts = [{ value:'hit', name:'好评' },{ value:'miss', name:'蓄力' },{ value:'partial', name:'部分' },{ value:'push', name:'走水' }]
const showResult = ref(false), showViewers = ref(false), submitting = ref(false), hi = ref(0)
const rf = reactive({ id:null, title:'', hitStatus:'hit', partialDetail:'', notes:'' })
const viewers = ref([]), vTitle = ref(''), vTotal = ref(0), vUnique = ref(0), vGuest = ref(0)
const vAvg = ref(0)

function cardClass(r) { return [r.is_confirmed?'is-ok':'',r.hasKeyMatch?'is-km':'',r.actual_outcome?.hit_status?'ot-'+r.actual_outcome.hit_status:''] }
function outcomeLabel(s) { return { hit:'好评', miss:'蓄力', partial:'部分好评', push:'走水' }[s]||s }
function fmt(d) { if(!d) return ''; const t=new Date(d); return `${t.getMonth()+1}-${t.getDate()} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}` }
function formatViewTime(d) { if(!d) return ''; const t=new Date(d); return `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}` }
function msLabel(s) { return !s||s==='pending'?'待定':s==='hit'?'中':s==='push'?'走':'错' }
function msClass(s) { return !s||s==='pending'?'ms-pen':s==='hit'?'ms-hit':s==='push'?'ms-push':'ms-miss' }

async function loadRecs(more=false) {
  if(loading.value) return; loading.value=true
  try {
    const p = more?page.value+1:1, params = { page:p, page_size:20 }
    const f = filters[fi.value].value; if(f!=='all') params.prediction_type=f
    const res = await api.getAdminRecommendations(params)
    const items = (res.items||[]).filter(x=>x.status!=='inactive')
    recs.value = more?[...recs.value,...items]:items
    hasMore.value = res.has_more; page.value=p
  }catch(e){ console.error(e) }finally{ loading.value=false }
}
function onFilter(i) { if(i===fi.value) return; fi.value=i; page.value=1; recs.value=[]; loadRecs() }
function loadMore() { loadRecs(true) }

async function toggleConfirm(r) { try { await api.toggleConfirm(r.id); r.is_confirmed=!r.is_confirmed }catch(e){ alert(e.message) } }

function openResult(r) { rf.id=r.id; rf.title=r.title; rf.hitStatus='hit'; rf.partialDetail=''; rf.notes=''; hi.value=0; showResult.value=true }
async function submitResult() {
  submitting.value=true
  try {
    const ao = { hit_status:rf.hitStatus, notes:rf.notes||null, is_highlight:false }
    if(rf.hitStatus==='partial'&&rf.partialDetail) ao.partial_detail=rf.partialDetail
    await api.markResult(rf.id, { actual_outcome: ao })
    showResult.value=false; page.value=1; recs.value=[]; loadRecs()
  }catch(e){ alert(e.message) }finally{ submitting.value=false }
}

async function openViewers(r) {
  showViewers.value=true; vTitle.value=r.title; viewers.value=[]; vTotal.value=0; vUnique.value=0; vGuest.value=0; vAvg.value=0;
  try {
    const res = await api.getViewRecords(r.id)
    // 按浏览次数降序排列
    const sorted = (res.records||[]).sort((a,b) => (b.view_count||0) - (a.view_count||0))
    viewers.value = sorted.map(x => ({
      ...x,
      _roleLabel: x.user_role==='admin'?'管理员':x.user_role==='guest'?'游客':x.user_is_paid?'会员':'非会员',
      _roleClass: x.user_role==='admin'?'va':x.user_role==='guest'?'vg':x.user_is_paid?'vp':'vf',
      _viewedAt: x.last_viewed_at ? formatViewTime(x.last_viewed_at) : '',
      _firstAt: x.first_viewed_at ? formatViewTime(x.first_viewed_at) : ''
    }))
    vTotal.value = res.total
    vUnique.value = res.unique_viewers
    vGuest.value = res.guest_view_count || 0
    vAvg.value = vUnique.value > 0 ? (vTotal.value / vUnique.value).toFixed(1) : 0
  } catch(e) { alert('加载浏览记录失败: ' + (e.message||'')) }
}

async function toggleMatch(r, mi) {
  const m = r.prediction_data.single_matches[mi]
  const cycle = { undefined:'hit', pending:'hit', hit:'push', push:'miss', miss:'pending' }
  m.hit_status = cycle[m.hit_status||'pending']
  try { await api.updateRecommendation(r.id, { prediction_data: r.prediction_data }) }
  catch(e){ alert('更新失败') }
}

function delRec(r) { if(!confirm(`删除「${r.title}」？`)) return; api.deleteRecommendation(r.id).then(()=>{ recs.value=recs.value.filter(x=>x.id!==r.id) }).catch(e=>alert(e.message)) }

loadRecs()
</script>

<style scoped>
.container { max-width:900px; margin:0 auto; padding:16px 16px 40px; }
@media (min-width:768px) { .container { padding:24px 24px 40px; } }
.top-bar { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px; }
.top-bar h2 { font-size:20px; font-weight:800; color:var(--text); margin-bottom:4px; }
.hint { font-size:13px; color:var(--muted); display:block; }
.back-btn { display:inline-flex; align-items:center; gap:4px; padding:5px 12px; margin-bottom:8px; background:var(--bg); border:1px solid var(--border); border-radius:6px; font-size:13px; color:var(--text-secondary); cursor:pointer; }
.back-btn:hover { color:var(--primary); border-color:var(--primary); }
.create-btn { padding:10px 24px; background:var(--primary); color:#fff; border-radius:20px; font-size:14px; font-weight:600; flex-shrink:0; box-shadow:0 2px 8px rgba(99,102,241,0.25); }
.create-btn:hover { opacity:0.9; transform:translateY(-1px); }
.filter-row { display:flex; gap:10px; margin-bottom:18px; justify-content:center; }
.fbtn { padding:9px 22px; border-radius:20px; font-size:14px; font-weight:500; background:var(--surface); border:1px solid var(--border); color:var(--text-secondary); cursor:pointer; transition:all .15s; }
.fbtn:hover { border-color:var(--primary); color:var(--primary); }
.fbtn.on { background:var(--primary); color:#fff; border-color:var(--primary); font-weight:600; }
.list { display:flex; flex-direction:column; gap:12px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:18px 20px; position:relative; overflow:hidden; box-shadow:var(--shadow-sm); transition:box-shadow .15s; }
.card:hover { box-shadow:var(--shadow); }
.card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; }
.card.ot-hit { border-color:#A7F3D0; } .card.ot-hit::before { background:var(--success); }
.card.ot-miss::before { background:#FCA5A5; }
.card.ot-partial::before { background:var(--warning); }
.card.ot-push::before { background:#8B5CF6; }
.card.is-ok { border-color:#C7D2FE; } .card.is-ok::before { background:var(--primary); }
.badges { display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap; }
.bdg { font-size:10px; font-weight:700; padding:3px 10px; border-radius:6px; color:#fff; }
.bdg-ok { background:linear-gradient(135deg,var(--primary),#7C3AED); }
.bdg-km { background:linear-gradient(135deg,#F59E0B,#E8870A); }
.bdg-ft { background:linear-gradient(135deg,#8B5CF6,#7C3AED); }
.chd { display:flex; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap; }
.sport { font-size:12px; font-weight:600; padding:4px 12px; border-radius:12px; }
.sp-football { background:#E0F7FA; color:#0288D1; } .sp-basketball { background:#FFF3E0; color:#E65100; }
.stag { font-size:11px; font-weight:600; padding:3px 12px; border-radius:10px; }
.st-active { background:#EEF2FF; color:var(--primary); }
.st-completed { background:#ECFDF5; color:var(--success); }
.time { font-size:12px; color:var(--muted); margin-left:auto; }
.otag { font-size:11px; font-weight:700; padding:4px 12px; border-radius:6px; display:inline-flex; }
.ot-hit { background:#ECFDF5; color:#059669; border-left:3px solid var(--success); }
.ot-miss { background:#FEF2F2; color:#DC2626; border-left:3px solid #EF4444; }
.ot-partial { background:#FFFBEB; color:#D97706; border-left:3px solid var(--warning); }
.ot-push { background:#F5F3FF; color:#7C3AED; border-left:3px solid #8B5CF6; }
.title { font-size:15px; font-weight:700; margin-bottom:10px; line-height:1.5; color:var(--text); }
.preview { background:var(--bg); border-radius:10px; padding:14px 16px; margin-bottom:10px; border:1px solid var(--border-light); }
.pv-label { font-size:11px; font-weight:600; color:var(--muted); margin-bottom:10px; letter-spacing:0.03em; }
.match-row { background:#fff; border-radius:8px; padding:14px 14px; margin-bottom:8px; border:1px solid var(--border-light); position:relative; }
.match-row::before { content:''; position:absolute; left:0; top:10px; bottom:10px; width:3px; border-radius:0 2px 2px 0; }
.match-row:has(.mr-km)::before { background:#F59E0B; }
.match-row:has(.mr-ft)::before { background:#8B5CF6; }
.match-row:last-child { margin-bottom:0; }
.mr-top { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.mr-id { font-size:11px; font-weight:600; color:var(--muted); }
.mr-tag { font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; }
.mr-km { color:#B45309; background:#FFFDF5; border:1px solid #FDE68A; }
.mr-ft { color:#6D28D9; background:#FAFAFE; border:1px solid #DDD6FE; }
.mr-toggle { margin-left:auto; font-size:12px; font-weight:700; padding:5px 14px; border-radius:8px; min-width:50px; text-align:center; cursor:pointer; border:1px solid; transition:all .1s; }
.ms-pen { background:#F8FAFC; color:#94A3B8; border-color:#E2E8F0; }
.ms-hit { background:#D1FAE5; color:#065F46; border-color:#A7F3D0; }
.ms-push { background:#E0E7FF; color:#4338CA; border-color:#C7D2FE; }
.ms-miss { background:#FEE2E2; color:#991B1B; border-color:#FECACA; }
.mr-vs { font-size:14px; font-weight:600; display:block; margin-bottom:6px; color:var(--text); text-align:center; }
.mr-preds { display:flex; gap:8px; flex-wrap:wrap; justify-content:center; }
.mr-pred { font-size:12px; font-weight:600; color:#B45309; background:#FFFBEB; padding:3px 12px; border-radius:6px; border:1px solid #FDE68A; }
.mr-basis { margin-top:8px; padding:10px 12px; background:var(--bg); border-radius:6px; border-left:3px solid var(--primary); }
.mr-basis-text { font-size:13px; color:var(--text-secondary); line-height:1.6; white-space:pre-line; }
.parlay-row { font-size:13px; padding:8px 12px; background:#fff; border-radius:6px; margin-bottom:4px; border:1px solid var(--border-light); }
.parlay-row:last-child { margin-bottom:0; }
.actions { display:flex; flex-direction:column; gap:8px; margin-top:8px; }
.actions-row { display:flex; gap:8px; }
.act { font-size:13px; font-weight:600; padding:8px 0; border-radius:8px; border:1px solid; cursor:pointer; transition:all .15s; text-align:center; }
.act:hover { opacity:0.85; }
.act-ok { flex:1; padding:10px 0; font-size:14px; background:var(--primary); color:#fff; border-color:var(--primary); }
.act-view, .act-edit, .act-result, .act-del { flex:1; }
.act-view { background:#EFF6FF; color:#2563EB; border-color:#BFDBFE; }
.act-edit { background:#FFFBEB; color:#D97706; border-color:#FDE68A; }
.act-result { background:#ECFDF5; color:#059669; border-color:#A7F3D0; }
.act-del { background:#FEF2F2; color:#DC2626; border-color:#FECACA; }
.more { text-align:center; padding:32px 0; color:var(--primary); font-weight:600; cursor:pointer; font-size:15px; }

.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,.4); z-index:200; display:flex; align-items:center; justify-content:center; padding:24px; }
.modal { background:#fff; border-radius:16px; padding:28px; max-width:500px; width:100%; max-height:80vh; overflow-y:auto; }
.modal-xl { max-width:680px; }
.modal h3 { font-size:18px; font-weight:700; margin-bottom:4px; }
.msub { font-size:13px; color:var(--muted); margin-bottom:16px; }
.mbtns { display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }
.mbtn { padding:8px 18px; border-radius:20px; font-size:13px; font-weight:600; background:var(--bg); border:1px solid var(--border); color:var(--text-secondary); cursor:pointer; }
.mbtn.on { background:var(--primary); color:#fff; border-color:var(--primary); }
.minp,.mta { width:100%; padding:10px 14px; border:1px solid var(--border); border-radius:8px; font-size:14px; margin-bottom:12px; background:var(--bg); }
.mact { display:flex; gap:10px; }
.msubmit { flex:1; padding:12px; background:var(--primary); color:#fff; border-radius:10px; font-size:15px; font-weight:700; cursor:pointer; }
.msubmit:disabled { opacity:.5; }
.mcancel { padding:12px 24px; background:var(--bg); color:var(--text-secondary); border-radius:10px; cursor:pointer; }

/* ===== 浏览记录弹窗 ===== */
.vw-head { margin-bottom:0; }
.vw-head .msub { margin-bottom:14px; }

/* 汇总统计 */
.vw-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:18px; }
.vw-stat {
  text-align:center; padding:14px 8px; border-radius:var(--radius);
  background:var(--bg); border:1px solid var(--border-light);
}
.vw-stat-num { display:block; font-size:24px; font-weight:800; color:var(--text); line-height:1.2; }
.vw-stat-label { font-size:12px; color:var(--muted); margin-top:4px; display:block; }
.vw-stat--user .vw-stat-num { color:var(--primary); }
.vw-stat--guest .vw-stat-num { color:#8B5CF6; }
.vw-stat--avg .vw-stat-num { color:#F59E0B; }

/* 列表 */
.vw-list { max-height:340px; overflow-y:auto; margin-bottom:14px; }
.vw-list-head {
  display:flex; align-items:center; gap:8px;
  padding:8px 12px; font-size:12px; font-weight:600; color:var(--muted);
  border-bottom:2px solid var(--border); position:sticky; top:0; background:#fff; z-index:1;
}
.vw-empty { text-align:center; padding:28px 0; color:var(--muted); font-size:14px; }

.vw-row {
  display:flex; align-items:center; gap:8px;
  padding:12px 12px; border-bottom:1px solid var(--border-light); font-size:13px;
  transition:background .1s;
}
.vw-row:hover { background:var(--bg); }

.vw-col-phone { flex:2; min-width:0; display:flex; flex-direction:column; }
.vw-nickname { font-weight:600; color:var(--text); font-size:14px; }
.vw-phone-sub { font-size:11px; color:var(--muted); }
.vw-col-role { flex:1; text-align:center; }
.vw-col-count { width:48px; text-align:center; }
.vw-col-first { width:110px; text-align:center; font-size:12px; color:var(--muted); }
.vw-col-last { width:110px; text-align:center; font-size:12px; color:var(--muted); }
.vw-list-head .vw-col-first,
.vw-list-head .vw-col-last { font-size:12px; color:var(--muted); }

.vw-tag { font-size:10px; font-weight:600; padding:2px 8px; border-radius:6px; display:inline-block; }
.va { background:#EEF2FF; color:var(--primary); } .vg { background:#F5F3FF; color:#7C3AED; } .vp { background:#FEF3C7; color:#B45309; } .vf { background:var(--bg); color:var(--muted); }
.vw-count-badge {
  display:inline-flex; align-items:center; justify-content:center;
  min-width:28px; height:24px; padding:0 6px; border-radius:12px;
  background:var(--primary-light); color:var(--primary);
  font-size:13px; font-weight:700;
}
.vw-close { display:block; margin:0 auto; }

@media (max-width:767px) {
  .vw-stats { grid-template-columns:repeat(2,1fr); }
  .vw-stat-num { font-size:20px; }
  .vw-col-first, .vw-col-last { display:none; }
  .vw-list-head .vw-col-first,
  .vw-list-head .vw-col-last { display:none; }
  .vw-col-phone { flex:1.5; }
  .modal { padding:20px 16px; }
  .vw-row { padding:10px 8px; }
  .vw-nickname { font-size:13px; }
}

@media (max-width:767px) {
  .card { padding:14px 16px; }
  .actions { gap:4px; } .act { padding:6px 12px; font-size:11px; }
  .title { font-size:14px; }
}
</style>
