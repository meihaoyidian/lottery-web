<template>
  <div class="container">
    <Loading v-if="loading" />

    <template v-else-if="!auth.token || !user">
      <!-- 未登录状态 -->
      <div class="guest-card">
        <div class="guest-card-bg"></div>
        <div class="guest-body">
          <div class="guest-avatar">
            <img class="guest-avatar-img" src="/logo.png" alt="logo" />
          </div>
          <h2 class="guest-title">AI竞界</h2>
          <p class="guest-desc">登录后可查看个人数据、开通会员、管理战绩</p>
          <button class="guest-login-btn" @click="$router.push('/login')">登录 / 注册</button>
        </div>
      </div>
    </template>

    <template v-else>
      <!-- 用户头部卡片 -->
      <div class="user-card" :class="cardClass">
        <div class="user-card-bg"></div>
        <div class="user-card-body">
          <div class="avatar-col">
            <div class="avatar" :class="avatarClass">
              <img class="avatar-img" src="/logo.png" alt="logo" />
            </div>
          </div>
          <div class="info-col">
            <div class="nickname-hero">
              <span v-if="!editing" class="nickname-text">{{ user?.nickname || '点击设置昵称' }}</span>
              <div v-if="!editing" class="nickname-edit" @click="startEdit">
                <span class="edit-icon">✎</span>
              </div>
              <div v-else class="nickname-input-wrap">
                <input v-model="nicknameInput" class="nickname-input" maxlength="20" @keyup.enter="saveNickname" />
                <span class="nickname-confirm" @click="saveNickname">确定</span>
              </div>
            </div>
            <div class="phone-row">
              <span class="phone-text">{{ user?.phone || '--' }}</span>
              <span class="phone-copy" @click="copyPhone">复制账号</span>
            </div>
            <div class="identity-tag" :class="identityClass">
              <i class="id-dot"></i>
              <span>{{ identityText }}</span>
            </div>
          </div>
        </div>
        <div class="user-stats-row">
          <div class="user-stat">
            <span class="user-stat-value">{{ registerTime || '--' }}</span>
            <span class="user-stat-label">加入时间</span>
          </div>
          <div class="user-stat-divider"></div>
          <div class="user-stat">
            <span class="user-stat-value" :class="expiryClass">
              {{ isAdmin ? '永久' : (isPaid ? paidEndTime : '--') }}
            </span>
            <span class="user-stat-label">到期时间</span>
          </div>
        </div>
      </div>

      <!-- 会员状态卡片 -->
      <div v-if="isPaid && paidEndTime" class="member-card" :class="memberClass">
        <div class="member-status-bar">
          <div class="member-status-dot" :class="expiryDotClass"></div>
          <span class="member-status-text">{{ isExpired ? '已过期' : isExpiringSoon ? '即将到期' : '使用中' }}</span>
        </div>
        <template v-if="!isExpired">
          <div class="member-hero">
            <span class="member-days-num">{{ remainingDays }}</span>
            <span class="member-days-unit">天</span>
          </div>
          <span class="member-days-label">剩余可用天数</span>
          <div class="member-progress">
            <div class="member-progress-track">
              <div class="member-progress-fill" :class="progressClass" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <span class="member-progress-pct">{{ remainingPercent }}%</span>
          </div>
        </template>
        <div v-else class="member-expired-block">
          <span class="member-expired-title">会员已到期</span>
          <span class="member-expired-hint">联系客服续费</span>
        </div>
        <div class="member-guide-link" @click="showGuide = !showGuide">
          <span>会员使用指南</span><span class="guide-arrow">{{ showGuide ? '▲' : '▼' }}</span>
        </div>
        <div v-if="showGuide" class="member-guide">
          <div class="guide-block">
            <h4>一、核心权益与准则</h4>
            <p>双维度方案：组合串关 + 单场指数，足篮独立分开</p>
            <p>动态仓位体系：滚仓、止盈、止损、降仓、复位完整闭环</p>
            <p>四层赛事筛选：重心 · 精选 · 临场专属 · 专属</p>
            <p>实时数据推演：盘面、水位、筹码、机构意图实时监测</p>
            <p class="guide-divider"></p>
            <p>数据模型提高胜率，接受连错，吃准周期盈利</p>
            <p>严格按仓位执行，不私加仓、不倍投</p>
            <p>跟体系不凭感觉，短期看对错，长期看复利</p>
          </div>
          <div class="guide-block">
            <h4>二、两套复利打法</h4>
            <p class="guide-sub">单场指数 · 滚仓复利（稳健主仓）</p>
            <p>仓位标准：重心 8%-10%，精选 6%-8%，合集均注</p>
            <p>滚仓：盈利上浮10%，亏损降2%，连错2场暂停单场</p>
            <p>红线：单日亏损达6%立即停手</p>
            <p class="guide-sub">组合串关 · 复利滚仓</p>
            <p>标准：串关不做蚊子肉 | 滚仓：盈利上浮15%，亏损降2%，连错三天停手</p>
            <p class="guide-sub warn">统一风控红线</p>
            <p>日亏损8%强制停手 · 日盈利15%止盈落袋 · 单注不超过10% · 禁止倍投、追损、情绪化</p>
          </div>
          <div class="guide-block">
            <h4>三、服务流程</h4>
            <p>1、每日中午时段 — 赛事数据更新</p>
            <p>2、每日傍晚时段 — 筛选重心、精选、临场场次</p>
            <p>3、今日赛事页顶部状态栏查看最新定稿方案</p>
            <p>4、赛前1小时 — 高置信场次及时通知</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <div v-if="isAdmin" class="admin-action-row">
          <button class="action-btn admin-btn" @click="$router.push('/admin/recommendations')">推荐</button>
          <button class="action-btn admin-btn" @click="goToAchievement">战绩</button>
          <button class="action-btn admin-btn" @click="$router.push('/admin/membership')">用户管理</button>
        </div>
        <button class="action-btn pwd-btn" @click="openPwd">修改密码</button>
        <button class="action-btn logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </template>

    <!-- 修改密码弹窗 -->
    <Transition name="pwd-fade">
      <div v-if="showPwd" class="pwd-overlay" @click.self="closePwd">
        <div class="pwd-modal">
          <div class="pwd-modal-head">
            <span class="pwd-modal-title">修改密码</span>
            <button class="pwd-modal-close" @click="closePwd" aria-label="关闭">✕</button>
          </div>
          <div class="pwd-field">
            <label>新密码</label>
            <input v-model="newPwd" type="password" placeholder="6-20位，含字母和数字" maxlength="20" />
          </div>
          <div class="pwd-field">
            <label>确认新密码</label>
            <input v-model="confirmPwd" type="password" placeholder="再次输入新密码" maxlength="20" @keyup.enter="submitPwd" />
          </div>
          <p v-if="pwdError" class="pwd-error">{{ pwdError }}</p>
          <button class="pwd-submit" :disabled="pwdSubmitting" @click="submitPwd">
            {{ pwdSubmitting ? '提交中...' : '确认修改' }}
          </button>
          <p class="pwd-hint">修改后需用新密码重新登录</p>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import Loading from '../components/Loading.vue'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const user = ref(null)
