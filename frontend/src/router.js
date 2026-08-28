import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('./views/LoginView.vue'), meta: { public: true } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('./views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/complaints', name: 'Complaints', component: () => import('./views/ComplaintListView.vue'), meta: { requiresAuth: true } },
  { path: '/complaints/new', name: 'NewComplaint', component: () => import('./views/NewComplaintView.vue'), meta: { requiresAuth: true } },
  { path: '/complaints/:id', name: 'ComplaintDetail', component: () => import('./views/ComplaintDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/reports', name: 'Reports', component: () => import('./views/ReportsView.vue'), meta: { requiresAuth: true } },
  { path: '/audit', name: 'Audit', component: () => import('./views/AuditLogView.vue'), meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('./views/NotFoundView.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() { return { top: 0 } }
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) return next('/login')
  if (to.meta.public && token) return next('/dashboard')
  next()
})

export default router
