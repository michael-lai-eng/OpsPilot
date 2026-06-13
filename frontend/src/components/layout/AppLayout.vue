<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <span class="logo-icon">🚀</span>
        <span class="logo-text">OpsPilot</span>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section-title">Overview</div>
        <router-link class="nav-item" to="/dashboard">
          <el-icon class="nav-icon"><Odometer /></el-icon> Dashboard
        </router-link>

        <div class="nav-section-title" style="margin-top:12px">CI/CD</div>
        <router-link class="nav-item" to="/pipelines">
          <el-icon class="nav-icon"><Connection /></el-icon> Pipelines
        </router-link>
        <router-link class="nav-item" to="/deployments">
          <el-icon class="nav-icon"><Upload /></el-icon> Deployments
        </router-link>

        <div class="nav-section-title" style="margin-top:12px">Operations</div>
        <router-link class="nav-item" to="/tasks">
          <el-icon class="nav-icon"><Operation /></el-icon> Task Automation
        </router-link>
        <router-link class="nav-item" to="/alerts">
          <el-icon class="nav-icon"><Bell /></el-icon>
          Alerts
          <span v-if="alertCount > 0" class="alert-dot">{{ alertCount }}</span>
        </router-link>

        <div class="nav-section-title" style="margin-top:12px">Assets</div>
        <router-link class="nav-item" to="/servers">
          <el-icon class="nav-icon"><Monitor /></el-icon> Servers
        </router-link>
      </nav>

      <div class="sidebar-user" @click="handleUserMenu">
        <div class="user-avatar">{{ authStore.initials }}</div>
        <div class="user-info">
          <div class="user-name">{{ authStore.user?.username }}</div>
          <div class="user-role">{{ authStore.user?.role }}</div>
        </div>
        <el-icon><MoreFilled /></el-icon>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-layout">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import { alertApi } from '@/api'

const authStore = useAuthStore()
const router = useRouter()
const alertCount = ref(0)

onMounted(async () => {
  try {
    const s = await alertApi.summary()
    alertCount.value = s.firing || 0
  } catch {}
})

async function handleUserMenu() {
  try {
    await ElMessageBox.confirm('Logout from OpsPilot?', 'Confirm', { type: 'warning' })
    authStore.logout()
    router.push('/login')
  } catch {}
}
</script>

<style scoped>
.app-shell { display: flex; min-height: 100vh; }
.alert-dot {
  margin-left: auto;
  background: var(--color-danger);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  padding: 1px 6px;
  font-weight: 600;
}
</style>
