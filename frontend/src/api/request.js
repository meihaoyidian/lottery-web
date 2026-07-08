import axios from 'axios'

const BASE_URL = import.meta.env.DEV ? '/api/v1' : 'https://sportlens.online/api/v1'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 8000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器：自动带 token
http.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  res => res,
  error => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || error.response?.data?.message || '请求失败'

    // 401 且非登录接口 → 清登录态
    if (status === 401 && !error.config.url.includes('/auth/')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }

    return Promise.reject({ statusCode: status || 0, message: msg, data: error.response?.data })
  }
)

export default http
