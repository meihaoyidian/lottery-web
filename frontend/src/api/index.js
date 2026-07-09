import http from './request'

const api = {
  // ===== 认证 =====
  login(phone, password) {
    return http.post('/auth/login', { phone, password }).then(r => r.data)
  },
  register(phone, password, nickname) {
    return http.post('/auth/register', { phone, password, nickname }).then(r => r.data)
  },

  // ===== 用户 =====
  getSubscription() {
    return http.get('/users/me/subscription').then(r => r.data)
  },
  updateNickname(nickname) {
    return http.put('/users/me/nickname', { nickname }).then(r => r.data)
  },
  changePassword(new_password) {
    return http.post('/users/change-password', { new_password }).then(r => r.data)
  },

  // ===== 推荐列表 =====
  getRecommendations(params) {
    return http.get('/recommendations', { params }).then(r => r.data)
  },
  getTodayStatus() {
    return http.get('/recommendations/today-status').then(r => r.data)
  },
  getAdminRecommendations(params) {
    return http.get('/recommendations/admin/all', { params }).then(r => r.data)
  },
  createRecommendation(data) {
    return http.post('/recommendations', data).then(r => r.data)
  },
  getRecommendationDetail(id) {
    return http.get(`/recommendations/${id}`).then(r => r.data)
  },
  updateRecommendation(id, data) {
    return http.put(`/recommendations/${id}`, data).then(r => r.data)
  },
  deleteRecommendation(id) {
    return http.delete(`/recommendations/${id}`).then(r => r.data)
  },
  toggleConfirm(id) {
    return http.post(`/recommendations/${id}/toggle-confirm`).then(r => r.data)
  },
  markResult(id, data) {
    return http.post(`/recommendations/${id}/complete`, data).then(r => r.data)
  },
  getViewRecords(id, params) {
    return http.get(`/view-records/recommendation/${id}`, { params }).then(r => r.data)
  },

  // ===== 历史战绩 =====
  getHistory(params) {
    return http.get('/history', { params }).then(r => r.data)
  },
  getStatistics(params) {
    return http.get('/history/statistics', { params }).then(r => r.data)
  },
  getMonthlyStatistics(params) {
    return http.get('/history/monthly-statistics', { params }).then(r => r.data)
  },
  getHighlights() {
    return http.get('/history/highlights').then(r => r.data)
  },

  // ===== 昨日战绩 =====
  getLatestAchievement(params) {
    return http.get('/daily-achievements/latest', { params }).then(r => r.data)
  },
  getAchievements(params) {
    return http.get('/daily-achievements', { params }).then(r => r.data)
  },
  getAchievement(id) {
    return http.get(`/daily-achievements/${id}`).then(r => r.data)
  },
  createAchievement(data) {
    return http.post('/daily-achievements', data).then(r => r.data)
  },
  updateAchievement(id, data) {
    return http.put(`/daily-achievements/${id}`, data).then(r => r.data)
  },
  deleteAchievement(id) {
    return http.delete(`/daily-achievements/${id}`).then(r => r.data)
  },

  // ===== 热度 =====
  getSocialProof() {
    return http.get('/stats/social-proof').then(r => r.data)
  },

  // ===== 用户管理（admin） =====
  getUsers(params) {
    return http.get('/admin/users', { params }).then(r => r.data)
  },
  searchUser(phone) {
    return http.post('/users/search', { phone }).then(r => r.data)
  },
  setMembership(user_id, days) {
    return http.post('/users/membership', { user_id, days, is_paid: true }).then(r => r.data)
  },
  cancelMembership(user_id) {
    return http.post('/users/membership', { user_id, days: 0, is_paid: false }).then(r => r.data)
  },
  resetPassword(user_id) {
    return http.post('/users/reset-password', { user_id }).then(r => r.data)
  }
}

export default api
