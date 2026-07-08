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
            <div><span class="fct">亮点数据</span><span class="fchint">（可选）</span></div>
            <button class="add-btn" @click="addHl">+ 添加</button>
          </div>
          <div v-if="!fd.highlights.length" class="empty">添加战绩亮点标签，如"连红3场"、"全中"等</div>
          <div v-for="(h,i) in fd.highlights" :key="i" class="hl-row">
            <div class="hl-main">
              <span class="hl-icon">{{ h.icon || icons[0] }}</span>
              <input class="hl-inp" v-model="h.text" placeholder="亮点文字" maxlength="20" />
            </div>
            <div class="hl-pick">
              <button v-for="ic in icons" :key="ic" :class="['hio', { on: h.icon===ic }]" @click="h.icon=ic">{{ ic }}</button>
            </div>
            <div class="hl-prev">预览：<span class="hlp-tag"><span v-if="h.icon">{{ h.icon }}</span>{{ h.text||'亮点文字' }}</span></div>
            <button class="hl-del" @click="fd.highlights.splice(i,1)">删除</button>
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import Loading from '../../components/Loading.vue'

const route = useRoute(), router = useRouter()
const editId = ref(route.params.id || null)
const loading = ref(false), submitting = ref(false)
const icons = ['','','','','','']

const fd = reactive({
  date: '', title: '', subtitle: '', highlights: [], description: '', is_active: true
})

onMounted(async () => {
  const y = new Date(); y.setDate(y.getDate()-1)
  fd.date = y.toISOString().split('T')[0]
  if (editId.value) {
    loading.value = true
    try {
      const ach = await api.getAchievement(editId.value)
      Object.assign(fd, {
        date: ach.date, title: ach.title, subtitle: ach.subtitle||'',
        highlights: ach.highlights||[], description: ach.description||'', is_active: ach.is_active
      })
    } catch(e) { alert('加载失败'); router.back() }
    finally { loading.value = false }
  }
})

function addHl() { fd.highlights.push({ text:'', icon:'' }) }

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
  } catch(e) { alert(e.message||'提交失败') }
  finally { submitting.value = false }
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

.add-btn { padding:6px 18px; background:var(--primary); color:#fff; border-radius:20px; font-size:13px; font-weight:600; }
.empty { text-align:center; padding:30px; font-size:13px; color:var(--muted); }

.hl-row { background:var(--bg); border-radius:10px; padding:16px; margin-bottom:10px; border:1px solid var(--border-light); }
.hl-main { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.hl-icon { font-size:20px; width:40px; height:40px; display:flex; align-items:center; justify-content:center; background:#fff; border-radius:8px; border:1px solid var(--border); }
.hl-inp { flex:1; padding:10px 14px; background:#fff; border:1px solid var(--border); border-radius:8px; font-size:14px; }
.hl-pick { display:flex; gap:6px; margin-bottom:10px; flex-wrap:wrap; }
.hio { width:36px; height:32px; font-size:16px; background:#fff; border:1px solid var(--border); border-radius:6px; display:flex; align-items:center; justify-content:center; }
.hio.on { border-color:var(--primary); background:var(--primary-light); }
.hl-prev { font-size:12px; color:var(--muted); margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.hlp-tag { display:inline-flex; align-items:center; gap:4px; padding:4px 14px; background:#fff; border-radius:20px; border:1px solid #DDD6FE; font-weight:600; color:#333; }
.hl-del { width:100%; padding:8px; background:#FEF2F2; color:var(--error); border:1px solid #FECACA; border-radius:8px; font-size:13px; font-weight:600; }

.dta { width:100%; min-height:160px; padding:14px; background:var(--bg); border:1px solid var(--border); border-radius:10px; font-size:14px; line-height:1.7; resize:vertical; }
.dta:focus { border-color:var(--primary); background:#fff; }
.dprev { margin-top:14px; } .dpl { font-size:12px; color:var(--muted); display:block; margin-bottom:8px; }
.dpc { padding:18px 20px; background:linear-gradient(135deg, #1E3A8A, var(--primary)); border-radius:12px; }
.dpt { font-size:13px; color:rgba(255,255,255,.9); line-height:1.8; white-space:pre-line; }

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
