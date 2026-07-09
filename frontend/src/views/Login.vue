<template>
  <div class="login-page">
    <!-- 背景：神经网络节点图 -->
    <div class="bg-pattern" aria-hidden="true">
      <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" class="bg-svg">
        <!-- 节点 -->
        <g fill="none">
          <circle cx="120" cy="180" r="2.5" fill="#6366F1" opacity="0.12" />
          <circle cx="340" cy="90" r="2" fill="#8B5CF6" opacity="0.10" />
          <circle cx="580" cy="160" r="3" fill="#6366F1" opacity="0.10" />
          <circle cx="860" cy="100" r="2" fill="#8B5CF6" opacity="0.12" />
          <circle cx="1100" cy="200" r="2.5" fill="#6366F1" opacity="0.08" />
          <circle cx="1320" cy="140" r="2" fill="#8B5CF6" opacity="0.10" />
          <circle cx="200" cy="420" r="2" fill="#6366F1" opacity="0.08" />
          <circle cx="60" cy="620" r="2.5" fill="#8B5CF6" opacity="0.10" />
          <circle cx="280" cy="720" r="2" fill="#6366F1" opacity="0.08" />
          <circle cx="500" cy="680" r="3" fill="#8B5CF6" opacity="0.06" />
          <circle cx="750" cy="740" r="2" fill="#6366F1" opacity="0.08" />
          <circle cx="980" cy="620" r="2.5" fill="#8B5CF6" opacity="0.10" />
          <circle cx="1200" cy="700" r="2" fill="#6366F1" opacity="0.08" />
          <circle cx="1380" cy="480" r="3" fill="#8B5CF6" opacity="0.06" />
          <circle cx="1080" cy="400" r="2" fill="#6366F1" opacity="0.08" />
          <circle cx="400" cy="320" r="2.5" fill="#8B5CF6" opacity="0.06" />
          <circle cx="920" cy="280" r="2" fill="#6366F1" opacity="0.07" />
        </g>
        <!-- 连线 -->
        <g stroke="#6366F1" stroke-width="0.5" opacity="0.06">
          <line x1="120" y1="180" x2="340" y2="90" />
          <line x1="340" y1="90" x2="580" y2="160" />
          <line x1="580" y1="160" x2="860" y2="100" />
          <line x1="860" y1="100" x2="1100" y2="200" />
          <line x1="1100" y1="200" x2="1320" y2="140" />
          <line x1="200" y1="420" x2="400" y2="320" />
          <line x1="400" y1="320" x2="920" y2="280" />
          <line x1="920" y1="280" x2="1080" y2="400" />
          <line x1="120" y1="180" x2="200" y2="420" />
          <line x1="580" y1="160" x2="400" y2="320" />
          <line x1="860" y1="100" x2="1080" y2="400" />
          <line x1="200" y1="420" x2="60" y2="620" />
          <line x1="400" y1="320" x2="500" y2="680" />
          <line x1="500" y1="680" x2="280" y2="720" />
          <line x1="1080" y1="400" x2="980" y2="620" />
          <line x1="920" y1="280" x2="1200" y2="700" />
          <line x1="1200" y1="700" x2="1380" y2="480" />
          <line x1="60" y1="620" x2="280" y2="720" />
          <line x1="750" y1="740" x2="980" y2="620" />
          <line x1="980" y1="620" x2="1200" y2="700" />
        </g>
      </svg>
    </div>

    <!-- 卡片 -->
    <div class="login-card">
      <!-- 头部 -->
      <div class="login-header">
        <div class="logo-wrap">
          <div class="logo-ring"></div>
          <img class="login-logo" src="/logo.png" alt="AI竞界" />
        </div>
        <h1 class="login-brand">AI竞界</h1>
        <p class="login-slogan">AI 大模型驱动 · 专业赛事智能分析</p>
      </div>

      <!-- Tab -->
      <div class="tab-switch">
        <button class="tab-btn" :class="{ active: mode === 'login' }" @click="switchMode('login')">登录</button>
        <button class="tab-btn" :class="{ active: mode === 'register' }" @click="switchMode('register')">注册</button>
      </div>

      <!-- 表单 -->
      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="field">
          <label class="field-label">手机号</label>
          <input
            v-model="phone"
            type="tel"
            placeholder="输入手机号"
            maxlength="11"
            class="login-input"
          />
        </div>

        <div class="field">
          <label class="field-label">密码</label>
          <input
            v-model="password"
            :type="showPwd ? 'text' : 'password'"
            :placeholder="mode === 'register' ? '6-20位，含字母和数字' : '输入密码'"
            maxlength="20"
            class="login-input"
          />
        </div>

        <div v-if="mode === 'register'" class="field">
          <label class="field-label">确认密码</label>
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="再次输入密码"
            maxlength="20"
            class="login-input"
          />
        </div>

        <button class="login-btn" type="submit" :disabled="loading">
          <span v-if="loading" class="btn-dot-pulse"></span>
          <span v-else>{{ mode === 'login' ? '登 录' : '创建账号' }}</span>
        </button>

        <p v-if="error" class="login-error">{{ error }}</p>
        <p class="login-hint">
          {{ mode === 'register' ? '注册即可开启 AI 赛事智能分析' : '登录即可开启 AI 赛事智能分析' }}
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const mode = ref('login')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPwd = ref(false)
const loading = ref(false)
const error = ref('')

