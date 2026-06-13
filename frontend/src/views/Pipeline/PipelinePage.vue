<template>
  <div>
    <div class="page-header">
      <h1>CI/CD Pipelines</h1>
      <p>Manage and trigger GitHub Actions workflows</p>
    </div>
    <div class="page-content">
      <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
        <button class="btn btn-primary" @click="showCreate = true">
          <el-icon><Plus /></el-icon> New Pipeline
        </button>
      </div>

      <div class="card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th><th>Repository</th><th>Branch</th>
              <th>Workflow</th><th>Tags</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in pipelines" :key="p.id">
              <td>
                <router-link :to="`/pipelines/${p.id}`" style="color:var(--color-info)">
                  {{ p.name }}
                </router-link>
              </td>
              <td style="font-family:monospace;font-size:12px">{{ p.repo }}</td>
              <td><span class="badge info">{{ p.branch }}</span></td>
              <td style="font-size:12px;color:var(--color-muted)">{{ p.workflow_file }}</td>
              <td>
                <el-tag v-for="t in p.tags" :key="t" size="small" style="margin-right:4px">{{ t }}</el-tag>
              </td>
              <td>
                <button class="btn btn-sm btn-primary" @click="triggerPipeline(p)">
                  <el-icon><VideoPlay /></el-icon> Run
                </button>
                <button class="btn btn-sm btn-default" style="margin-left:6px"
                        @click="$router.push(`/pipelines/${p.id}`)">
                  Runs
                </button>
              </td>
            </tr>
            <tr v-if="!pipelines.length">
              <td colspan="6" style="text-align:center;color:var(--color-muted);padding:32px">
                No pipelines yet. Create one to get started.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create dialog -->
    <el-dialog v-model="showCreate" title="New Pipeline" width="520px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="Name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Repository">
          <el-input v-model="form.repo" placeholder="owner/repo" />
        </el-form-item>
        <el-form-item label="Branch"><el-input v-model="form.branch" /></el-form-item>
        <el-form-item label="Workflow File">
          <el-input v-model="form.workflow_file" placeholder="ci.yml" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showCreate = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="createPipeline">Create</button>
      </template>
    </el-dialog>

    <!-- Trigger dialog -->
    <el-dialog v-model="showTrigger" :title="`Trigger: ${selected?.name}`" width="420px">
      <el-form label-width="80px">
        <el-form-item label="Ref">
          <el-input v-model="triggerRef" placeholder="main" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showTrigger = false">Cancel</button>
        <button class="btn btn-primary" :loading="triggering" style="margin-left:8px"
                @click="confirmTrigger">
          <el-icon><VideoPlay /></el-icon> Trigger
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { pipelineApi } from '@/api'

const pipelines = ref([])
const showCreate = ref(false)
const showTrigger = ref(false)
const selected = ref(null)
const triggerRef = ref('main')
const triggering = ref(false)
const form = reactive({ name: '', repo: '', branch: 'main', workflow_file: 'ci.yml', description: '' })

onMounted(async () => { pipelines.value = await pipelineApi.list() })

async function createPipeline() {
  await pipelineApi.create(form)
  ElMessage.success('Pipeline created')
  showCreate.value = false
  pipelines.value = await pipelineApi.list()
}

function triggerPipeline(p) {
  selected.value = p
  triggerRef.value = p.branch
  showTrigger.value = true
}

async function confirmTrigger() {
  triggering.value = true
  try {
    await pipelineApi.trigger(selected.value.id, { ref: triggerRef.value })
    ElMessage.success('Pipeline triggered successfully')
    showTrigger.value = false
  } finally { triggering.value = false }
}
</script>