const editing = ref(false)
const nicknameInput = ref('')
const showGuide = ref(false)

const isAdmin = computed(() => auth.isAdmin())
const isPaid = computed(() => user.value?.is_paid)

const cardClass = computed(() => isAdmin.value ? 'card-admin' : isPaid.value ? 'card-vip' : 'card-free')
const avatarClass = computed(() => isAdmin.value ? 'avatar-admin' : isPaid.value ? 'avatar-vip' : '')
const identityText = computed(() => isAdmin.value ? '管理员' : (isPaid.value ? '会员' : '非会员'))
const identityClass = computed(() => isAdmin.value ? 'id-admin' : isPaid.value ? 'id-vip' : 'id-free')

const paidEndTime = computed(() => fmt(user.value?.paid_end_time))
const registerTime = computed(() => fmt(user.value?.created_at))

function fmt(d) {
  if (!d) return null
  const t = new Date(d)
  return `${t.getFullYear()}年${t.getMonth()+1}月${t.getDate()}日`
}

const isExpired = computed(() => {
  const t = user.value?.paid_end_time; return t && new Date(t) < new Date()
})
const isExpiringSoon = computed(() => {
  const t = user.value?.paid_end_time
  if (!t) return false
  const days = Math.ceil((new Date(t) - new Date()) / 86400000)
  return days <= 7 && days > 0
})
const remainingDays = computed(() => {
  const t = user.value?.paid_end_time
  if (!t) return 0
  const ed = new Date(new Date(t).getFullYear(), new Date(t).getMonth(), new Date(t).getDate())
  const td = new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate())
  return Math.max(0, Math.round((ed - td) / 86400000))
})
const remainingPercent = computed(() => remainingDays.value > 365 ? 100 : Math.round((remainingDays.value / 365) * 100))
const progressPercent = computed(() => remainingDays.value > 365 ? 100 : remainingDays.value)
const memberClass = computed(() => isExpired.value ? 'member-expired' : isExpiringSoon.value ? 'member-expiring' : 'member-active')
const expiryDotClass = computed(() => isExpired.value ? 'dot-expired' : isExpiringSoon.value ? 'dot-expiring' : 'dot-active')
const progressClass = computed(() => isExpiringSoon.value ? 'fill-expiring' : 'fill-active')
const expiryClass = computed(() => isExpired.value ? 'stat-free' : '')

