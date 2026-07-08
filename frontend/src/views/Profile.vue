<template>
  <div class="container">
    <Loading v-if="loading" />

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
              {{ isAdmin ? '永久' : (isPaid ? paidEndTime : (isTrial ? trialEndTime : '--')) }}
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
            <p>1、每日中午时段 — 赛事数据更新，自主订阅</p>
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
        <button class="action-btn logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
const isTrial = computed(() => user.value?.is_trial_user && !user.value?.is_paid)

const cardClass = computed(() => isAdmin.value ? 'card-admin' : isPaid.value ? 'card-vip' : 'card-free')
const avatarClass = computed(() => isAdmin.value ? 'avatar-admin' : isPaid.value ? 'avatar-vip' : '')
const identityText = computed(() => isAdmin.value ? '管理员' : (isPaid.value ? '完整版用户' : (isTrial.value ? '体验版用户' : '基础版用户')))
const identityClass = computed(() => isAdmin.value ? 'id-admin' : (isPaid.value || isTrial.value) ? 'id-vip' : 'id-free')

const paidEndTime = computed(() => fmt(user.value?.paid_end_time))
const trialEndTime = computed(() => fmt(user.value?.trial_end_time))
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

function handleLogout() { auth.logout(); router.push('/login') }

onMounted(async () => { loading.value = true; await auth.fetchUser(); user.value = auth.user; loading.value = false })
</script>

<style scoped>
.container { min-height: 100vh; background: #f3f4f8; padding: 16px 16px 48px; }
@media (min-width: 768px) { .container { padding: 24px 24px 48px; } }

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
.nickname-text { font-size: 18px; font-weight: 800; color: var(--text); }
.nickname-edit { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: var(--primary-light); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all 0.15s; }
.nickname-edit:hover { background: #C7D2FE; }
.edit-icon { font-size: 12px; color: var(--primary); }
.nickname-input-wrap { display: flex; align-items: center; gap: 8px; }
.nickname-input { width: 150px; height: 34px; padding: 0 12px; border-radius: 8px; background: var(--bg); color: var(--text); font-size: 15px; font-weight: 700; border: 1px solid var(--border); }
.nickname-confirm { font-size: 14px; color: var(--primary); font-weight: 700; cursor: pointer; }

.phone-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.phone-text { font-size: 13px; color: var(--muted); }
.phone-copy { padding: 2px 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 20px; font-size: 11px; color: var(--muted); cursor: pointer; transition: all 0.15s; }
.phone-copy:hover { border-color: var(--primary); color: var(--primary); }

.identity-tag { display: inline-flex; align-items: center; gap: 6px; padding: 4px 14px; border-radius: 20px; }
.id-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.identity-tag span { font-size: 11px; font-weight: 700; }
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
.user-stat-value { font-size: 17px; font-weight: 700; color: var(--text); }
.user-stat-value.stat-free { color: var(--muted); }
.user-stat-label { font-size: 11px; color: var(--muted); font-weight: 500; }
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
.member-status-text { font-size: 13px; font-weight: 600; color: #475569; }

.member-hero { display: flex; align-items: baseline; gap: 4px; margin-bottom: 4px; }
.member-days-num { font-size: 64px; font-weight: 900; color: #1a1a2e; line-height: 1; letter-spacing: -0.02em; }
.member-days-unit { font-size: 26px; font-weight: 700; color: #64748b; }
.member-days-label { font-size: 13px; color: #94a3b8; font-weight: 500; margin-bottom: 24px; }

.member-progress { width: 100%; display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
.member-progress-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.member-progress-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.fill-active { background: linear-gradient(90deg, #0ea06e, #34d399); }
.fill-expiring { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.member-progress-pct { font-size: 14px; font-weight: 700; color: #94a3b8; min-width: 44px; text-align: right; flex-shrink: 0; }

.member-expired-block { text-align: center; padding: 16px 0 8px; }
.member-expired-title { display: block; font-size: 18px; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; }
.member-expired-hint { font-size: 13px; color: #94a3b8; }

.member-guide-link { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; padding-top: 16px; border-top: 1px solid #f1f5f9; font-size: 14px; font-weight: 600; color: #2563eb; cursor: pointer; }
.guide-arrow { font-size: 10px; color: #94a3b8; }
.member-guide { margin-top: 14px; padding-top: 14px; border-top: 1px solid #f1f5f9; text-align: left; }
.guide-block { margin-bottom: 16px; }
.guide-block h4 { font-size: 14px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.guide-block p { font-size: 13px; color: #475569; line-height: 1.8; margin-bottom: 2px; }
.guide-sub { font-weight: 600; color: #1e293b !important; margin-top: 8px; }
.guide-sub.warn { color: #dc2626 !important; }
.guide-divider { height: 1px; background: #e8ecf2; margin: 10px 0 !important; }

/* ===== BUTTONS ===== */
.action-buttons { display: flex; flex-direction: column; gap: 14px; }
.admin-action-row { display: flex; gap: 12px; }
.action-btn { display: flex; align-items: center; justify-content: center; padding: 16px 24px; border-radius: 14px; font-size: 15px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; }
.action-btn:active { transform: scale(0.97); }
.admin-btn { flex: 1; padding: 16px 8px; font-size: 14px; background: #eff6ff; color: #2563eb; border: 1.5px solid #bfdbfe; }
.admin-btn:hover { background: #dbeafe; }
.logout-btn { background: #fff; color: #94a3b8; border: 1.5px solid #e2e8f0; }
.logout-btn:hover { color: #64748b; border-color: #cbd5e1; }
</style>
