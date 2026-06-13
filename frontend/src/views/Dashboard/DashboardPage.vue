<template>
  <div>
    <div class="page-header">
      <h1>Dashboard</h1>
      <p>System overview — {{ dayjs().format('YYYY-MM-DD HH:mm') }}</p>
    </div>

    <div class="page-content">
      <!-- Stat cards -->
      <div class="stat-cards">
        <div class="stat-card" :class="data.servers.offline > 0 ? 'danger' : 'success'">
          <div class="stat-label">Servers</div>
          <div class="stat-value">{{ data.servers.online }}/{{ data.servers.total }}</div>
          <div class="stat-sub">{{ data.servers.offline }} offline</div>
        </div>
        <div class="stat-card" :class="data.deployments.unhealthy > 0 ? 'warning' : 'success'">
          <div class="stat-label">Deployments</div>
          <div class="stat-value">{{ data.deployments.healthy }}/{{ data.deployments.total }}</div>
          <div class="stat-sub">{{ data.deployments.unhealthy }} unhealthy</div>
        </div>
        <div class="stat-card" :class="data.alerts.critical > 0 ? 'danger' : data.alerts.firing > 0 ? 'warning' : 'success'">
          <div class="stat-label">Firing Alerts</div>
          <div class="stat-value">{{ data.alerts.firing }}</div>
          <div class="stat-sub">{{ data.alerts.critical }} critical</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">Pipeline Runs</div>
          <div class="stat-value">{{ data.recent_pipeline_runs.length }}</div>
          <div class="stat-sub">recent activity</div>
        </div>
      </div>

      <!-- Recent activity grid -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <!-- Recent pipeline runs -->
        <div class="card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
            <strong>Recent Pipeline Runs</strong>
            <router-link to="/pipelines" style="font-size:12px;color:var(--color-info)">View all</router-link>
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Pipeline</th><th>Triggered By</th><th>Status</th><th>Time</th></tr>
            </thead>
            <tbody>
              <tr v-for="run in data.recent_pipeline_runs" :key="run.id">
                <td>#{{ run.id }}</td>
                <td>{{ run.triggered_by }}</td>
                <td><span :class="['badge', run.status]">{{ run.status }}</span></td>
                <td style="color:var(--color-muted);font-size:12px">{{ fromNow(run.created_at) }}</td>
              </tr>
              <tr v-if="!data.recent_pipeline_runs.length">
                <td colspan="4" style="text-align:center;color:var(--color-muted)">No recent runs</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Recent task executions -->
        <div class="card">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">
            <strong>Recent Task Executions</strong>
            <router-link to="/tasks" style="font-size:12px;color:var(--color-info)">View all</router-link>
          </div>
          <table class="data-table">
            <thead>
              <tr><th>Task</th><th>Status</th><th>Time</th></tr>
            </thead>
            <tbody>
              <tr v-for="task in data.recent_task_executions" :key="task.id">
                <td>{{ task.title }}</td>
                <td><span :class="['badge', task.status]">{{ task.status }}</span></td>
                <td style="color:var(--color-muted);font-size:12px">{{ fromNow(task.created_at) }}</td>
              </tr>
              <tr v-if="!data.recent_task_executions.length">
                <td colspan="3" style="text-align:center;color:var(--color-muted)">No recent tasks</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { dashboardApi } from '@/api'

dayjs.extend(relativeTime)

const data = ref({
  servers: { total: 0, online: 0, offline: 0 },
  deployments: { total: 0, healthy: 0, unhealthy: 0 },
  alerts: { firing: 0, critical: 0, warning: 0 },
  recent_pipeline_runs: [],
  recent_task_executions: [],
})

const fromNow = (t) => t ? dayjs(t).fromNow() : '-'

onMounted(async () => {
  try {
    data.value = await dashboardApi.overview()
  } catch {}
})
</script>