function startEdit() { nicknameInput.value = user.value?.nickname || ''; editing.value = true }
async function saveNickname() {
  if (!nicknameInput.value.trim()) { editing.value = false; return }
  try { await api.updateNickname(nicknameInput.value.trim()); user.value.nickname = nicknameInput.value.trim() } catch {}
  editing.value = false
}
function copyPhone() {
  const text = user.value?.phone || ''
  if (!text) return
  const done = () => alert('已复制')
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done).catch(() => { fallbackCopy(text); done() })
  } else {
    fallbackCopy(text); done()
  }
}
function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0'
  document.body.appendChild(ta); ta.select()
  try { document.execCommand('copy') } catch {}
  document.body.removeChild(ta)
}

async function goToAchievement() {
  try {
    const list = await api.getLatestAchievement()
    if (list?.id) { router.push(`/admin/achievements/edit/${list.id}`) }
    else { router.push('/admin/achievements/edit') }
  } catch { router.push('/admin/achievements/edit') }
}

function handleLogout() { auth.logout(); router.push('/') }

// ===== 修改密码 =====
const showPwd = ref(false)
const newPwd = ref('')
const confirmPwd = ref('')
const pwdError = ref('')
const pwdSubmitting = ref(false)
function openPwd() { showPwd.value = true; newPwd.value = ''; confirmPwd.value = ''; pwdError.value = '' }
function closePwd() { showPwd.value = false }
async function submitPwd() {
  pwdError.value = ''
  if (newPwd.value.length < 6 || newPwd.value.length > 20) { pwdError.value = '密码长度为 6-20 位'; return }
  if (!/[a-zA-Z]/.test(newPwd.value) || !/\d/.test(newPwd.value)) { pwdError.value = '密码需同时包含字母和数字'; return }
  if (newPwd.value !== confirmPwd.value) { pwdError.value = '两次密码输入不一致'; return }
  pwdSubmitting.value = true
  try {
    await api.changePassword(newPwd.value)
    showPwd.value = false
    alert('密码修改成功，请用新密码重新登录')
    auth.logout()
    router.push('/')
  } catch (e) {
    pwdError.value = e.message || '修改失败'
  } finally {
    pwdSubmitting.value = false
  }
}

// 登录/退出时刷新页面状态
watch(() => auth.token, async () => {
  loading.value = true
  if (auth.token) {
    await auth.fetchUser()
    user.value = auth.user
  } else {
    user.value = null
  }
  loading.value = false
})

onMounted(async () => {
  loading.value = true
  if (auth.token) {
    await auth.fetchUser()
    user.value = auth.user
  }
  loading.value = false
})
</script>

