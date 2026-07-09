<template>
  <div class="page">
    <div class="container">
      <Loading v-if="loading" />
      <div v-else class="form">
        <div class="top-bar">
          <button class="back-btn" @click="$router.push('/profile')">← 返回</button>
          <h2>{{ editId ? '编辑昨日战绩' : '创建昨日战绩' }}</h2>
          <span class="hint">展示在今日赛事页顶部</span>
        </div>

        <!-- 基础信息 -->
        <div class="fc">
          <div class="frow">
            <label class="flabel">日期</label>
            <input type="date" v-model="fd.date" class="finp" />
          </div>
          <div class="fdiv"></div>
          <div class="frow">
            <label class="flabel">标题</label>
            <input class="finp" v-model="fd.title" placeholder="例如：昨日5中4" maxlength="100" />
          </div>
          <div class="fdiv"></div>
          <div class="frow">
            <label class="flabel">副标题</label>
            <input class="finp" v-model="fd.subtitle" placeholder="例如：足球3中3，篮球2中1" maxlength="200" />
          </div>
        </div>

        <!-- 亮点 -->
        <div class="fc">
          <div class="fch">
            <div class="fch-title-group">
              <span class="fct">亮点数据</span>
              <span class="fchint">显示为标签，可选</span>
            </div>
            <button class="add-btn" @click="addHl">+ 添加</button>
          </div>
          <div v-if="!fd.highlights.length" class="empty">
            <span class="empty-icon">🏷️</span>
            <span>添加战绩亮点标签，如"连红3场"、"全中"等</span>
          </div>
          <div v-for="(h,i) in fd.highlights" :key="i" class="hl-row">
            <!-- 主行：图标 + 文字输入 -->
            <div class="hl-main">
              <div class="hl-icon-box">{{ h.icon || icons[0] }}</div>
              <input class="hl-inp" v-model="h.text" placeholder="亮点文字" maxlength="20" />
            </div>
            <!-- 图标选择器 -->
            <div class="hl-picker-label">选择图标</div>
            <div class="hl-pick">
              <button
                v-for="ic in icons"
                :key="ic"
                :class="['hio', { on: h.icon === ic }]"
                @click="h.icon = (h.icon === ic ? '' : ic)"
              >{{ ic }}</button>
            </div>
            <!-- 预览 -->
            <div class="hl-prev">
              <span class="hl-prev-label">预览</span>
              <span class="hlp-tag">
                <span v-if="h.icon" class="hlp-emoji">{{ h.icon }}</span>
                <span>{{ h.text || '亮点文字' }}</span>
              </span>
            </div>
            <!-- 删除 -->
            <button class="hl-del" @click="fd.highlights.splice(i,1)">
              <svg viewBox="0 0 16 16" fill="none" class="hl-del-icon"><path d="M2 4h12M5.333 4V2.667a1.333 1.333 0 011.334-1.334h2.666a1.333 1.333 0 011.334 1.334V4m2 0v9.333a1.333 1.333 0 01-1.334 1.334H4.667a1.333 1.333 0 01-1.334-1.334V4h9.334z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <span>删除</span>
            </button>
          </div>
        </div>

        <!-- 描述 -->
        <div class="fc">
          <div class="fch">
            <div><span class="fct">详细描述</span><span class="fchint">（可选）</span></div>
            <span class="fcnt">{{ fd.description.length }}/2000</span>
          </div>
          <textarea class="dta" v-model="fd.description" placeholder="填写战绩的详细描述..." maxlength="2000" rows="6"></textarea>
          <div v-if="fd.description" class="dprev">
            <span class="dpl">效果预览</span>
            <div class="dpc"><span class="dpt">{{ fd.description }}</span></div>
          </div>
        </div>

        <!-- 显示控制 -->
        <div class="fc">
          <div class="frow switch-row">
            <div><label class="flabel">在首页展示</label><span class="fsublabel">关闭后隐藏此战绩卡片</span></div>
            <label class="switch"><input type="checkbox" v-model="fd.is_active" /><span class="sw-track"></span></label>
          </div>
        </div>

        <!-- 提交 -->
        <div class="submit-row">
          <button class="smt-btn" :disabled="submitting" @click="submit">{{ submitting?'提交中...':(editId?'更新战绩':'创建战绩') }}</button>
          <button v-if="editId" class="del-btn" @click="delAch">删除此战绩</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const route = useRoute(), router = useRouter()
const editId = ref(route.params.id || null)
const loading = ref(false), submitting = ref(false)
const icons = ['🔥','⚡','🎯','💎','⭐','🏆']

