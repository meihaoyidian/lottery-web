<template>
  <div class="page">
    <Loading v-if="loading" />

    <div v-else class="container">
      <!-- 用户卡片 -->
      <div class="user-card" :class="userCardClass">
        <div class="user-card-bg"></div>
        <div class="user-card-body">
          <div class="avatar-col">
            <div class="avatar" :class="avatarClass">
              <img class="avatar-img" src="/logo.png" alt="logo" />
            </div>
          </div>
          <div class="info-col">
            <div class="nickname-hero">
              <span class="nickname-hero-text" v-if="!editing">{{ user?.nickname || '点击设置昵称' }}</span>
              <span class="nickname-hero-edit" v-if="!editing" @click="startEdit">✎</span>
              <div v-else class="nickname-edit">
                <input v-model="nicknameInput" class="nickname-input" maxlength="20" @keyup.enter="saveNickname" />
                <span class="nickname-confirm" @click="saveNickname">确定</span>
              </div>
            </div>
            <div class="phone-row">
              <span class="phone-text">{{ user?.phone || '--' }}</span>
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
        <div v-if="!isExpired" class="member-detail">
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
        </div>
        <div v-else class="member-expired-block">
          <span class="member-expired-title">会员已到期</span>
          <span class="member-expired-hint">联系客服续费</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button class="action-btn logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </div>
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

const loading = ref(false)
const user = ref(null)
const editing = ref(false)
const nicknameInput = ref('')

const isAdmin = computed(() => auth.isAdmin())
const isPaid = computed(() => user.value?.is_paid)
const isTrial = computed(() => user.value?.is_trial_user && !user.value?.is_paid)

const userCardClass = computed(() => isAdmin.value ? 'card-admin' : isPaid.value ? 'card-vip' : 'card-free')
const avatarClass = computed(() => isAdmin.value ? 'avatar-admin' : isPaid.value ? 'avatar-vip' : '')
const identityText = computed(() => isAdmin.value ? '管理员' : (isPaid.value ? '完整版用户' : (isTrial.value ? '体验版用户' : '基础版用户')))
const identityClass = computed(() => isAdmin.value ? 'id-admin' : (isPaid.value || isTrial.value) ? 'id-vip' : 'id-free')

const paidEndTime = computed(() => formatDate(user.value?.paid_end_time))
const trialEndTime = computed(() => formatDate(user.value?.trial_end_time))
const registerTime = computed(() => formatDate(user.value?.created_at))

const isExpired = computed(() => {
  const t = user.value?.paid_end_time
  return t && new Date(t) < new Date()
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
  return Math.max(0, Math.ceil((new Date(t) - new Date()) / 86400000))
})
const remainingPercent = computed(() => {
  if (!user.value?.paid_end_time || !user.value?.paid_start_time) return 0
  const total = (new Date(user.value.paid_end_time) - new Date(user.value.paid_start_time)) / 86400000
  return total > 0 ? Math.round((remainingDays.value / total) * 100) : 0
})
const progressPercent = computed(() => Math.min(100, remainingDays.value > 365 ? 100 : remainingDays.value))
const memberClass = computed(() => isExpired.value ? 'member-expired' : isExpiringSoon.value ? 'member-expiring' : 'member-active')
const expiryDotClass = computed(() => isExpired.value ? 'dot-expired' : isExpiringSoon.value ? 'dot-expiring' : 'dot-active')
const progressClass = computed(() => isExpiringSoon.value ? 'fill-expiring' : 'fill-active')
const expiryClass = computed(() => isExpired.value ? 'stat-free' : '')

function formatDate(d) {
  if (!d) return null
  return new Date(d).toLocaleDateString('zh-CN')
}

function startEdit() {
  nicknameInput.value = user.value?.nickname || ''
  editing.value = true
}

async function saveNickname() {
  if (nicknameInput.value.trim()) {
    try {
      await api.updateProfile({ nickname: nicknameInput.value.trim() })
      user.value.nickname = nicknameInput.value.trim()
    } catch { /* ignore */ }
  }
  editing.value = false
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  await auth.fetchUser()
  user.value = auth.user
})
</script>

<style scoped>
.container { max-width: 480px; margin: 0 auto; padding: 24px; }

