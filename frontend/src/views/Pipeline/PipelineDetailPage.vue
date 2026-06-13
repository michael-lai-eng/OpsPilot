<template>
  <div>
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <button class="btn btn-default btn-sm" @click="$router.back()">← Back</button>
        <div>
          <h1>{{ pipeline?.name || 'Pipeline' }}</h1>
          <p>{{ pipeline?.repo }} · {{ pipeline?.branch }}</p>
        </div>
      </div>
    </div>
    <div class="page-content">
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn btn-primary" @click="showTrigger = true">
          <el-icon><VideoPlay /></el-icon> Trigger Run
        </button>
      </div>

      <div class="card">
        <div style="margin-bottom:14px;display:flex;align-items:center;justify-content:space-between">
          <strong>Run History</strong>
          <button class="btn btn-sm btn-default" @click="loadRuns">
            <el-icon><Refresh /></el-icon> Refresh
          </button>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th><th>GitHub Run</th><th>Triggered By</th>
              <th>Status</th><th>Conclusion</th><th>Duration</th><th>Commit</th><th>Time</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td>{{ run.run_number || run.id }}</td>
              <td>
                <a v-if="run.logs_url" :href="run.logs_url" target="_blank"
                   style="color:var(--color-info);font-size:12px">
                  #{{ run.github_run_id }}
                </a>
                <span v-else style="color:var(--color-muted)">-</span>
              </td>
              <td>{{ run.triggered_by }}</td>
              <td><span :class="['badge', run.status]">{{ run.status }}</span></td>
              <td>
                <span v-if="run.conclusion" :class="['badge', run.conclusion]">{{ run.conclusion }}</span>
                <span v-else style="color:var(--color-muted)">—</span>
              </td>
              <td style="font-size:12px">
                {{ run.duration_seconds ? `${run.duration_seconds}s` : '—' }}
              </td>
              <td style="font-family:monospace;font-size:11px;color:var(--color-muted)">
                {{ run.commit_sha?.slice(0, 7) || '—' }}
              </td>
              <td style="font-size:12px;color:var(--color-muted)">{{ fromNow(run.created_at) }}</td>
            </tr>
            <tr v-if="!runs.length">
              <td colspan="8" style="text-align:center;color:var(--color-muted);padding:32px">No runs yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <el-dialog v-model="showTrigger" title="Trigger Pipeline" width="380px">
      <el-form label-width="60px">
        <el-form-item label="Ref"><el-input v-model="triggerRef" /></el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showTrigger = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="doTrigger">
          <el-icon><VideoPlay /></el-icon> Run
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { pipelineApi } from '@/api'

dayjs.extend(relativeTime)
const route = useRoute()
const pipeline = ref(null)
const runs = ref([])
const showTrigger = ref(false)
const triggerRef = ref('main')
const fromNow = (t) => t ? dayjs(t).fromNow() : '-'

onMounted(async () => {
  const all = await pipelineApi.list()
  pipeline.value = all.find(p => p.id === Number(route.params.id))
  if (pipeline.value) triggerRef.value = pipeline.value.branch
  await loadRuns()
})

async function loadRuns() {
  runs.value = await pipelineApi.runs(route.params.id)
}

async function doTrigger() {
  await pipelineApi.trigger(route.params.id, { ref: triggerRef.value })
  ElMessage.success('Triggered!')
  showTrigger.value = false
  setTimeout(loadRuns, 2000)
}
</script>
