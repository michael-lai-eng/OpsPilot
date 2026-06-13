<template>
  <div>
    <div class="page-header">
      <h1>Task Automation</h1>
      <p>Runbooks — reusable scripts for operational tasks</p>
    </div>
    <div class="page-content">
      <div style="display:flex;gap:12px">
        <!-- Left: runbook library -->
        <div style="width:340px;flex-shrink:0">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <strong>Runbooks</strong>
            <button class="btn btn-sm btn-primary" @click="showCreate = true">
              <el-icon><Plus /></el-icon> New
            </button>
          </div>

          <el-select v-model="catFilter" placeholder="Category" clearable size="small"
                     @change="loadRunbooks" style="width:100%;margin-bottom:10px">
            <el-option label="Deploy" value="deploy" />
            <el-option label="Maintenance" value="maintain" />
            <el-option label="Diagnose" value="diagnose" />
            <el-option label="Cleanup" value="cleanup" />
            <el-option label="Misc" value="misc" />
          </el-select>

          <div v-for="book in runbooks" :key="book.id"
               :class="['card', 'runbook-item', selected?.id === book.id ? 'selected' : '']"
               style="margin-bottom:8px;cursor:pointer;padding:12px 16px"
               @click="selectRunbook(book)">
            <div style="display:flex;align-items:center;gap:8px">
              <span :class="['badge', catColor(book.category)]">{{ book.category }}</span>
              <strong style="font-size:13px">{{ book.name }}</strong>
              <el-icon v-if="book.requires_approval" title="Requires approval" style="color:var(--color-warning)"><Warning /></el-icon>
            </div>
            <div style="font-size:12px;color:var(--color-muted);margin-top:4px">{{ book.description }}</div>
          </div>
          <div v-if="!runbooks.length" style="text-align:center;color:var(--color-muted);padding:20px;font-size:13px">
            No runbooks yet
          </div>
        </div>

        <!-- Right: detail + execute -->
        <div style="flex:1">
          <div v-if="selected" class="card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
              <div>
                <h3>{{ selected.name }}</h3>
                <p style="color:var(--color-muted);font-size:13px;margin-top:4px">{{ selected.description }}</p>
              </div>
              <button class="btn btn-primary" @click="showExec = true">
                <el-icon><CaretRight /></el-icon> Execute
              </button>
            </div>

            <div style="margin-bottom:16px">
              <div style="font-size:12px;color:var(--color-muted);margin-bottom:6px">Script ({{ selected.script_type }})</div>
              <pre class="code-block">{{ selected.script }}</pre>
            </div>

            <div style="font-size:12px;color:var(--color-muted)">
              Timeout: {{ selected.timeout_seconds }}s ·
              <span v-if="selected.requires_approval" style="color:var(--color-warning)">⚠ Requires approval</span>
              <span v-else style="color:var(--color-primary-hover)">✓ Auto-approved</span>
            </div>
          </div>
          <div v-else class="card" style="text-align:center;padding:48px;color:var(--color-muted)">
            Select a runbook to view details and execute
          </div>

          <!-- Execution history -->
          <div class="card" style="margin-top:16px">
            <div style="display:flex;justify-content:space-between;margin-bottom:12px">
              <strong>Recent Executions</strong>
              <button class="btn btn-sm btn-default" @click="loadExecs">
                <el-icon><Refresh /></el-icon>
              </button>
            </div>
            <table class="data-table">
              <thead>
                <tr><th>ID</th><th>Task</th><th>Status</th><th>Exit</th><th>Duration</th><th>Time</th></tr>
              </thead>
              <tbody>
                <tr v-for="ex in executions" :key="ex.id" style="cursor:pointer"
                    @click="viewExec(ex)">
                  <td>#{{ ex.id }}</td>
                  <td>{{ ex.title }}</td>
                  <td><span :class="['badge', ex.status]">{{ ex.status }}</span></td>
                  <td style="font-family:monospace">{{ ex.exit_code ?? '—' }}</td>
                  <td style="font-size:12px">
                    {{ ex.started_at && ex.finished_at
                      ? `${Math.round((new Date(ex.finished_at)-new Date(ex.started_at))/1000)}s`
                      : '—' }}
                  </td>
                  <td style="font-size:12px;color:var(--color-muted)">{{ fromNow(ex.created_at) }}</td>
                </tr>
                <tr v-if="!executions.length">
                  <td colspan="6" style="text-align:center;color:var(--color-muted)">No executions</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Execute dialog -->
    <el-dialog v-model="showExec" :title="`Execute: ${selected?.name}`" width="480px">
      <el-form label-width="100px">
        <el-form-item label="Title">
          <el-input v-model="execForm.title" :placeholder="selected?.name" />
        </el-form-item>
        <template v-if="selected?.params_schema?.properties">
          <el-form-item v-for="(schema, key) in selected.params_schema.properties" :key="key" :label="key">
            <el-input v-model="execForm.params[key]" :placeholder="schema.description || ''" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showExec = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="doExecute">
          <el-icon><CaretRight /></el-icon> Run
        </button>
      </template>
    </el-dialog>

    <!-- Create runbook dialog -->
    <el-dialog v-model="showCreate" title="New Runbook" width="620px">
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="Name"><el-input v-model="createForm.name" /></el-form-item>
        <el-form-item label="Category">
          <el-select v-model="createForm.category" style="width:100%">
            <el-option label="deploy" value="deploy" />
            <el-option label="maintain" value="maintain" />
            <el-option label="diagnose" value="diagnose" />
            <el-option label="cleanup" value="cleanup" />
            <el-option label="misc" value="misc" />
          </el-select>
        </el-form-item>
        <el-form-item label="Script Type">
          <el-radio-group v-model="createForm.script_type">
            <el-radio label="bash">Bash</el-radio>
            <el-radio label="python">Python</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="createForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Script">
          <el-input v-model="createForm.script" type="textarea" :rows="8"
                    style="font-family:monospace;font-size:12px" />
        </el-form-item>
        <el-form-item label="Timeout (s)">
          <el-input-number v-model="createForm.timeout_seconds" :min="10" :max="3600" />
        </el-form-item>
        <el-form-item label="Need Approval">
          <el-switch v-model="createForm.requires_approval" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showCreate = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="createRunbook">Create</button>
      </template>
    </el-dialog>

    <!-- Execution detail drawer -->
    <el-drawer v-model="showExecDetail" title="Execution Output" size="50%">
      <div v-if="execDetail">
        <div style="margin-bottom:16px">
          <span :class="['badge', execDetail.status]" style="font-size:13px">{{ execDetail.status }}</span>
          <span style="font-size:12px;color:var(--color-muted);margin-left:12px">Exit: {{ execDetail.exit_code ?? '—' }}</span>
        </div>
        <div style="font-size:12px;color:var(--color-muted);margin-bottom:8px">stdout</div>
        <pre class="code-block" style="max-height:300px;overflow:auto">{{ execDetail.output || '(empty)' }}</pre>
        <div v-if="execDetail.error" style="margin-top:16px">
          <div style="font-size:12px;color:var(--color-danger);margin-bottom:8px">stderr</div>
          <pre class="code-block" style="border-color:rgba(218,54,51,.3)">{{ execDetail.error }}</pre>
        </div>
        <div style="margin-top:16px;display:flex;gap:8px">
          <button v-if="execDetail.status === 'pending'" class="btn btn-primary" @click="approveExec">
            ✓ Approve
          </button>
          <button v-if="['pending','running'].includes(execDetail.status)"
                  class="btn btn-danger" @click="cancelExec">Cancel</button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { taskApi } from '@/api'

