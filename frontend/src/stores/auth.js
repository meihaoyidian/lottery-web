import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  function setAuth(t, u) {
    token.value = t
    user.value = u
    localStorage.setItem('token', t)
    localStorage.setItem('user', JSON.stringify(u))
  }

  function restore() {
    const t = localStorage.getItem('token')
    const u = JSON.parse(localStorage.getItem('user') || 'null')
    if (t) {
      token.value = t
      user.value = u
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchUser() {
    try {
      const res = await api.getSubscription()
      user.value = {
        ...user.value,
        ...res,
        isPaid: res.is_paid,
        isTrial: res.is_trial,
        role: res.role
      }
      localStorage.setItem('user', JSON.stringify(user.value))
    } catch (e) {
      if (e.statusCode === 401) logout()
    }
  }

  const isPaidUser = () => user.value?.isPaid || user.value?.role === 'admin'
  const isTrial = () => user.value?.isTrial && !user.value?.isPaid
  const isAdmin = () => user.value?.role === 'admin'

  return { token, user, setAuth, restore, logout, fetchUser, isPaidUser, isTrial, isAdmin }
})
