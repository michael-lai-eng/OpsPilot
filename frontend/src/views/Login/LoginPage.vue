<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-icon">🚀</span>
        <h1>OpsPilot</h1>
        <p>DevOps Operations Platform</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent="submit">
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" placeholder="Enter username" size="large"
                    prefix-icon="User" autofocus />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="form.password" type="password" placeholder="Enter password"
                    size="large" prefix-icon="Lock" show-password @keyup.enter="submit" />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading"
                   style="width:100%;margin-top:8px" @click="submit">
          Sign In
        </el-button>
      </el-form>

      <p class="login-hint">Default: admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: 'Username is required' }],
  password: [{ required: true, message: 'Password is required' }],
}

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}
.login-card {
  width: 380px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 36px 32px;
}
.login-brand {
  text-align: center;
  margin-bottom: 28px;
  .brand-icon { font-size: 40px; }
  h1 { font-size: 24px; font-weight: 700; margin-top: 8px; }
  p { color: var(--color-muted); font-size: 13px; margin-top: 4px; }
}
.login-hint { text-align: center; color: var(--color-muted); font-size: 12px; margin-top: 16px; }
</style>