function switchMode(m) {
  mode.value = m
  error.value = ''
  confirmPassword.value = ''
}

function validate() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) return '请输入正确的11位手机号'
  if (password.value.length < 6 || password.value.length > 20) return '密码长度为 6-20 位'
  // 与后端规则一致：必须同时包含字母和数字
  if (!/[a-zA-Z]/.test(password.value) || !/\d/.test(password.value)) return '密码需同时包含字母和数字'
  if (mode.value === 'register' && password.value !== confirmPassword.value) return '两次密码输入不一致'
  return ''
}

async function handleSubmit() {
  const err = validate()
  if (err) { error.value = err; return }
  loading.value = true
  error.value = ''
  try {
    let res
    if (mode.value === 'register') {
      await api.register(phone.value, password.value)
      res = await api.login(phone.value, password.value)
    } else {
      res = await api.login(phone.value, password.value)
    }
    auth.setAuth(res.access_token, {
      ...res.user,
      isPaid: res.user.is_paid,
      role: res.user.role
    })
    router.push(route.query.redirect || '/')
  } catch (e) {
    // 手机号未注册 → 自动切到注册页，保留手机号，清掉错误提示
    if (e.message?.includes('未注册') || e.statusCode === 404) {
      mode.value = 'register'
      confirmPassword.value = ''
      error.value = ''
      return
    }
    error.value = e.message || (mode.value === 'login' ? '登录失败' : '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ===== 页面背景 ===== */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(175deg, #F8FAFC 0%, #EEF2FF 50%, #F5F3FF 100%);
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.bg-pattern {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-svg {
  width: 100%;
  height: 100%;
}

/* ===== 卡片 ===== */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  padding: 48px 40px 40px;
  box-shadow:
    0 1px 3px rgba(0,0,0,0.04),
    0 20px 60px rgba(99,102,241,0.06),
    0 0 0 0.5px rgba(99,102,241,0.04);
}

/* ===== 头部 ===== */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-wrap {
  position: relative;
  width: 76px;
  height: 76px;
  margin: 0 auto 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 脉冲光环 — AI 分析中的视觉线索 */
.logo-ring {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #6366F1, #8B5CF6, #A78BFA, #6366F1);
  opacity: 0.15;
  animation: ring-rotate 8s linear infinite;
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

.login-logo {
  position: relative;
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 12px rgba(99,102,241,0.1);
  z-index: 1;
}

.login-brand {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.06em;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.login-slogan {
  font-size: 13px;
  color: #94A3B8;
  letter-spacing: 0.04em;
}

/* ===== Tab 切换 ===== */
.tab-switch {
  display: flex;
  margin-bottom: 28px;
  background: #F1F5F9;
  border-radius: 10px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  height: 38px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #94A3B8;
  background: transparent;
  letter-spacing: 0.03em;
  transition: all 0.2s ease;
}

.tab-btn.active {
  color: #4F46E5;
  background: #FFFFFF;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 0 0 1px rgba(99,102,241,0.08);
}

/* ===== 表单 ===== */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  letter-spacing: 0.05em;
  padding-left: 2px;
}

.login-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 15px;
  color: #0F172A;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
}

.login-input::placeholder {
  color: #CBD5E1;
}

.login-input:focus {
  border-color: #6366F1;
  background: #FFFFFF;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
}

/* ===== 按钮 ===== */
.login-btn {
  position: relative;
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #6366F1 0%, #7C3AED 100%);
  color: #FFFFFF;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
  margin-top: 4px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25);
}

.login-btn:hover:not(:disabled) {
  box-shadow: 0 6px 24px rgba(99,102,241,0.35);
  transform: translateY(-1px);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-dot-pulse {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.3); }
}

/* ===== 提示 & 错误 ===== */
.login-error {
  font-size: 13px;
  color: #EF4444;
  text-align: center;
  padding: 8px 14px;
  background: #FEF2F2;
  border-radius: 8px;
  border: 1px solid #FECACA;
}

.login-hint {
  font-size: 12px;
  color: #94A3B8;
  text-align: center;
  line-height: 1.6;
}

/* ===== 响应式 ===== */
@media (max-width: 480px) {
  .login-card {
    padding: 36px 28px 32px;
    border-radius: 16px;
  }
  .login-brand {
    font-size: 24px;
  }
}
</style>
