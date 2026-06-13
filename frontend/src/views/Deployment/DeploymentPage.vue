<template>
  <div>
    <div class="page-header">
      <h1>Deployments</h1>
      <p>Manage Kubernetes deployments across environments</p>
    </div>
    <div class="page-content">
      <!-- Env tabs -->
      <div style="display:flex;gap:8px;margin-bottom:20px">
        <button :class="['btn', activeEnv === null ? 'btn-primary' : 'btn-default']"
                @click="filterEnv(null)">All</button>
        <button v-for="env in environments" :key="env.id"
                :class="['btn', activeEnv === env.id ? 'btn-primary' : 'btn-default']"
                @click="filterEnv(env.id)">
          {{ env.name }}
          <span v-if="env.is_protected" style="font-size:10px;margin-left:4px">🔒</span>
        </button>
      </div>

      <div class="card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Service</th><th>Image</th><th>Replicas</th>
              <th>Status</th><th>Health</th><th>Deployed At</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="dep in deployments" :key="dep.id">
              <td style="font-weight:600">{{ dep.service }}</td>
              <td style="font-family:monospace;font-size:11px;max-width:240px;
                         overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ dep.image }}
              </td>
              <td>{{ dep.ready_replicas }}/{{ dep.replicas }}</td>
              <td><span :class="['badge', dep.status]">{{ dep.status }}</span></td>
              <td><span :class="['badge', dep.health]">{{ dep.health }}</span></td>
              <td style="font-size:12px;color:var(--color-muted)">{{ fromNow(dep.deployed_at) }}</td>
              <td style="display:flex;gap:6px">
                <button class="btn btn-sm btn-primary" @click="openDeploy(dep)">Deploy</button>
                <button class="btn btn-sm btn-default" @click="doRollback(dep)">Rollback</button>
                <button class="btn btn-sm btn-default" @click="openScale(dep)">Scale</button>
              </td>
            </tr>
            <tr v-if="!deployments.length">
              <td colspan="7" style="text-align:center;color:var(--color-muted);padding:32px">
                No deployments found
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Deploy dialog -->
    <el-dialog v-model="showDeploy" :title="`Deploy: ${selected?.service}`" width="460px">
      <el-form label-width="100px">
        <el-form-item label="New Image">
          <el-input v-model="deployForm.image" placeholder="registry/image:tag" />
        </el-form-item>
        <el-form-item label="Note">
          <el-input v-model="deployForm.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showDeploy = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="confirmDeploy">Deploy</button>
      </template>
    </el-dialog>

    <!-- Scale dialog -->
    <el-dialog v-model="showScale" :title="`Scale: ${selected?.service}`" width="360px">
      <el-form label-width="100px">
        <el-form-item label="Replicas">
          <el-input-number v-model="scaleReplicas" :min="0" :max="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-default" @click="showScale = false">Cancel</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="confirmScale">Scale</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { deploymentApi } from '@/api'

dayjs.extend(relativeTime)

const environments = ref([])
const deployments = ref([])
const activeEnv = ref(null)
const selected = ref(null)
const showDeploy = ref(false)
const showScale = ref(false)
const deployForm = reactive({ image: '', note: '' })
const scaleReplicas = ref(1)
const fromNow = (t) => t ? dayjs(t).fromNow() : '-'

onMounted(async () => {
  environments.value = await deploymentApi.environments()
  deployments.value = await deploymentApi.list()
})

async function filterEnv(id) {
  activeEnv.value = id
  deployments.value = await deploymentApi.list(id)
}

function openDeploy(dep) {
  selected.value = dep
  deployForm.image = dep.image
  deployForm.note = ''
  showDeploy.value = true
}

async function confirmDeploy() {
  await deploymentApi.deploy(selected.value.id, deployForm)
  ElMessage.success('Deployment triggered')
  showDeploy.value = false
  deployments.value = await deploymentApi.list(activeEnv.value)
}

async function doRollback(dep) {
  await ElMessageBox.confirm(`Rollback ${dep.service} to the previous version?`, 'Confirm Rollback', { type: 'warning' })
  await deploymentApi.rollback(dep.id)
  ElMessage.success('Rollback initiated')
  deployments.value = await deploymentApi.list(activeEnv.value)
}

function openScale(dep) {
  selected.value = dep
  scaleReplicas.value = dep.replicas
  showScale.value = true
}

async function confirmScale() {
  await deploymentApi.scale(selected.value.id, scaleReplicas.value)
  ElMessage.success(`Scaled to ${scaleReplicas.value} replicas`)
  showScale.value = false
  deployments.value = await deploymentApi.list(activeEnv.value)
}
</script>