/* ===== USER CARD ===== */
.user-card {
  position: relative; background: #fff; border-radius: 24px; margin-bottom: 20px;
  overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.06); border: 1px solid #e8ecf2;
}
.user-card-bg {
  position: absolute; top: 0; left: 0; right: 0; height: 120px;
  background: linear-gradient(160deg, #0f172a, #1e3a8a, #2563eb);
}
.card-admin .user-card-bg { background: linear-gradient(160deg, #1e1b4b, #3730a3, #6366f1); }
.card-admin { border-color: #c7d2fe; }
.card-vip { border-color: #bfdbfe; }

.user-card-body { position: relative; z-index: 1; display: flex; align-items: center; padding: 32px 28px 24px; }
.avatar-col { margin-right: 24px; flex-shrink: 0; }
.avatar {
  width: 72px; height: 72px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  border: 3px solid rgba(255,255,255,0.9); background: #fff;
  box-shadow: 0 6px 24px rgba(0,0,0,0.18); overflow: hidden;
}
.avatar-img { width: 68%; height: 68%; }
.avatar-admin { border-color: #c7d2fe; box-shadow: 0 0 0 3px rgba(99,102,241,0.3), 0 6px 24px rgba(0,0,0,0.15); }
.avatar-vip { border-color: #bfdbfe; box-shadow: 0 0 0 3px rgba(37,99,235,0.2), 0 6px 24px rgba(0,0,0,0.12); }

.info-col { flex: 1; min-width: 0; }
.nickname-hero { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.nickname-hero-text { font-size: 20px; font-weight: 800; color: #fff; }
.nickname-hero-edit { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: rgba(255,255,255,0.12); display: flex; align-items: center; justify-content: center; font-size: 12px; color: rgba(255,255,255,0.55); cursor: pointer; }
.nickname-edit { display: flex; align-items: center; gap: 10px; }
.nickname-input { width: 160px; height: 36px; padding: 0 12px; border-radius: 8px; background: rgba(255,255,255,0.15); color: #fff; font-size: 16px; font-weight: 700; border: 1px solid rgba(255,255,255,0.2); }
.nickname-confirm { font-size: 14px; color: #fbbf24; font-weight: 700; cursor: pointer; }

.phone-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.phone-text { font-size: 14px; color: rgba(255,255,255,0.55); }

.identity-tag { display: inline-flex; align-items: center; gap: 8px; padding: 5px 16px; border-radius: 20px; }
.id-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; display: inline-block; }
.identity-tag span { font-size: 11px; font-weight: 700; }
.id-admin { background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); }
.id-admin .id-dot { background: #c7d2fe; }
.id-admin span { color: #e0e7ff; }
.id-vip { background: rgba(251,191,36,0.15); border: 1px solid rgba(251,191,36,0.3); }
.id-vip .id-dot { background: #fbbf24; }
.id-vip span { color: #fde68a; }
.id-free { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); }
.id-free .id-dot { background: rgba(255,255,255,0.4); }
.id-free span { color: rgba(255,255,255,0.55); }

.user-stats-row {
  position: relative; z-index: 1; display: flex; align-items: center;
  padding: 20px 28px; background: linear-gradient(to bottom, rgba(255,255,255,0.03), #fff);
  border-top: 1px solid rgba(0,0,0,0.04);
}
.user-stat { flex: 1; text-align: center; display: flex; flex-direction: column; gap: 2px; }
.user-stat-value { font-size: 16px; font-weight: 700; color: #1a1a2e; }
.user-stat-value.stat-free { color: #64748b; }
.user-stat-label { font-size: 11px; color: #94a3b8; font-weight: 500; }
.user-stat-divider { width: 1px; height: 36px; background: #e8ecf2; }

/* ===== MEMBER CARD ===== */
.member-card {
  background: #fff; border-radius: 20px; margin-bottom: 20px;
  padding: 28px; border: 1px solid #e8ecf2; box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  display: flex; flex-direction: column; align-items: center; position: relative; overflow: hidden;
}
.member-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 5px; border-radius: 20px 20px 0 0;
}
.member-active::before { background: linear-gradient(90deg, #0ea06e, #34d399); }
.member-expiring::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.member-expired::before { background: linear-gradient(90deg, #94a3b8, #cbd5e1); }

.member-status-bar { display: flex; align-items: center; gap: 10px; align-self: flex-start; margin-bottom: 24px; }
.member-status-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.dot-active { background: #0ea06e; box-shadow: 0 0 8px rgba(14,160,110,0.4); }
.dot-expiring { background: #f59e0b; box-shadow: 0 0 8px rgba(245,158,11,0.4); }
.dot-expired { background: #94a3b8; }
.member-status-text { font-size: 14px; font-weight: 600; color: #475569; }

.member-hero { display: flex; align-items: baseline; gap: 4px; margin-bottom: 4px; }
.member-days-num { font-size: 56px; font-weight: 900; color: #1a1a2e; line-height: 1; }
.member-days-unit { font-size: 24px; font-weight: 700; color: #64748b; }
.member-days-label { font-size: 14px; color: #94a3b8; font-weight: 500; margin-bottom: 24px; }

.member-progress { width: 100%; display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.member-progress-track { flex: 1; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.member-progress-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.fill-active { background: linear-gradient(90deg, #0ea06e, #34d399); }
.fill-expiring { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.member-progress-pct { font-size: 14px; font-weight: 700; color: #94a3b8; width: 48px; text-align: right; flex-shrink: 0; }

.member-expired-block { text-align: center; padding: 20px 0 12px; }
.member-expired-title { display: block; font-size: 20px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; }
.member-expired-hint { font-size: 14px; color: #94a3b8; }

/* ===== ACTION ===== */
.action-buttons { display: flex; flex-direction: column; gap: 16px; }
.action-btn { display: flex; align-items: center; justify-content: center; padding: 24px 32px; border-radius: 24px; font-size: 17px; font-weight: 600; cursor: pointer; }
.logout-btn { background: #fff; color: #94a3b8; border: 2px solid #e2e8f0; }
.logout-btn:active { transform: scale(0.97); }
</style>
