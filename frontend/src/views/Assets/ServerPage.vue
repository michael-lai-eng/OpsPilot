<template>
  <div>
    <div class="page-header">
      <h1>Servers</h1>
      <p>Infrastructure asset inventory</p>
    </div>
    <div class="page-content">
      <!-- Summary -->
      <div class="stat-cards" style="grid-template-columns:repeat(4,1fr)">
        <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">{{ summary.total }}</div></div>
        <div class="stat-card success"><div class="stat-label">Online</div><div class="stat-value">{{ summary.online }}</div></div>
        <div class="stat-card danger"><div class="stat-label">Offline</div><div class="stat-value">{{ summary.offline }}</div></div>
        <div class="stat-card warning"><div class="stat-label">Maintenance</div><div class="stat-value">{{ summary.maintenance }}</div></div>
      </div>

      <!-- Filters + Add -->
      <div style="display:flex;gap:10px;margin-bottom:16px;align-items:center">
        <el-select v-model="filterEnv" placeholder="Environment" clearable size="small"
                   @change="loadServers" style="width:140px">
          <el-option label="dev" value="dev" />
          <el-option label="staging" value="staging" />
          <el-option label="prod" value="prod" />
        </el-select>
        <el-select v-model="filterRole" placeholder="Role" clearable size="small"
                   @change="loadServers" style="width:130px">
          <el-option label="app" value="app" />
          <el-option label="db" value="db" />
          <el-option label="cache" value="cache" />
          <el-option label="lb" value="lb" />
          <el-option label="k8s-node" value="k8s-node" />
        </el-select>
        <div style="flex:1" />
        <button class="btn btn-primary" @click="showAdd = true">
          <el-icon><Plus /></el-icon> Add Server
        </button>
      </div>

      <div class="card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th><th>IP</th><th>OS</th><th>Specs</th>
              <th>Env</th><th>Role</th><th>Provider</th><th>Status</th><th>Last Seen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in servers" :key="s.id">
              <td style="font-weight:600">{{ s.name }}</td>
              <td style="font-family:monospace;font-size:12px">{{ s.ip }}</td>
              <td style="font-size:12px">{{ s.os }}</td>
              <td style="font-size:12px;color:var(--color-muted)">
                {{ s.cpu_cores }}C / {{ s.memory_gb }}GB
              </td>
              <td><span class="badge info">{{ s.environment }}</span></td>
              <td style="font-size:12px">{{ s.role }}</td>
              <td style="font-size:12px;color:var(--color-muted)">{{ s.provider || '—' }}</td>
              <td><span :class="['badge', s.status]">{{ s.status }}</span></td>
              <td style="font-size:12px;color:var(--color-muted)">{{ fromNow(s.last_seen) }}</td>
            </tr>
            <tr v-if="!servers.length">
              <td colspan="9" style="text-align:center;color:var(--color-muted);padding:32px">No servers</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add server dialog -->
    <el-dialog v-model="showAdd" title="Add Server" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="Name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Hostname"><el-input v-model="form.hostname" /></el-form-item>
        <el-form-item label="IP"><el-input v-model="form.ip" /></el-form-item>
        <el-form-item label="OS"><el-input v-model="form.os" placeholder="Ubuntu 22.04" /></el-form-item>
        <el-form-item label="CPU Cores"><el-input-number v-model="form.cpu_cores" :min="1" /></el-form-item>
        <el-form-item label="Memory (GB)"><el-input-number v-model="form.memory_gb" :min="0.5" :step="0.5" /></el-form-item>
        <el-form-item label="Environment">
          <el-select v-model="form.environment" style="width:100%">
            <el-option label="dev" value="dev" />
            <el-option label="staging" value="staging" />
            <el-option label="prod" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item label="Role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="app" value="app" />
            <el-option label="db" value="db" />
            <el-option label="cache" value="cache" />
            <el-option label="lb" value="lb" />
            <el-option label="k8s-node" value="k8s-node" />
          </el-select>
        </el-form-item>
        <el-form-item label="Provider">
          <el-select v-model="form.provider" style="width:100%">
            <el-option label="AWS" value="aws" />
            <el-option label="GCP" value="gcp" />
            <el-option label="Azure" value="azure" />
            <el-option label="On-Premise" value="onprem" />
          </el-select>
        </el-form-item>
        <el-form-item label="Region"><el-input v-model="form.region" placeholder="us-east-1" /></el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showAdd = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="addServer">Add</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { serverApi } from '@/api'

dayjs.extend(relativeTime)

const servers = ref([])
const summary = ref({ total: 0, online: 0, offline: 0, maintenance: 0 })
const filterEnv = ref('')
const filterRole = ref('')
const showAdd = ref(false)
const form = reactive({
  name: '', hostname: '', ip: '', os: '', cpu_cores: 4, memory_gb: 8,
  disk_gb: 100, environment: 'prod', role: 'app', region: '', provider: 'aws', tags: {},
})
const fromNow = (t) => t ? dayjs(t).fromNow() : 'Never'

onMounted(async () => {
  await Promise.all([loadServers(), loadSummary()])
})

async function loadServers() {
  const params = {}
  if (filterEnv.value) params.environment = filterEnv.value
  if (filterRole.value) params.role = filterRole.value
  servers.value = await serverApi.list(params)
}

async function loadSummary() {
  summary.value = await serverApi.summary()
}

async function addServer() {
  await serverApi.create(form)
  ElMessage.success('Server added')
  showAdd.value = false
  await Promise.all([loadServers(), loadSummary()])
}
</script>