const fd = reactive({
  date: '', title: '', subtitle: '', highlights: [], description: '', is_active: true
})

// 监听路由参数变化：router.replace 同路由切换时也能响应
watch(() => route.params.id, (newId) => {
  if (newId && newId !== editId.value) {
    editId.value = newId
    loadAchievement(newId)
  }
})

async function loadAchievement(id) {
  loading.value = true
  try {
    const ach = await api.getAchievement(id)
    Object.assign(fd, {
      date: ach.date, title: ach.title, subtitle: ach.subtitle||'',
      highlights: ach.highlights||[], description: ach.description||'', is_active: ach.is_active
    })
  } catch(e) { alert('加载失败'); router.back() }
  finally { loading.value = false }
}

onMounted(async () => {
  const y = new Date(); y.setDate(y.getDate()-1)
  const yesterdayStr = y.toISOString().split('T')[0]
  fd.date = yesterdayStr

  if (editId.value) {
    loadAchievement(editId.value)
  } else {
    // 创建模式：检查是否已有战绩（含 is_active=false 的），有则直接加载
    try {
      const list = await api.getAchievements()  // 返回所有战绩，不过滤 is_active
      const existing = list?.find(a => a.date === yesterdayStr)
      if (existing) {
        router.replace(`/admin/achievements/edit/${existing.id}`)
        return
      }
    } catch { /* 获取列表失败则保持创建模式 */ }
  }
})

function addHl() { fd.highlights.push({ text:'', icon: icons[0] }) }

async function submit() {
  if (!fd.date) return alert('请选择日期')
  if (!fd.title) return alert('请输入标题')
  submitting.value = true
  try {
    const data = {
      date: fd.date, title: fd.title, subtitle: fd.subtitle||null,
      total_count: 0, win_count: 0,
      highlights: fd.highlights.filter(h=>h.text.trim()).length ? fd.highlights.filter(h=>h.text.trim()) : null,
      description: fd.description||null, is_active: fd.is_active
    }
    if (editId.value) { await api.updateAchievement(editId.value, data) }
    else { await api.createAchievement(data) }
    alert('保存成功'); router.back()
  } catch(e) {
    // 409：该日期已有战绩 → 提供直接编辑入口
    if (e.data?.existing_id) {
      if (confirm(e.message || '该日期战绩已存在，是否编辑已有记录？')) {
        router.replace(`/admin/achievements/edit/${e.data.existing_id}`)
        return
      }
    }
    alert(e.message||'提交失败')
  } finally { submitting.value = false }
}

async function delAch() {
  if (!confirm('确定删除？')) return
  try { await api.deleteAchievement(editId.value); alert('已删除'); router.back() }
  catch(e) { alert(e.message) }
}
</script>

<style scoped>
.container { max-width:700px; margin:0 auto; padding:24px; }
.top-bar { margin-bottom:20px; } .top-bar h2 { font-size:20px; font-weight:800; } .hint { font-size:13px; color:var(--muted); display:block; }
.back-btn { display:inline-flex; align-items:center; gap:4px; padding:4px 12px; margin-bottom:8px; background:var(--bg); border:1px solid var(--border); border-radius:6px; font-size:13px; color:var(--text-secondary); cursor:pointer; }
.back-btn:hover { color:var(--primary); border-color:var(--primary); }

