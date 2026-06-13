import request from './request'

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  login: (username, password) => {
    const form = new URLSearchParams({ username, password })
    return request.post('/auth/token', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
  },
  me: () => request.get('/auth/me'),
}

// ── Dashboard ─────────────────────────────────────────────────
export const dashboardApi = {
  overview: () => request.get('/dashboard/overview'),
}

// ── Pipelines ─────────────────────────────────────────────────
export const pipelineApi = {
  list: () => request.get('/pipelines'),
  create: (data) => request.post('/pipelines', data),
  runs: (id, limit = 20) => request.get(`/pipelines/${id}/runs`, { params: { limit } }),
  trigger: (id, payload) => request.post(`/pipelines/${id}/trigger`, payload),
  syncRun: (pipelineId, runId) => request.get(`/pipelines/${pipelineId}/runs/${runId}/sync`),
}

// ── Deployments ───────────────────────────────────────────────
export const deploymentApi = {
  environments: () => request.get('/deployments/environments'),
  list: (envId) => request.get('/deployments', { params: envId ? { env_id: envId } : {} }),
  get: (id) => request.get(`/deployments/${id}`),
  deploy: (id, payload) => request.post(`/deployments/${id}/deploy`, payload),
  rollback: (id) => request.post(`/deployments/${id}/rollback`),
  scale: (id, replicas) => request.post(`/deployments/${id}/scale`, { replicas }),
  history: (id) => request.get(`/deployments/${id}/history`),
}

// ── Servers ───────────────────────────────────────────────────
export const serverApi = {
  list: (params) => request.get('/servers', { params }),
  get: (id) => request.get(`/servers/${id}`),
  create: (data) => request.post('/servers', data),
  metrics: (id, hours = 1) => request.get(`/servers/${id}/metrics`, { params: { hours } }),
  summary: () => request.get('/servers/stats/summary'),
}

// ── Tasks ─────────────────────────────────────────────────────
export const taskApi = {
  listRunbooks: (category) => request.get('/tasks/runbooks', { params: category ? { category } : {} }),
  getRunbook: (id) => request.get(`/tasks/runbooks/${id}`),
  createRunbook: (data) => request.post('/tasks/runbooks', data),
  execute: (id, payload) => request.post(`/tasks/runbooks/${id}/execute`, payload),
  listExecutions: (runbookId, limit = 30) =>
    request.get('/tasks/executions', { params: { runbook_id: runbookId, limit } }),
  getExecution: (id) => request.get(`/tasks/executions/${id}`),
  approve: (id) => request.post(`/tasks/executions/${id}/approve`),
  cancel: (id) => request.post(`/tasks/executions/${id}/cancel`),
}

// ── Alerts ────────────────────────────────────────────────────
export const alertApi = {
  listRules: () => request.get('/alerts/rules'),
  createRule: (data) => request.post('/alerts/rules', data),
  toggleRule: (id) => request.put(`/alerts/rules/${id}/toggle`),
  list: (params) => request.get('/alerts', { params }),
  acknowledge: (id) => request.post(`/alerts/${id}/acknowledge`),
  resolve: (id) => request.post(`/alerts/${id}/resolve`),
  summary: () => request.get('/alerts/stats/summary'),
}
