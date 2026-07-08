import http from './request'

const api = {
  // ===== 认证 =====
  sendCode(phone) {
    return http.post('/auth/web/send-code', { phone }).then(r => r.data)
  },
  webLogin(phone, code) {
    return http.post('/auth/web/login', { phone, code }).then(r => r.data)
  },

  // ===== 用户 =====
  getSubscription() {
    return http.get('/users/me/subscription').then(r => r.data)
  },
  updateProfile(data) {
    return http.put('/users/me/profile', data).then(r => r.data)
  },

  // ===== 推荐列表 =====
  getRecommendations(params) {
    return http.get('/recommendations', { params }).then(r => r.data)
  },
  getTodayStatus() {
    return http.get('/recommendations/today-status').then(r => r.data)
  },
  createRecommendation(data) {
    return http.post('/admin/recommendations', data).then(r => r.data)
  },
  updateRecommendation(id, data) {
    return http.put(`/admin/recommendations/${id}`, data).then(r => r.data)
  },
  toggleConfirm(id) {
    return http.post(`/admin/recommendations/${id}/toggle-confirm`).then(r => r.data)
  },
  markResult(id, data) {
    return http.put(`/admin/recommendations/${id}/result`, data).then(r => r.data)
  },

  // ===== 历史战绩 =====
  getHistory(params) {
    return http.get('/history', { params }).then(r => r.data)
  },
  getStatistics() {
    return http.get('/history/statistics').then(r => r.data)
  },
  getMonthlyStatistics() {
    return http.get('/history/monthly-statistics').then(r => r.data)
  },
  getHighlights() {
    return http.get('/history/highlights').then(r => r.data)
  },

  // ===== 昨日战绩 =====
  getLatestAchievement() {
    return http.get('/daily-achievements/latest').then(r => r.data)
  },
  updateAchievement(id, data) {
    return http.put(`/admin/daily-achievements/${id}`, data).then(r => r.data)
  },

  // ===== 热度 =====
  getSocialProof() {
    return http.get('/stats/social-proof').then(r => r.data)
  },

  // ===== 用户管理（admin） =====
  getUsers(params) {
    return http.get('/admin/users', { params }).then(r => r.data)
  },
  updateMembership(userId, data) {
    return http.put(`/admin/users/${userId}/membership`, data).then(r => r.data)
  }
}

export default api
