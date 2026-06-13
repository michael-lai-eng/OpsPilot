import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import { useAuthStore } from '@/store/modules/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard/DashboardPage.vue'),
        meta: { title: 'Dashboard' },
      },
      {
        path: 'pipelines',
        name: 'Pipelines',
        component: () => import('@/views/Pipeline/PipelinePage.vue'),
        meta: { title: 'CI/CD Pipelines' },
      },
      {
        path: 'pipelines/:id',
        name: 'PipelineDetail',
        component: () => import('@/views/Pipeline/PipelineDetailPage.vue'),
        meta: { title: 'Pipeline Detail' },
      },
      {
        path: 'deployments',
        name: 'Deployments',
        component: () => import('@/views/Deployment/DeploymentPage.vue'),
        meta: { title: 'Deployments' },
      },
      {
        path: 'servers',
        name: 'Servers',
        component: () => import('@/views/Assets/ServerPage.vue'),
        meta: { title: 'Servers' },
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks/TaskPage.vue'),
        meta: { title: 'Task Automation' },
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/Alerts/AlertPage.vue'),
        meta: { title: 'Alert Manager' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  NProgress.start()
  if (!to.meta.public) {
    const auth = useAuthStore()
    if (!auth.token) return '/login'
  }
})

router.afterEach(() => NProgress.done())

export default router