dayjs.extend(relativeTime)

const runbooks = ref([])
const executions = ref([])
const selected = ref(null)
const catFilter = ref('')
const showExec = ref(false)
const showCreate = ref(false)
const showExecDetail = ref(false)
const execDetail = ref(null)
const execForm = reactive({ title: '', params: {} })
const createForm = reactive({
  name: '', category: 'misc', description: '', script: '#!/bin/bash\necho "Hello, OpsPilot!"',
  script_type: 'bash', timeout_seconds: 300, requires_approval: false, params_schema: {},
})
const fromNow = (t) => t ? dayjs(t).fromNow() : '-'
const catColor = (c) => ({ deploy: 'info', maintain: 'warning', diagnose: 'info', cleanup: 'danger', misc: '' })[c] || ''

onMounted(async () => { await loadRunbooks(); await loadExecs() })

async function loadRunbooks() {
  runbooks.value = await taskApi.listRunbooks(catFilter.value || undefined)
}

async function loadExecs() {
  executions.value = await taskApi.listExecutions(selected.value?.id)
}

function selectRunbook(book) {
  selected.value = book
  execForm.title = ''
  execForm.params = {}
  loadExecs()
}

async function doExecute() {
  const res = await taskApi.execute(selected.value.id, {
    title: execForm.title || selected.value.name,
    params: execForm.params,
  })
  ElMessage.success(res.status === 'pending' ? 'Queued — awaiting approval' : 'Execution started')
  showExec.value = false
  await loadExecs()
}

async function createRunbook() {
  await taskApi.createRunbook(createForm)
  ElMessage.success('Runbook created')
  showCreate.value = false
  await loadRunbooks()
}

async function viewExec(ex) {
  execDetail.value = await taskApi.getExecution(ex.id)
  showExecDetail.value = true
}

async function approveExec() {
  await taskApi.approve(execDetail.value.id)
  ElMessage.success('Approved')
  showExecDetail.value = false
  await loadExecs()
}

async function cancelExec() {
  await taskApi.cancel(execDetail.value.id)
  ElMessage.success('Cancelled')
  showExecDetail.value = false
  await loadExecs()
}
</script>

<style scoped>
.runbook-item { transition: border-color .15s; }
.runbook-item:hover { border-color: var(--color-info); }
.runbook-item.selected { border-color: var(--color-primary-hover); }
.code-block {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px 16px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
