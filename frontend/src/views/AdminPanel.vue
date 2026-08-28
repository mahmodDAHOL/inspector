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
          <button class="btn-primary" @click="showUserForm = true">+ {{ $t('admin.addUser') }}</button>
        </div>

        <table>
          <thead>
            <tr>
              <th>{{ $t('admin.username') }}</th>
              <th>{{ $t('admin.fullName') }}</th>
              <th>{{ $t('admin.role') }}</th>
              <th>{{ $t('admin.status') }}</th>
              <th>{{ $t('admin.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in store.users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.full_name_ar }}</td>
              <td><span class="badge">{{ user.role }}</span></td>
              <td><span :class="['badge', user.is_active ? 'closed' : 'urgent']">{{ user.is_active ? $t('admin.active') : $t('admin.inactive') }}</span></td>
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
        <div class="roles-grid">
          <div v-for="role in store.roles" :key="role" class="role-card">
            <h3>{{ role }}</h3>
            <p>{{ rolePermissions[role]?.join(', ') }}</p>
          </div>
        </div>
      </div>

      <div v-else class="tab-panel">
        <h2>{{ $t('admin.system') }}</h2>
        <p>{{ $t('admin.comingSoon') }}</p>
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
              <option v-for="role in store.roles" :key="role" :value="role">{{ role }}</option>
            </select>
            <input v-if="!editingUser" v-model="form.password" type="password" :placeholder="$t('admin.password')" required />
            <label class="checkbox-label">
              <input v-model="form.is_active" type="checkbox" />
              {{ $t('admin.active') }}
            </label>
            <div class="form-actions">
              <button type="button" class="btn-secondary" @click="closeForm">{{ $t('common.cancel') }}</button>
              <button type="submit" class="btn-primary">{{ $t('common.save') }}</button>
            </div>
          </form>
        </div>
      </div>
    </main>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useUsersStore } from '../stores/users'

const store = useUsersStore()
const activeTab = ref('users')
const showUserForm = ref(false)
const editingUser = ref(null)

const tabs = [
  { key: 'users', label: 'Users' },
  { key: 'roles', label: 'Roles & Permissions' },
  { key: 'system', label: 'System' },
]

const rolePermissions = {
  super_admin: ['Full system access'],
  admin: ['Manage users', 'View reports', 'Manage complaints'],
  senior_inspector: ['Assign complaints', 'Sign reports', 'Manage investigations'],
  inspector: ['View complaints', 'Add notes', 'Update status'],
  viewer: ['Read-only access'],
}

const form = reactive({
  username: '',
  full_name_ar: '',
  full_name_en: '',
  email: '',
  role: '',
  password: '',
  is_active: true,
})

onMounted(() => {
  store.fetchUsers()
  store.fetchRoles()
})

function editUser(user) {
  editingUser.value = user
  form.username = user.username
  form.full_name_ar = user.full_name_ar
  form.full_name_en = user.full_name_en || ''
  form.email = user.email || ''
  form.role = user.role
  form.password = ''
  form.is_active = user.is_active
  showUserForm.value = true
}

function closeForm() {
  showUserForm.value = false
  editingUser.value = null
  form.username = ''
  form.full_name_ar = ''
  form.full_name_en = ''
  form.email = ''
  form.role = ''
  form.password = ''
  form.is_active = true
}

async function saveUser() {
  if (editingUser.value) {
    await store.updateUser(editingUser.value.id, {
      full_name_ar: form.full_name_ar,
      full_name_en: form.full_name_en,
      email: form.email,
      role: form.role,
      is_active: form.is_active,
    })
  } else {
    await store.createUser({ ...form })
  }
  closeForm()
}

async function deactivate(id) {
  await store.deactivateUser(id)
}
</script>

<style scoped>
.tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); }
.tab { padding: 10px 20px; background: transparent; border: none; cursor: pointer; color: var(--text-secondary); border-bottom: 2px solid transparent; }
.tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
.tab-panel { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.roles-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.role-card { padding: 16px; border: 1px solid var(--border-color); border-radius: 8px; }
.role-card h3 { color: var(--color-primary); margin-bottom: 8px; }
.role-card p { color: var(--text-secondary); font-size: 13px; }
.btn-small { padding: 4px 10px; margin-inline-end: 6px; border: 1px solid var(--border-color); background: transparent; border-radius: 6px; cursor: pointer; }
.btn-small.danger { border-color: var(--color-danger); color: var(--color-danger); }
.checkbox-label { display: flex; align-items: center; gap: 8px; margin: 12px 0; }
.checkbox-label input { width: auto; margin: 0; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal { background: var(--bg-card); padding: 24px; border-radius: 12px; width: 100%; max-width: 460px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.btn-secondary { padding: 10px 20px; border: 1px solid var(--border-color); background: transparent; border-radius: 8px; cursor: pointer; }
</style>
