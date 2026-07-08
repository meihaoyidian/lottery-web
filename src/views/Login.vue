<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <img class="login-logo" src="/logo.png" alt="logo" />
        <h1 class="login-brand">AI竞界</h1>
        <p class="login-slogan">专业赛事分析</p>
      </div>

      <div class="login-form">
        <div class="input-group">
          <input
            v-model="phone"
            type="tel"
            placeholder="请输入手机号"
            maxlength="11"
            class="login-input"
          />
        </div>

        <div class="input-group code-group">
          <input
            v-model="code"
            type="tel"
            placeholder="验证码"
            maxlength="4"
            class="login-input code-input"
            @keyup.enter="handleLogin"
          />
          <button class="send-code-btn" :disabled="countdown > 0" @click="sendCode">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </div>

        <button class="login-btn" :disabled="loading" @click="handleLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <p v-if="error" class="login-error">{{ error }}</p>
        <p class="login-hint">新用户自动注册并赠送 1 天体验</p>
      </div>
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

const phone = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const countdown = ref(0)

function validatePhone(p) {
  return /^1[3-9]\d{9}$/.test(p)
}

async function sendCode() {
  if (!validatePhone(phone.value)) {
    error.value = '请输入正确的手机号'
    return
  }
  error.value = ''
  try {
    await api.sendCode(phone.value)
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    error.value = e.message || '发送失败'
  }
}

async function handleLogin() {
  if (!validatePhone(phone.value)) {
    error.value = '请输入正确的手机号'
    return
  }
  if (!code.value) {
    error.value = '请输入验证码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await api.webLogin(phone.value, code.value)
    auth.setAuth(res.access_token, {
      ...res.user,
      isPaid: res.user.is_paid,
      isTrial: res.user.is_trial_user,
      role: res.user.role
    })
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #0f172a, #1e3a8a, #2563eb);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 380px;
  background: #fff;
  border-radius: 20px;
  padding: 40px 32px 36px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  margin-bottom: 12px;
  background: #f0f4ff;
}

.login-brand {
  font-size: 28px;
  font-weight: 800;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.login-slogan {
  font-size: 14px;
  color: #94a3b8;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-group {
  position: relative;
}

.login-input {
  width: 100%;
  height: 52px;
  padding: 0 16px;
  border: 1px solid #e8ecf2;
  border-radius: 12px;
  font-size: 16px;
  color: #1a1a2e;
  background: #f8fafc;
  transition: border-color 0.2s;
}

.login-input:focus {
  border-color: #2563eb;
  background: #fff;
}

.code-group {
  display: flex;
  gap: 12px;
}

.code-input {
  flex: 1;
}

.send-code-btn {
  flex-shrink: 0;
  height: 52px;
  padding: 0 16px;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.send-code-btn:disabled {
  color: #94a3b8;
  background: #f1f5f9;
  border-color: #e8ecf2;
}

.login-btn {
  width: 100%;
  height: 52px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 6px 20px rgba(37,99,235,0.3);
}

.login-btn:disabled {
  opacity: 0.6;
}

.login-btn:active {
  transform: scale(0.98);
}

.login-error {
  font-size: 14px;
  color: #dc2626;
  text-align: center;
}

.login-hint {
  font-size: 13px;
  color: #94a3b8;
  text-align: center;
}
</style>
