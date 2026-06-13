import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('opspilot_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const status = err.response?.status
    const message = err.response?.data?.detail || err.message
    if (status === 401) {
      localStorage.removeItem('opspilot_token')
      router.push('/login')
    } else {
      ElMessage.error(message || 'Request failed')
    }
    return Promise.reject(err)
  }
)

export default request
