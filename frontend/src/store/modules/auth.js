import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('opspilot_token') || '',
    user: JSON.parse(localStorage.getItem('opspilot_user') || 'null'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
    isOperator: (s) => ['admin', 'operator'].includes(s.user?.role),
    initials: (s) => (s.user?.full_name || s.user?.username || 'U').slice(0, 2).toUpperCase(),
  },
  actions: {
    async login(username, password) {
      const data = await authApi.login(username, password)
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('opspilot_token', data.access_token)
      localStorage.setItem('opspilot_user', JSON.stringify(data.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('opspilot_token')
      localStorage.removeItem('opspilot_user')
    },
  },
})
