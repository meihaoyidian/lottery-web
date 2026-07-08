<template>
  <div class="page">
    <div class="container">
      <div class="top-bar"><button class="back-btn" @click="$router.push('/profile')">← 返回</button><h2>用户管理</h2></div>

      <!-- 搜索 -->
      <div class="search-card">
        <div class="search-row">
          <input v-model="phone" class="sinp" placeholder="输入手机号搜索" @keyup.enter="search" />
          <button class="sbtn" :disabled="loading" @click="search">{{ loading ? '搜索中' : '搜索' }}</button>
        </div>
      </div>

      <!-- 用户信息 -->
      <div v-if="user" class="ucard">
        <div class="uinfo">
          <span class="uphone">{{ user.phone }}</span>
          <div class="utags">
            <span :class="['utag', user.role==='admin'?'ut-admin':'']">{{ user.role==='admin'?'管理员':'用户' }}</span>
            <span :class="['utag', user.is_paid?'ut-paid':'ut-free']">{{ user.is_paid?'完整版':'免费' }}</span>
          </div>
        </div>
        <div class="umeta">
          <span v-if="user.paid_end_time">到期：{{ user.paid_end_time?.split('T')[0] }}</span>
          <span v-else>未开通完整版</span>
          <span class="umsep">|</span>
          <span>注册：{{ user.created_at?.split('T')[0] || '--' }}</span>
        </div>
        <button class="reset-btn" :disabled="resetting" @click="resetPwd">{{ resetting?'重置中...':'重置密码' }}</button>
      </div>

      <!-- 完整版设置 -->
      <div v-if="user" class="form-card">
        <h3 class="ftitle">完整版设置</h3>
        <div class="tiers">
          <div v-for="(t,i) in tiers" :key="t.days" :class="['tier', { on: sel===i }]" @click="sel = sel===i ? null : i">
            <span class="tname">{{ t.name }}</span><span class="tdesc">{{ t.desc }}</span>
          </div>
        </div>
        <button v-if="user.is_paid" class="cancel-btn" :disabled="cancelling" @click="cancelVip">{{ cancelling?'取消中...':'取消完整版' }}</button>
        <button v-if="sel!==null" class="submit-btn" :disabled="submitting" @click="setVip">确认开通 {{ tiers[sel].name }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../../api'

const phone = ref(''), user = ref(null), loading = ref(false)
const tiers = [{ name:'15天', days:15, desc:'体验' },{ name:'1个月', days:30, desc:'月卡' },{ name:'3个月', days:90, desc:'季卡' },{ name:'1年', days:365, desc:'年卡' }]
const sel = ref(null), submitting = ref(false), cancelling = ref(false), resetting = ref(false)

async function search() {
  if(phone.value.trim().length<3) return alert('请输入有效手机号')
  loading.value=true; user.value=null; sel.value=null
  try { user.value = await api.searchUser(phone.value.trim()) }
  catch(e){ alert(e.statusCode===404?'用户不存在':e.message) }
  finally{ loading.value=false }
}

async function setVip() {
  submitting.value=true
  try { const res = await api.setMembership(user.value.id, tiers[sel.value].days); alert(res.message); await search() }
  catch(e){ alert(e.message) } finally{ submitting.value=false }
}

async function cancelVip() {
  cancelling.value=true
  try { const res = await api.cancelMembership(user.value.id); alert(res.message); await search() }
  catch(e){ alert(e.message) } finally{ cancelling.value=false }
}

async function resetPwd() {
  if(!confirm(`为 ${user.value.phone} 重置密码？`)) return
  resetting.value=true
  try { const res = await api.resetPassword(user.value.id); alert(`新密码：${res.new_password}\n请截图发给用户`) }
  catch(e){ alert(e.message) } finally{ resetting.value=false }
}
</script>

<style scoped>
.container { max-width:600px; margin:0 auto; padding:24px; }
.top-bar { margin-bottom:20px; } .top-bar h2 { font-size:20px; font-weight:800; }
.back-btn { display:inline-flex; align-items:center; gap:4px; padding:4px 12px; margin-bottom:8px; background:var(--bg); border:1px solid var(--border); border-radius:6px; font-size:13px; color:var(--text-secondary); cursor:pointer; }
.back-btn:hover { color:var(--primary); border-color:var(--primary); }
.search-card { background:var(--surface); border-radius:var(--radius); padding:20px; margin-bottom:16px; border:1px solid var(--border); }
.search-row { display:flex; gap:10px; }
.sinp { flex:1; height:44px; padding:0 14px; background:var(--bg); border:1px solid var(--border); border-radius:8px; font-size:15px; }
.sbtn { padding:0 20px; background:var(--primary); color:#fff; border-radius:8px; font-size:14px; font-weight:600; }
.sbtn:disabled{ opacity:.6; }
.ucard { background:var(--surface); border-radius:var(--radius); padding:20px; margin-bottom:16px; border:1px solid var(--border); }
.uinfo { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.uphone { font-size:18px; font-weight:700; }
.utags { display:flex; gap:6px; }
.utag { font-size:11px; font-weight:600; padding:3px 12px; border-radius:12px; }
.ut-admin { background:#EEF2FF; color:var(--primary); }
.ut-paid { background:#FEF3C7; color:#B45309; }
.ut-free { background:var(--bg); color:var(--muted); }
.umeta { font-size:13px; color:var(--muted); margin-bottom:14px; }
.umsep { margin:0 8px; color:var(--border); }
.reset-btn { width:100%; padding:10px; background:#FEF2F2; color:var(--error); border:1px solid #FECACA; border-radius:8px; font-size:14px; font-weight:600; }
.reset-btn:disabled{ opacity:.5; }
.form-card { background:var(--surface); border-radius:var(--radius); padding:20px; border:1px solid var(--border); }
.ftitle { font-size:16px; font-weight:700; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border-light); }
.tiers { display:flex; gap:10px; margin-bottom:20px; }
.tier { flex:1; padding:18px 0; border-radius:12px; background:var(--bg); border:2px solid transparent; text-align:center; cursor:pointer; transition:.15s; }
.tier.on { background:#EEF2FF; border-color:var(--primary); }
.tname { font-size:16px; font-weight:700; display:block; }
.tdesc { font-size:12px; color:var(--muted); }
.cancel-btn { width:100%; padding:12px; margin-bottom:10px; background:#FEF2F2; color:var(--error); border:1px solid #FECACA; border-radius:10px; font-size:14px; font-weight:600; }
.cancel-btn:disabled{ opacity:.5; }
.submit-btn { width:100%; padding:14px; background:var(--primary); color:#fff; border-radius:10px; font-size:16px; font-weight:700; }
.submit-btn:disabled{ opacity:.5; }
</style>
