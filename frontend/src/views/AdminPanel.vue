<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('admin.title') }}</h1>

      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'users'" class="tab-panel">
        <div class="panel-header">
          <h2>{{ $t('admin.users') }}</h2>
          <button v-if="isSuperAdmin" class="btn-primary" @click="openUserForm()">+ {{ $t('admin.addUser') }}</button>
        </div>

        <table>
          <thead>
            <tr>
              <th>{{ $t('admin.username') }}</th>
              <th>{{ $t('admin.fullName') }}</th>
              <th>{{ $t('admin.role') }}</th>
              <th>{{ $t('admin.department') }}</th>
              <th>{{ $t('admin.status') }}</th>
              <th>{{ $t('admin.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in usersStore.users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.full_name_ar }}</td>
              <td><span class="badge">{{ $t(`admin.roleLabels.${user.role}`) }}</span></td>
              <td>{{ departmentName(user.department_id) }}</td>
              <td><span :class="['badge', user.is_active ? 'closed' : 'escalated']">{{ user.is_active ? $t('admin.active') : $t('admin.inactive') }}</span></td>
              <td>
                <button class="btn-small" @click="editUser(user)">{{ $t('admin.edit') }}</button>
                <button v-if="user.is_active" class="btn-small danger" @click="deactivate(user.id)">{{ $t('admin.deactivate') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="activeTab === 'roles'" class="tab-panel">
        <h2>{{ $t('admin.roles') }}</h2>
        <p class="hint">{{ $t('admin.rolesNote') }}</p>
        <div class="roles-grid">
          <div v-for="role in usersStore.roles" :key="role" class="role-card">
            <h3>{{ $t(`admin.roleLabels.${role}`) }}</h3>
            <ul>
              <li v-for="perm in rolePermissions[role]" :key="perm">{{ perm }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'departments'" class="tab-panel">
        <div class="panel-header">
          <h2>{{ $t('admin.departments') }}</h2>
          <button class="btn-primary" @click="openDeptForm()">+ {{ $t('admin.addDepartment') }}</button>
        </div>
        <table>
          <thead>
            <tr>
              <th>{{ $t('admin.code') }}</th>
              <th>{{ $t('admin.nameAr') }}</th>
              <th>{{ $t('admin.nameEn') }}</th>
              <th>{{ $t('admin.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="dept in departmentsStore.departments" :key="dept.id">
              <td class="mono">{{ dept.code }}</td>
              <td>{{ dept.name_ar }}</td>
              <td>{{ dept.name_en }}</td>
              <td><button class="btn-small" @click="editDept(dept)">{{ $t('admin.edit') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="tab-panel">
        <h2>{{ $t('admin.systemOverview') }}</h2>
        <div class="system-grid">
          <div class="system-card">
            <div class="system-value">{{ appVersion }}</div>
            <div class="system-label">{{ $t('admin.appVersion') }}</div>
          </div>
          <div class="system-card">
            <div class="system-value" :class="apiHealthy ? 'ok' : 'bad'">{{ apiHealthy ? $t('admin.healthy') : $t('admin.unhealthy') }}</div>
            <div class="system-label">{{ $t('admin.apiStatus') }}</div>
          </div>
          <div class="system-card">
            <div class="system-value">{{ usersStore.users.length }}</div>
            <div class="system-label">{{ $t('admin.totalUsers') }}</div>
          </div>
          <div class="system-card">
            <div class="system-value">{{ departmentsStore.departments.length }}</div>
            <div class="system-label">{{ $t('admin.totalDepartments') }}</div>
          </div>
          <div class="system-card">
            <div class="system-value">{{ dashboardStore.total }}</div>
            <div class="system-label">{{ $t('admin.totalComplaints') }}</div>
          </div>
          <div class="system-card">
            <div class="system-value">{{ $t('admin.auditRetentionValue') }}</div>
            <div class="system-label">{{ $t('admin.auditRetention') }}</div>
          </div>
        </div>
      </div>

      <div v-if="showUserForm" class="modal-overlay" @click.self="closeForm">
        <div class="modal">
          <h2>{{ editingUser ? $t('admin.editUser') : $t('admin.addUser') }}</h2>
          <form @submit.prevent="saveUser">
            <input v-model="form.username" :placeholder="$t('admin.username')" required :disabled="!!editingUser" />
            <input v-model="form.full_name_ar" :placeholder="$t('admin.fullNameAr')" required />
            <input v-model="form.full_name_en" :placeholder="$t('admin.fullNameEn')" />
            <input v-model="form.email" type="email" :placeholder="$t('admin.email')" required />
            <select v-model="form.role" required>
              <option value="">{{ $t('admin.selectRole') }}</option>
              <option v-for="role in usersStore.roles" :key="role" :value="role">{{ $t(`admin.roleLabels.${role}`) }}</option>
            </select>
            <select v-model="form.department_id">
              <option value="">{{ $t('admin.selectDepartment') }}</option>
              <option v-for="dept in departmentsStore.departments" :key="dept.id" :value="dept.id">{{ dept.name_ar }}</option>
            </select>
            <input v-if="!editingUser" v-model="form.password" type="password" :placeholder="$t('admin.password')" required />
            <label class="checkbox-label">
              <input v-model="form.is_active" type="checkbox" />
              {{ $t('admin.active') }}
            </label>
            <p v-if="formError" class="error">{{ formError }}</p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeForm">{{ $t('common.cancel') }}</button>
              <button type="submit" class="btn-primary">{{ $t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="showDeptForm" class="modal-overlay" @click.self="closeDeptForm">
        <div class="modal">
          <h2>{{ editingDept ? $t('admin.editDepartment') : $t('admin.addDepartment') }}</h2>
          <form @submit.prevent="saveDept">
            <input v-model="deptForm.code" :placeholder="$t('admin.code')" required :disabled="!!editingDept" />
            <input v-model="deptForm.name_ar" :placeholder="$t('admin.nameAr')" required />
            <input v-model="deptForm.name_en" :placeholder="$t('admin.nameEn')" />
            <p v-if="deptFormError" class="error">{{ deptFormError }}</p>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeDeptForm">{{ $t('common.cancel') }}</button>
              <button type="submit" class="btn-primary">{{ $t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="showSecretModal" class="modal-overlay" @click.self="closeSecretModal">
        <div class="modal">
          <h2>{{ $t('admin.authenticatorSetupTitle') }}</h2>
          <p class="hint">{{ $t('admin.authenticatorSetupNote') }}</p>
          <label class="secret-label">{{ $t('admin.authenticatorSecret') }}</label>
          <div class="secret-row">
            <code>{{ createdTotpSecret }}</code>
            <button type="button" class="btn-small" @click="copySecret">{{ $t('admin.copySecret') }}</button>
          </div>
          <button type="button" class="btn-primary" @click="closeSecretModal">{{ $t('common.close') }}</button>
        </div>
      </div>
    </main>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLayout from '../components/AppLayout.vue'
import { useUsersStore } from '../stores/users'
import { useDepartmentsStore } from '../stores/departments'
import { useDashboardStore } from '../stores/dashboard'
import api from '../api/client'

const { t } = useI18n()
const usersStore = useUsersStore()
const departmentsStore = useDepartmentsStore()
const dashboardStore = useDashboardStore()

const activeTab = ref('users')
const showUserForm = ref(false)
const editingUser = ref(null)
const formError = ref('')
const showDeptForm = ref(false)
const editingDept = ref(null)
const deptFormError = ref('')
const appVersion = ref('—')
const apiHealthy = ref(false)
const showSecretModal = ref(false)
const createdTotpSecret = ref('')

const isSuperAdmin = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}').role === 'super_admin'
  } catch {
    return false
  }
})

const tabs = computed(() => [
  { key: 'users', label: t('admin.users') },
  { key: 'roles', label: t('admin.roles') },
  { key: 'departments', label: t('admin.departments') },
  { key: 'system', label: t('admin.system') },
])

const rolePermissionKeys = {
  super_admin: ['fullAccess', 'manageUsersDepts', 'manageRoles'],
  admin: ['manageUsers', 'manageDepartments', 'viewReports', 'manageComplaints'],
  senior_inspector: ['assignComplaints', 'signReports', 'manageInvestigations'],
  inspector: ['viewComplaints', 'addNotes', 'updateStatus'],
  viewer: ['readOnly'],
}
const rolePermissions = computed(() => {
  const result = {}
  for (const [role, keys] of Object.entries(rolePermissionKeys)) {
    result[role] = keys.map(key => t(`admin.permissionLabels.${key}`))
  }
  return result
})

const form = reactive({
  username: '',
  full_name_ar: '',
  full_name_en: '',
  email: '',
  role: '',
  department_id: '',
  password: '',
  is_active: true,
})

const deptForm = reactive({ code: '', name_ar: '', name_en: '' })

function departmentName(id) {
  const dept = departmentsStore.departments.find(d => d.id === id)
  return dept ? dept.name_ar : '—'
}

onMounted(async () => {
  await Promise.all([
    usersStore.fetchUsers(),
    usersStore.fetchRoles(),
    departmentsStore.fetchDepartments(),
    dashboardStore.fetchStats(),
  ])
  try {
    const res = await api.get('/health')
    apiHealthy.value = res.data.status === 'healthy'
    appVersion.value = res.data.version || '—'
  } catch {
    apiHealthy.value = false
  }
})

function openUserForm() {
  editingUser.value = null
  showUserForm.value = true
}

function editUser(user) {
  editingUser.value = user
  form.username = user.username
  form.full_name_ar = user.full_name_ar
  form.full_name_en = user.full_name_en || ''
  form.email = user.email || ''
  form.role = user.role
  form.department_id = user.department_id || ''
  form.password = ''
  form.is_active = user.is_active
  showUserForm.value = true
}

function closeForm() {
  showUserForm.value = false
  editingUser.value = null
  formError.value = ''
  form.username = ''
  form.full_name_ar = ''
  form.full_name_en = ''
  form.email = ''
  form.role = ''
  form.department_id = ''
  form.password = ''
  form.is_active = true
}

function closeSecretModal() {
  showSecretModal.value = false
  createdTotpSecret.value = ''
}

async function copySecret() {
  await navigator.clipboard.writeText(createdTotpSecret.value)
}

async function saveUser() {
  formError.value = ''
  try {
    if (editingUser.value) {
      await usersStore.updateUser(editingUser.value.id, {
        full_name_ar: form.full_name_ar,
        full_name_en: form.full_name_en,
        email: form.email,
        role: form.role,
        department_id: form.department_id || null,
        is_active: form.is_active,
      })
    } else {
      const createdUser = await usersStore.createUser({ ...form, department_id: form.department_id || null })
      createdTotpSecret.value = createdUser.totp_secret
      closeForm()
      showSecretModal.value = true
      return
    }
    closeForm()
  } catch (e) {
    formError.value = e.response?.data?.detail || t('common.saveFailed')
  }
}

async function deactivate(id) {
  await usersStore.deactivateUser(id)
}

function openDeptForm() {
  editingDept.value = null
  showDeptForm.value = true
}

function editDept(dept) {
  editingDept.value = dept
  deptForm.code = dept.code
  deptForm.name_ar = dept.name_ar
  deptForm.name_en = dept.name_en || ''
  showDeptForm.value = true
}

function closeDeptForm() {
  showDeptForm.value = false
  editingDept.value = null
  deptFormError.value = ''
  deptForm.code = ''
  deptForm.name_ar = ''
  deptForm.name_en = ''
}

async function saveDept() {
  deptFormError.value = ''
  try {
    if (editingDept.value) {
      await departmentsStore.updateDepartment(editingDept.value.id, {
        name_ar: deptForm.name_ar,
        name_en: deptForm.name_en,
      })
    } else {
      await departmentsStore.createDepartment({ ...deptForm })
    }
    closeDeptForm()
  } catch (e) {
    deptFormError.value = e.response?.data?.detail || t('common.saveFailed')
  }
}
</script>

<style scoped>
.tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); flex-wrap: wrap; }
.tab { padding: 10px 20px; background: transparent; border: none; cursor: pointer; color: var(--text-secondary); border-bottom: 2px solid transparent; }
.tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
.tab-panel { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.hint { color: var(--text-secondary); font-size: 13px; margin-bottom: 16px; }
.roles-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.role-card { padding: 16px; border: 1px solid var(--border-color); border-radius: 8px; }
.role-card h3 { color: var(--color-primary); margin-bottom: 8px; }
.role-card ul { margin: 0; padding-inline-start: 18px; color: var(--text-secondary); font-size: 13px; }
.role-card li { margin-bottom: 4px; }
.btn-small { padding: 4px 10px; margin-inline-end: 6px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; color: var(--text-primary); }
.btn-small.danger { border-color: var(--color-danger); color: var(--color-danger); }
.checkbox-label { display: flex; align-items: center; gap: 8px; margin: 12px 0; }
.checkbox-label input { width: auto; margin: 0; }
.secret-label { display: block; color: var(--text-secondary); font-size: 13px; margin: 12px 0 6px; }
.secret-row { display: flex; align-items: center; gap: 8px; }
.secret-row code { flex: 1; padding: 10px; background: var(--bg-body); border: 1px solid var(--border-color); border-radius: 6px; font-family: monospace; font-size: 16px; letter-spacing: 1px; overflow-wrap: anywhere; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: var(--bg-card); padding: 24px; border-radius: 12px; width: 100%; max-width: 460px; max-height: 90vh; overflow-y: auto; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-secondary { padding: 10px 20px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; color: var(--text-primary); }
.error { color: var(--color-danger); font-size: 13px; margin: 8px 0 0; }
.system-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.system-card { background: var(--bg-muted); border-radius: 10px; padding: 18px; text-align: center; }
.system-value { font-size: 22px; font-weight: 700; color: var(--color-primary); }
.system-value.ok { color: var(--color-success); }
.system-value.bad { color: var(--color-danger); }
.system-label { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }
</style>