.fc { background:var(--surface); border-radius:var(--radius); padding:20px 24px; margin-bottom:14px; border:1px solid var(--border); }
.fch { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.fct { font-size:15px; font-weight:700; } .fchint { font-size:12px; color:var(--muted); margin-left:6px; }
.frow { display:flex; align-items:center; gap:14px; padding:6px 0; }
.flabel { font-size:14px; font-weight:600; color:var(--text-secondary); min-width:80px; }
.finp { flex:1; padding:10px 14px; background:var(--bg); border:1px solid var(--border); border-radius:8px; font-size:14px; }
.finp:focus { border-color:var(--primary); background:#fff; }
.fdiv { height:1px; background:var(--border-light); margin:4px 0; }
.fsublabel { font-size:12px; color:var(--muted); display:block; }
.fcnt { font-size:12px; color:var(--muted); background:var(--bg); padding:3px 10px; border-radius:6px; }

.fch-title-group { display:flex; flex-direction:column; gap:2px; }

.add-btn { padding:6px 18px; background:var(--primary); color:#fff; border-radius:20px; font-size:13px; font-weight:600; transition: all 0.15s; }
.add-btn:hover { background:var(--primary-hover); box-shadow: 0 2px 8px var(--primary-glow); }

.empty { text-align:center; padding:32px 20px; font-size:13px; color:var(--muted); display:flex; flex-direction:column; align-items:center; gap:8px; }
.empty-icon { font-size:28px; }

/* ---- 亮点行 ---- */
.hl-row {
  background: var(--bg);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 12px;
  border: 1px solid var(--border-light);
  transition: border-color 0.15s;
}
.hl-row:last-child { margin-bottom: 0; }
.hl-row:focus-within { border-color: #C7D2FE; }

.hl-main { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.hl-icon-box {
  width: 44px; height: 44px;
  display:flex; align-items:center; justify-content:center;
  background: #fff; border-radius: 10px; border: 1px solid var(--border);
  font-size: 22px; flex-shrink: 0; box-shadow: var(--shadow-sm);
}
.hl-inp {
  flex: 1; padding: 11px 14px;
  background: #fff; border: 1px solid var(--border); border-radius: 8px;
  font-size: 14px; outline: none;
}
.hl-inp:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }

.hl-picker-label { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }

.hl-pick {
  display:flex; gap:8px; margin-bottom: 14px; flex-wrap:wrap;
}
.hio {
  width: 40px; height: 36px; font-size: 18px;
  background: #fff; border: 1.5px solid var(--border);
  border-radius: 8px; display:flex; align-items:center; justify-content:center;
  cursor: pointer; transition: all 0.12s; min-width: 40px; min-height: 36px;
}
.hio:hover { border-color: #A5B4FC; background: #F5F3FF; transform: scale(1.1); }
.hio.on {
  border-color: var(--primary); background: var(--primary-light);
  box-shadow: 0 0 0 3px var(--primary-glow); transform: scale(1.08);
}

.hl-prev { display:flex; align-items:center; gap:10px; margin-bottom:14px; }
.hl-prev-label {
  font-size: 11px; font-weight: 600; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.05em;
}
.hlp-tag {
  display:inline-flex; align-items:center; gap:5px;
  padding:5px 16px; background: #fff;
  border-radius: 20px; border: 1.5px solid #DDD6FE;
  font-size: 13px; font-weight: 600; color: var(--text);
  box-shadow: var(--shadow-sm);
}
.hlp-emoji { font-size: 15px; flex-shrink: 0; }

.hl-del {
  width: 100%; padding: 9px;
  background: #FEF2F2; color: var(--error);
  border: 1px solid #FECACA; border-radius: 8px;
  font-size: 13px; font-weight: 600;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  cursor: pointer; transition: all 0.12s;
}
.hl-del:hover { background: #FEE2E2; border-color: #FCA5A5; }
.hl-del-icon { width: 14px; height: 14px; flex-shrink: 0; }

.dta { width:100%; min-height:160px; padding:14px; background:var(--bg); border:1px solid var(--border); border-radius:10px; font-size:14px; line-height:1.7; resize:vertical; }
.dta:focus { border-color:var(--primary); background:#fff; }
.dprev { margin-top:14px; } .dpl { font-size:12px; color:var(--muted); display:block; margin-bottom:8px; }
/* 预览效果与今日赛事页战绩 Banner 的描述展示保持一致（浅色卡片 + 相同排版）*/
.dpc { padding:16px 18px; background:linear-gradient(160deg,#FFFFFF,#FAFBFF,#F5F3FF); border:1px solid var(--border); border-radius:12px; }
.dpt { font-size:13px; color:var(--text-secondary); line-height:1.8; white-space:pre-line; }

/* switch */
.switch-row { justify-content:space-between; }
.switch { position:relative; display:inline-block; width:48px; height:28px; cursor:pointer; }
.switch input { opacity:0; width:0; height:0; }
.sw-track { position:absolute; inset:0; background:#CBD5E1; border-radius:14px; transition:.2s; }
.sw-track::after { content:''; position:absolute; width:22px; height:22px; left:3px; bottom:3px; background:#fff; border-radius:50%; transition:.2s; }
.switch input:checked+.sw-track { background:var(--primary); }
.switch input:checked+.sw-track::after { transform:translateX(20px); }

.submit-row { display:flex; gap:12px; margin-top:24px; }
.smt-btn { flex:1; padding:16px; background:var(--primary); color:#fff; border-radius:12px; font-size:16px; font-weight:700; }
.smt-btn:disabled { opacity:.5; }
.del-btn { padding:16px 24px; background:#fff; color:var(--error); border:1px solid #FECACA; border-radius:12px; font-size:14px; font-weight:600; }
</style>
