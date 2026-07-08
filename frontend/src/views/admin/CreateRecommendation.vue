<template>
  <div class="page">
    <div class="container">
      <div class="top-bar">
        <button class="back-btn" @click="$router.push('/admin/recommendations')">← 返回</button>
        <h2>{{ editId ? '编辑推荐' : '创建推荐' }}</h2>
      </div>

      <!-- 预测类型 -->
      <div class="form-item">
        <span class="label">预测类型</span>
        <div class="type-toggles">
          <button :class="['type-btn',{on:sportType==='football'}]" @click="sportType='football'">足球</button>
          <button :class="['type-btn',{on:sportType==='basketball'}]" @click="sportType='basketball'">篮球</button>
        </div>
      </div>

      <!-- 标题 -->
      <div class="form-item">
        <span class="label">推荐标题（最多50字）</span>
        <input v-model="title" class="inp" placeholder="请输入推荐标题" maxlength="50" />
        <span class="cnt">{{ title.length }}/50</span>
      </div>

      <!-- 推广标题 -->
      <div class="form-item">
        <span class="label">推广标题（选填，最多100字）</span>
        <textarea v-model="promoTitle" class="inp ta" placeholder="今日3场精选：灰熊vs尼克斯大小分..." maxlength="100" rows="5"></textarea>
        <span class="cnt">{{ promoTitle.length }}/100</span>
      </div>

      <!-- 单场模块 -->
      <div class="module-card">
        <div class="module-header" @click="showMatches = !showMatches">
          <span class="mod-arrow">{{ showMatches ? '▼' : '▶' }}</span>
          <span class="mod-title">单场（{{ matches.length }}场详情）</span>
          <button class="add-btn" @click.stop="addMatch">+ 添加</button>
        </div>
        <div v-if="showMatches" class="module-body">
          <div v-for="(m, i) in matches" :key="i" class="match-item">
            <!-- 场次ID + 删除 -->
            <div class="mi-row">
              <input v-model="m.match_id" class="mi-id" placeholder="场次ID 如:#302" maxlength="10" />
              <button class="mi-del" @click="matches.splice(i,1)">删除</button>
            </div>
            <!-- 主队 vs 客队 -->
            <div class="mi-row mi-vs-row">
              <input v-model="m.home_team" class="mi-half" placeholder="主队" maxlength="30" />
              <span class="mi-vs">vs</span>
              <input v-model="m.away_team" class="mi-half" placeholder="客队" maxlength="30" />
            </div>
            <!-- 总分 + 让分 -->
            <div class="mi-row">
              <input v-model="m.total_points" class="mi-half" placeholder="总分 如:大235.5" maxlength="30" />
              <input v-model="m.handicap" class="mi-half" placeholder="让分 如:主队-1.5" maxlength="30" />
            </div>
            <!-- 置信度 -->
            <div class="mi-row">
              <input v-model="m.prediction_rate" class="mi-id" type="number" placeholder="置信度 %（如：85）" style="max-width:200px" />
            </div>
            <!-- 开关：公开/重心/精选/冷门 -->
            <div class="mi-switches">
              <label class="sw-row"><span>是否公开展示</span><span class="sw-track"><input type="checkbox" v-model="m.is_public" /><i></i></span></label>
              <label class="sw-row"><span>是否重心场次</span><span class="sw-track"><input type="checkbox" v-model="m.is_key_match" /><i></i></span></label>
              <label class="sw-row"><span>是否精选核心</span><span class="sw-track"><input type="checkbox" v-model="m.is_featured" /><i></i></span></label>
              <label class="sw-row"><span>是否冷门预警</span><span class="sw-track"><input type="checkbox" v-model="m.is_upset_warning" /><i></i></span></label>
            </div>
            <!-- 预测依据 + 模板按钮 -->
            <div class="mi-basis">
              <div class="basis-head">
                <span>总结简述（选填，最多200字）</span>
                <button class="tpl-btn" @click="applyTemplate(i)">使用模板</button>
              </div>
              <textarea v-model="m.prediction_basis" class="mi-ta" placeholder="总结简述（选填）" maxlength="200" rows="8"></textarea>
              <span class="cnt">{{ m.prediction_basis?.length || 0 }}/200</span>
            </div>
          </div>
          <p v-if="!matches.length" class="empty-tip">点击"+ 添加"按钮添加单场</p>
        </div>
      </div>

      <!-- 组合模块 -->
      <div class="module-card">
        <div class="module-header" @click="showParlays = !showParlays">
          <span class="mod-arrow">{{ showParlays ? '▼' : '▶' }}</span>
          <span class="mod-title">组合建议（{{ parlays.length }}个）</span>
          <button class="add-btn" @click.stop="addParlay">+ 添加</button>
        </div>
        <div v-if="showParlays" class="module-body">
          <div v-for="(p, i) in parlays" :key="i" class="parlay-item">
            <div class="mi-row">
              <span class="pi-label">组合 #{{ i+1 }}</span>
              <button class="mi-del" @click="parlays.splice(i,1)">删除</button>
            </div>
            <div class="pi-field">
              <span class="pi-lbl">组合场次：</span>
              <input v-model="p.match_ids" class="inp" placeholder="输入比赛ID，用+分隔 如:#307+#309" />
            </div>
            <div class="pi-field">
              <span class="pi-lbl">选择类型：</span>
              <input v-model="p.bet_types" class="inp" placeholder="输入类型，用×分隔 如:主胜×高分×客胜" />
            </div>
          </div>
          <p v-if="!parlays.length" class="empty-tip">点击"+ 添加"按钮添加组合建议</p>
        </div>
      </div>

      <button class="submit-btn" :disabled="submitting" @click="submit">{{ submitting?'提交中...':(editId?'更新推荐':'创建推荐') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const editId = ref(route.params.id || null)
const sportType = ref('football')
const title = ref('')
const promoTitle = ref('')
const matches = ref([])
const parlays = ref([])
const submitting = ref(false)
const loading = ref(false)
const showMatches = ref(true)
const showParlays = ref(true)

function addMatch() {
  matches.value.push({ match_id:'', home_team:'', away_team:'', total_points:'', handicap:'', prediction_rate:'', prediction_basis:'', is_public:false, is_key_match:false, is_featured:false, is_upset_warning:false })
}
function addParlay() { parlays.value.push({ match_ids:'', bet_types:'' }) }

function applyTemplate(i) {
  const t = sportType.value === 'basketball'
    ? '基于球队攻防效率值、伤病名单分析、背靠背赛程影响、市场指数波动及AI预测模型综合研判'
    : '综合AI大模型、市场数据变化趋势、球队近期战绩及历史交锋数据，结合AI算法置信度评估'
  matches.value[i].prediction_basis = t
}

async function submit() {
  if (!title.value.trim()) return alert('请输入标题')
  submitting.value = true
  try {
    const pd = { prediction_type: sportType.value, single_matches: matches.value.map(m => ({
      match_id: m.match_id, home_team: m.home_team, away_team: m.away_team,
      handicap: m.handicap||null, total_points: m.total_points||null,
      prediction_rate: m.prediction_rate?Number(m.prediction_rate):null,
      prediction_basis: m.prediction_basis||null,
      is_key_match: m.is_key_match, is_featured: m.is_featured,
      is_public: m.is_public, is_upset_warning: m.is_upset_warning
    }))}
    if (parlays.value.length) pd.parlays = parlays.value.map(p => ({
      match_ids: p.match_ids.split('+').map(s=>s.trim()).filter(Boolean),
      bet_types: p.bet_types.split('×').map(s=>s.trim()).filter(Boolean)
    }))
    const data = { prediction_type: sportType.value, title: title.value.trim(), prediction_data: pd, analysis_text: '' }
    if (promoTitle.value.trim()) data.promotion_title = promoTitle.value.trim()

    if (editId.value) {
      await api.updateRecommendation(editId.value, data)
    } else {
      await api.createRecommendation(data)
    }
    alert(editId.value ? '更新成功' : '创建成功')
    router.push('/admin/recommendations')
  } catch(e) { alert(e.message||'操作失败') } finally { submitting.value = false }
}

onMounted(async () => {
  if (!editId.value) return
  loading.value = true
  try {
    const res = await api.getRecommendationDetail(editId.value)
    sportType.value = res.prediction_type || 'football'
    title.value = res.title || ''
    promoTitle.value = res.promotion_title || ''
    if (res.prediction_data) {
      const pd = res.prediction_data
      matches.value = (pd.single_matches || []).map(m => ({
        match_id: m.match_id||'', home_team: m.home_team||'', away_team: m.away_team||'',
        total_points: m.total_points||'', handicap: m.handicap||'',
        prediction_rate: m.prediction_rate||'', prediction_basis: m.prediction_basis||'',
        is_public: m.is_public||false, is_key_match: m.is_key_match||false,
        is_featured: m.is_featured||false, is_upset_warning: m.is_upset_warning||false
      }))
      parlays.value = (pd.parlays || []).map(p => ({
        match_ids: (p.match_ids||[]).join('+'), bet_types: (p.bet_types||[]).join(' × ')
      }))
    }
  } catch(e) { alert('加载失败') } finally { loading.value = false }
})
</script>

<style scoped>
.container { max-width:720px; margin:0 auto; padding:16px 16px 48px; }
@media (min-width:768px) { .container { padding:24px 24px 48px; } }
.top-bar { margin-bottom:20px; }
.top-bar h2 { font-size:22px; font-weight:800; color:var(--text); }
.back-btn { display:inline-flex; align-items:center; gap:4px; padding:5px 12px; margin-bottom:8px; background:var(--bg); border:1px solid var(--border); border-radius:6px; font-size:13px; color:var(--text-secondary); cursor:pointer; }
.back-btn:hover { color:var(--primary); border-color:var(--primary); }

/* ===== FORM ITEM ===== */
.form-item { background:var(--surface); border-radius:var(--radius); padding:14px 18px; margin-bottom:10px; border:1px solid var(--border); }
.label { display:block; font-size:13px; font-weight:600; color:var(--text-secondary); margin-bottom:6px; }
.inp { width:100%; padding:8px 12px; background:var(--bg); border:1px solid var(--border); border-radius:7px; font-size:14px; color:var(--text); }
.inp:focus { border-color:var(--primary); outline:none; }
.cnt { display:block; text-align:right; font-size:12px; color:var(--muted); margin-top:4px; }
.type-toggles { display:flex; gap:10px; }
.type-btn { flex:1; padding:10px 0; border-radius:8px; background:var(--bg); border:1px solid var(--border); font-size:14px; font-weight:500; color:var(--text-secondary); cursor:pointer; transition:all .15s; text-align:center; }
.type-btn.on { background:var(--primary); color:#fff; border-color:var(--primary); font-weight:600; }

/* ===== MODULE CARD ===== */
.module-card { background:var(--surface); border-radius:var(--radius); margin-bottom:12px; border:1px solid var(--border); overflow:hidden; }
.module-header { display:flex; align-items:center; gap:8px; padding:12px 18px; cursor:pointer; user-select:none; }
.module-header:hover { background:var(--bg); }
.mod-arrow { font-size:10px; color:var(--muted); flex-shrink:0; }
.mod-title { flex:1; font-size:14px; font-weight:700; color:var(--text); }
.add-btn { padding:5px 16px; background:var(--primary); color:#fff; border-radius:20px; font-size:12px; font-weight:600; cursor:pointer; flex-shrink:0; }
.add-btn:hover { opacity:0.9; }
.module-body { padding:0 18px 18px; }

/* ===== MATCH ITEM ===== */
.match-item { background:var(--bg); border-radius:10px; padding:14px; margin-bottom:10px; border:1px solid var(--border-light); }
.match-item:last-child { margin-bottom:0; }
.mi-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.mi-id { flex:1; padding:7px 10px; background:#fff; border:1px solid var(--border); border-radius:6px; font-size:13px; color:var(--text); }
.mi-id:focus { border-color:var(--primary); outline:none; }
.mi-del { font-size:11px; color:var(--error); cursor:pointer; background:none; padding:3px 10px; border-radius:4px; border:1px solid transparent; }
.mi-del:hover { background:#FEF2F2; border-color:#FECACA; }

.mi-vs-row { justify-content:center; }
.mi-half { flex:1; min-width:0; padding:7px 12px; background:#fff; border:1px solid var(--border); border-radius:6px; font-size:13px; font-weight:600; color:var(--text); text-align:center; }
.mi-half:focus { border-color:var(--primary); outline:none; }
.mi-vs { font-size:12px; font-weight:700; color:var(--muted); flex-shrink:0; }

/* 封面 */
.inp.ta { resize:vertical; min-height:52px; }

/* 开关 */
.mi-switches { display:flex; flex-wrap:wrap; gap:6px 14px; margin-bottom:10px; }
.sw-row { display:flex; align-items:center; gap:8px; cursor:pointer; font-size:13px; color:var(--text-secondary); }
.sw-track { position:relative; width:40px; height:22px; flex-shrink:0; }
.sw-track input { opacity:0; width:0; height:0; position:absolute; }
.sw-track i { position:absolute; inset:0; background:#CBD5E1; border-radius:11px; transition:.2s; }
.sw-track i::after { content:''; position:absolute; width:16px; height:16px; left:3px; top:3px; background:#fff; border-radius:50%; transition:.2s; box-shadow:0 1px 2px rgba(0,0,0,.15); }
.sw-track input:checked+i { background:var(--primary); }
.sw-track input:checked+i::after { transform:translateX(18px); }

/* 预测依据 */
.mi-basis { margin-top:2px; }
.basis-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; font-size:12px; color:var(--muted); }
.tpl-btn { padding:3px 12px; background:#fff; border:1px solid var(--primary); border-radius:12px; font-size:11px; color:var(--primary); cursor:pointer; }
.tpl-btn:hover { background:var(--primary-light); }
.mi-ta { width:100%; padding:8px 10px; background:#fff; border:1px solid var(--border); border-radius:6px; font-size:13px; resize:vertical; color:var(--text); }
.mi-ta:focus { border-color:var(--primary); outline:none; }

/* ===== PARLAY ===== */
.parlay-item { background:var(--bg); border-radius:10px; padding:16px; margin-bottom:12px; border:1px solid var(--border-light); }
.parlay-item:last-child { margin-bottom:0; }
.pi-label { font-size:14px; font-weight:700; color:var(--text); flex:1; }
.pi-field { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.pi-lbl { font-size:13px; color:var(--text-secondary); white-space:nowrap; flex-shrink:0; }

.empty-tip { text-align:center; padding:32px 20px; font-size:14px; color:var(--muted); }

.submit-btn { width:100%; padding:16px; margin-top:8px; background:var(--primary); color:#fff; border-radius:12px; font-size:17px; font-weight:700; cursor:pointer; box-shadow:0 4px 20px rgba(99,102,241,0.25); transition:all .15s; }
.submit-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 8px 28px rgba(99,102,241,0.35); }
.submit-btn:disabled { opacity:0.5; cursor:not-allowed; }

@media (max-width:767px) {
  .mi-three { flex-wrap:wrap; } .mi-third { min-width:calc(50% - 4px); }
  .sw-row { font-size:13px; }
}
</style>
