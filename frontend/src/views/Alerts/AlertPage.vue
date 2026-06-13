<template>
  <div>
    <div class="page-header">
      <h1>Alert Manager</h1>
      <p>Monitor firing alerts and manage alert rules</p>
    </div>
    <div class="page-content">
      <!-- Summary -->
      <div class="stat-cards" style="grid-template-columns:repeat(3,1fr);margin-bottom:24px">
        <div class="stat-card danger">
          <div class="stat-label">Critical</div>
          <div class="stat-value">{{ summary.critical }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Warning</div>
          <div class="stat-value">{{ summary.warning }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Firing</div>
          <div class="stat-value">{{ summary.firing }}</div>
        </div>
      </div>

      <el-tabs v-model="activeTab">
        <!-- Firing alerts -->
        <el-tab-pane label="Firing Alerts" name="alerts">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <el-select v-model="filterStatus" placeholder="Status" clearable size="small"
                       @change="loadAlerts" style="width:130px">
              <el-option label="Firing" value="firing" />
              <el-option label="Resolved" value="resolved" />
              <el-option label="Silenced" value="silenced" />
            </el-select>
            <el-select v-model="filterSeverity" placeholder="Severity" clearable size="small"
                       @change="loadAlerts" style="width:130px">
              <el-option label="Critical" value="critical" />
              <el-option label="Warning" value="warning" />
              <el-option label="Info" value="info" />
            </el-select>
          </div>

          <div class="card">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Title</th><th>Resource</th><th>Severity</th>
                  <th>Status</th><th>Fired At</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in alerts" :key="a.id">
                  <td>
                    <div style="font-weight:500">{{ a.title }}</div>
                    <div style="font-size:12px;color:var(--color-muted)">{{ a.message }}</div>
                  </td>
                  <td style="font-size:12px">{{ a.resource_name }}</td>
                  <td><span :class="['badge', a.severity]">{{ a.severity }}</span></td>
                  <td><span :class="['badge', a.status]">{{ a.status }}</span></td>
                  <td style="font-size:12px;color:var(--color-muted)">{{ fromNow(a.fired_at) }}</td>
                  <td style="display:flex;gap:6px">
                    <button v-if="a.status === 'firing'" class="btn btn-sm btn-default"
                            @click="ack(a)">Ack</button>
                    <button v-if="a.status !== 'resolved'" class="btn btn-sm btn-default"
                            @click="resolve(a)">Resolve</button>
                  </td>
                </tr>
                <tr v-if="!alerts.length">
                  <td colspan="6" style="text-align:center;color:var(--color-muted);padding:32px">
                    🎉 No alerts
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>

        <!-- Alert rules -->
        <el-tab-pane label="Alert Rules" name="rules">
          <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
            <button class="btn btn-primary" @click="showCreate = true">
              <el-icon><Plus /></el-icon> New Rule
            </button>
          </div>
          <div class="card">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Name</th><th>Resource</th><th>Metric</th>
                  <th>Condition</th><th>Severity</th><th>Active</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in rules" :key="r.id">
                  <td style="font-weight:500">{{ r.name }}</td>
                  <td style="font-size:12px">{{ r.resource_type }}</td>
                  <td style="font-family:monospace;font-size:12px">{{ r.metric }}</td>
                  <td style="font-size:12px;font-family:monospace">
                    {{ r.operator }} {{ r.threshold }}
                  </td>
                  <td><span :class="['badge', r.severity]">{{ r.severity }}</span></td>
                  <td>
                    <el-switch :model-value="r.is_active" @change="toggleRule(r)" />
                  </td>
                  <td></td>
                </tr>
                <tr v-if="!rules.length">
                  <td colspan="7" style="text-align:center;color:var(--color-muted);padding:32px">No rules</td>
                </tr>
              </tbody>
            </table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Create rule dialog -->
    <el-dialog v-model="showCreate" title="New Alert Rule" width="480px">
      <el-form :model="ruleForm" label-width="120px">
        <el-form-item label="Name"><el-input v-model="ruleForm.name" /></el-form-item>
        <el-form-item label="Resource Type">
          <el-select v-model="ruleForm.resource_type" style="width:100%">
            <el-option label="server" value="server" />
            <el-option label="deployment" value="deployment" />
            <el-option label="pipeline" value="pipeline" />
          </el-select>
        </el-form-item>
        <el-form-item label="Metric">
          <el-select v-model="ruleForm.metric" style="width:100%">
            <el-option label="cpu_usage" value="cpu_usage" />
            <el-option label="mem_usage" value="mem_usage" />
            <el-option label="disk_usage" value="disk_usage" />
            <el-option label="error_rate" value="error_rate" />
          </el-select>
        </el-form-item>
        <el-form-item label="Operator">
          <el-select v-model="ruleForm.operator" style="width:100%">
            <el-option label=">" value=">" />
            <el-option label=">=" value=">=" />
            <el-option label="<" value="<" />
            <el-option label="<=" value="<=" />
          </el-select>
        </el-form-item>
        <el-form-item label="Threshold">
          <el-input-number v-model="ruleForm.threshold" :min="0" :max="100" :step="5" />
        </el-form-item>
        <el-form-item label="Severity">
          <el-select v-model="ruleForm.severity" style="width:100%">
            <el-option label="info" value="info" />
            <el-option label="warning" value="warning" />
            <el-option label="critical" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="Duration (s)">
          <el-input-number v-model="ruleForm.duration_seconds" :min="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showCreate = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="createRule">Create</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { alertApi } from '@/api'

dayjs.extend(relativeTime)

const activeTab = ref('alerts')
const alerts = ref([])
const rules = ref([])
const summary = ref({ firing: 0, critical: 0, warning: 0 })
const filterStatus = ref('firing')
const filterSeverity = ref('')
const showCreate = ref(false)
const ruleForm = reactive({
  name: '', resource_type: 'server', metric: 'cpu_usage',
  operator: '>', threshold: 80, duration_seconds: 60, severity: 'warning', channels: [],
})
const fromNow = (t) => t ? dayjs(t).fromNow() : '-'

onMounted(async () => {
  await Promise.all([loadAlerts(), loadRules(), loadSummary()])
})

async function loadAlerts() {
  const params = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterSeverity.value) params.severity = filterSeverity.value
  alerts.value = await alertApi.list(params)
}

async function loadRules() { rules.value = await alertApi.listRules() }
async function loadSummary() { summary.value = await alertApi.summary() }

async function ack(a) {
  await alertApi.acknowledge(a.id)
  ElMessage.success('Acknowledged')
  await loadAlerts()
}

async function resolve(a) {
  await alertApi.resolve(a.id)
  ElMessage.success('Resolved')
  await Promise.all([loadAlerts(), loadSummary()])
}

async function toggleRule(r) {
  await alertApi.toggleRule(r.id)
  await loadRules()
}

async function createRule() {
  await alertApi.createRule(ruleForm)
  ElMessage.success('Rule created')
  showCreate.value = false
  await loadRules()
}
</script>