<style scoped>
.container { min-height: 100vh; background: #f3f4f8; padding: 16px 16px 48px; }
@media (min-width: 768px) { .container { padding: 24px 24px 48px; } }

/* ===== GUEST CARD ===== */
.guest-card {
  position: relative; background: var(--surface); border-radius: var(--radius-lg);
  margin-bottom: 20px; overflow: hidden; box-shadow: var(--shadow); border: 1px solid var(--border);
}
.guest-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--primary), #8B5CF6);
  z-index: 2;
}
.guest-body {
  position: relative; z-index: 1;
  display: flex; flex-direction: column; align-items: center;
  padding: 36px 24px 32px; text-align: center;
}
.guest-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  border: 3px solid #C7D2FE; box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px; overflow: hidden;
}
.guest-avatar-img { width: 68%; height: 68%; }
.guest-title { font-size: 20px; font-weight: 800; color: var(--text); margin-bottom: 8px; }
.guest-desc { font-size: 15px; color: var(--muted); line-height: 1.6; margin-bottom: 20px; }
.guest-login-btn {
  width: 100%; max-width: 280px; height: 48px;
  background: linear-gradient(135deg, #6366F1, #7C3AED);
  color: #fff; border-radius: 12px; font-size: 16px; font-weight: 700;
  border: none; cursor: pointer; box-shadow: 0 4px 16px rgba(99,102,241,0.3);
  transition: all 0.15s;
}
.guest-login-btn:active { transform: scale(0.97); }

/* ===== USER CARD ===== */
.user-card {
  position: relative; background: var(--surface); border-radius: var(--radius-lg);
  margin-bottom: 20px; overflow: hidden; box-shadow: var(--shadow); border: 1px solid var(--border);
}
.user-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--primary), #8B5CF6);
  z-index: 2;
}
.user-card.card-admin { border-color: #C7D2FE; }
.user-card.card-admin::before { background: linear-gradient(90deg, #6366F1, #A78BFA); }
.user-card.card-vip  { border-color: #BFDBFE; }

.user-card-bg { display: none; }

.user-card-body { position: relative; z-index: 1; display: flex; align-items: center; padding: 28px 24px 20px; }
.avatar-col { margin-right: 20px; flex-shrink: 0; }
.avatar {
  width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  border: 3px solid var(--border); background: var(--bg);
  box-shadow: var(--shadow-sm); overflow: hidden;
}
.avatar.avatar-admin { border-color: #C7D2FE; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
.avatar.avatar-vip  { border-color: #BFDBFE; box-shadow: 0 0 0 3px rgba(59,130,246,0.12); }
.avatar-img { width: 68%; height: 68%; }

.info-col { flex: 1; min-width: 0; }
.nickname-hero { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.nickname-text { font-size: 19px; font-weight: 800; color: var(--text); }
.nickname-edit { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: var(--primary-light); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s; }
.nickname-edit:hover { background: #C7D2FE; }
.edit-icon { font-size: 12px; color: var(--primary); }
.nickname-input-wrap { display: flex; align-items: center; gap: 8px; }
.nickname-input { width: 150px; height: 36px; padding: 0 12px; border-radius: 8px; background: var(--bg); color: var(--text); font-size: 16px; font-weight: 700; border: 1px solid var(--border); }
.nickname-confirm { font-size: 15px; color: var(--primary); font-weight: 700; cursor: pointer; }

.phone-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.phone-text { font-size: 14px; color: var(--muted); }
.phone-copy { padding: 2px 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 20px; font-size: 12px; color: var(--muted); cursor: pointer; transition: all 0.15s; }
.phone-copy:hover { border-color: var(--primary); color: var(--primary); }

.identity-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 14px; border-radius: 20px; }
.id-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.identity-tag span { font-size: 12px; font-weight: 700; }
.id-admin { background: var(--primary-light); border: 1px solid #C7D2FE; }
.id-admin .id-dot { background: var(--primary); } .id-admin span { color: var(--primary-hover); }
.id-vip { background: #FFFDF5; border: 1px solid #FDE68A; }
.id-vip .id-dot { background: #F59E0B; } .id-vip span { color: #B45309; }
.id-free { background: var(--bg); border: 1px solid var(--border); }
.id-free .id-dot { background: var(--muted); } .id-free span { color: var(--muted); }

.user-stats-row {
  position: relative; z-index: 1; display: flex; align-items: center;
  padding: 20px 24px; background: var(--bg); border-top: 1px solid var(--border-light);
}
.user-stat { flex: 1; text-align: center; display: flex; flex-direction: column; gap: 2px; }
.user-stat-value { font-size: 18px; font-weight: 700; color: var(--text); }
.user-stat-value.stat-free { color: var(--muted); }
.user-stat-label { font-size: 12px; color: var(--muted); font-weight: 500; }
.user-stat-divider { width: 1px; height: 32px; background: var(--border); }

/* ===== MEMBER CARD ===== */
.member-card {
  background: #fff; border-radius: 20px; margin-bottom: 20px; padding: 28px 24px;
  border: 1px solid #e8ecf2; box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; align-items: center; position: relative; overflow: hidden;
}
.member-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; border-radius: 20px 20px 0 0; }
.member-card.member-active::before { background: linear-gradient(90deg, #0ea06e, #34d399); }
.member-card.member-expiring::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.member-card.member-expired::before { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }

.member-status-bar { display: flex; align-items: center; gap: 8px; align-self: flex-start; margin-bottom: 20px; }
.member-status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.dot-active { background: #0ea06e; box-shadow: 0 0 8px rgba(14,160,110,0.4); }
.dot-expiring { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.4); }
.dot-expired { background: #94a3b8; }
.member-status-text { font-size: 14px; font-weight: 600; color: #475569; }

.member-hero { display: flex; align-items: baseline; gap: 4px; margin-bottom: 4px; }
.member-days-num { font-size: 64px; font-weight: 900; color: #1a1a2e; line-height: 1; letter-spacing: -0.02em; }
.member-days-unit { font-size: 26px; font-weight: 700; color: #64748b; }
.member-days-label { font-size: 14px; color: #94a3b8; font-weight: 500; margin-bottom: 24px; }

.member-progress { width: 100%; display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
.member-progress-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.member-progress-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.fill-active { background: linear-gradient(90deg, #0ea06e, #34d399); }
.fill-expiring { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.member-progress-pct { font-size: 14px; font-weight: 700; color: #94a3b8; min-width: 44px; text-align: right; flex-shrink: 0; }

.member-expired-block { text-align: center; padding: 16px 0 8px; }
.member-expired-title { display: block; font-size: 19px; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; }
.member-expired-hint { font-size: 14px; color: #94a3b8; }

.member-guide-link { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; padding-top: 16px; border-top: 1px solid #f1f5f9; font-size: 15px; font-weight: 600; color: #2563eb; cursor: pointer; }
.guide-arrow { font-size: 10px; color: #94a3b8; }
.member-guide { margin-top: 14px; padding-top: 14px; border-top: 1px solid #f1f5f9; text-align: left; }
.guide-block { margin-bottom: 16px; }
.guide-block h4 { font-size: 15px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.guide-block p { font-size: 14px; color: #475569; line-height: 1.8; margin-bottom: 2px; }
.guide-sub { font-weight: 600; color: #1e293b !important; margin-top: 8px; }
.guide-sub.warn { color: #dc2626 !important; }
.guide-divider { height: 1px; background: #e8ecf2; margin: 10px 0 !important; }

/* ===== BUTTONS ===== */
.action-buttons { display: flex; flex-direction: column; gap: 14px; }
.admin-action-row { display: flex; gap: 12px; }
.action-btn { display: flex; align-items: center; justify-content: center; padding: 16px 24px; border-radius: 14px; font-size: 16px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; }
.action-btn:active { transform: scale(0.97); }
.admin-btn { flex: 1; padding: 16px 8px; font-size: 15px; background: #eff6ff; color: #2563eb; border: 1.5px solid #bfdbfe; }
.admin-btn:hover { background: #dbeafe; }
.logout-btn { background: #fff; color: #94a3b8; border: 1.5px solid #e2e8f0; }
.logout-btn:hover { color: #64748b; border-color: #cbd5e1; }
.pwd-btn { background: #fff; color: var(--primary); border: 1.5px solid #C7D2FE; }
.pwd-btn:hover { background: var(--primary-light); border-color: var(--primary); }

/* ===== 修改密码弹窗 ===== */
.pwd-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15,23,42,0.4); backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.pwd-modal {
  width: 100%; max-width: 360px;
  background: #fff; border-radius: 16px;
  padding: 28px 26px 24px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.15);
  animation: pwd-pop 0.3s cubic-bezier(0.22,0.61,0.36,1) both;
}
@keyframes pwd-pop {
  from { opacity: 0; transform: translateY(16px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.pwd-modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; }
.pwd-modal-title { font-size: 18px; font-weight: 800; color: var(--text); }
.pwd-modal-close {
  width: 30px; height: 30px; padding: 0; border: none; border-radius: 50%;
  background: var(--bg); color: var(--muted); font-size: 15px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.pwd-modal-close:hover { background: #FEE2E2; color: #EF4444; }
.pwd-field { margin-bottom: 16px; }
.pwd-field label { display: block; font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.pwd-field input {
  width: 100%; height: 44px; padding: 0 14px;
  border: 1.5px solid var(--border); border-radius: 10px;
  font-size: 15px; background: var(--bg); outline: none;
  transition: border 0.15s;
}
.pwd-field input:focus { border-color: var(--primary); background: #fff; }
.pwd-error {
  font-size: 12px; color: #EF4444; margin-bottom: 14px;
  padding: 8px 12px; background: #FEF2F2; border-radius: 8px; border: 1px solid #FECACA;
}
.pwd-submit {
  width: 100%; height: 44px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #6366F1, #7C3AED);
  color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; transition: all 0.15s;
}
.pwd-submit:hover:not(:disabled) { box-shadow: 0 4px 16px rgba(99,102,241,0.3); transform: translateY(-1px); }
.pwd-submit:disabled { opacity: 0.4; cursor: not-allowed; }
.pwd-hint { font-size: 12px; color: var(--muted); text-align: center; margin-top: 14px; }

.pwd-fade-enter-active, .pwd-fade-leave-active { transition: opacity 0.2s ease; }
.pwd-fade-enter-from, .pwd-fade-leave-to { opacity: 0; }
</style>
