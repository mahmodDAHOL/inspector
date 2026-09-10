<template>
  <div class="app-layout" :class="{ rtl: locale === 'ar' }">
    <aside class="sidebar">
      <div class="brand">
        <img src="/logo.jpg" alt="" class="logo-box" />
        <div class="brand-text">
          <h1 class="app-title">{{ $t('landing.title') }}</h1>
          <p class="app-subtitle">{{ $t('landing.subtitle') }}</p>
        </div>
      </div>

      <nav class="nav-links">
        <router-link
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          active-class="active"
        >
          <span class="link-icon">{{ link.icon }}</span>
          <span class="link-label">{{ link.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <button class="lang-toggle" @click="toggleLocale">
          {{ locale === 'ar' ? 'English' : 'العربية' }}
        </button>
        <button class="logout-btn" @click="logout">
          {{ $t('landing.logout') }}
        </button>
      </div>
    </aside>

    <div class="main">
      <AppHeader />
      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import AppHeader from './AppHeader.vue'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const userRole = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}').role || ''
  } catch {
    return ''
  }
})

const links = computed(() => {
  const base = [
    { to: '/dashboard', label: t('dashboard.title'), icon: '▣' },
    { to: '/complaints', label: t('complaints.title'), icon: '☰' },
    { to: '/complaints/new', label: t('complaints.new'), icon: '✎' },
    { to: '/reports', label: t('landing.reports'), icon: '▤' },
    { to: '/audit', label: t('landing.audit'), icon: '◷' }
  ]
  if (['admin', 'super_admin'].includes(userRole.value)) {
    base.push({ to: '/admin', label: t('admin.title'), icon: '⚙' })
  }
  return base
})

function toggleLocale() {
  const next = locale.value === 'ar' ? 'en' : 'ar'
  locale.value = next
  localStorage.setItem('locale', next)
  document.documentElement.setAttribute('lang', next)
  document.documentElement.setAttribute('dir', next === 'ar' ? 'rtl' : 'ltr')
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('temp_token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-body);
}

.sidebar {
  width: 260px;
  background: var(--color-primary);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  padding: 24px;
  position: fixed;
  inset-block-start: 0;
  inset-block-end: 0;
  inset-inline-start: 0;
  box-shadow: 4px 0 16px rgba(27, 94, 94, 0.15);
  z-index: 100;
}

.app-layout.rtl .sidebar {
  box-shadow: -4px 0 16px rgba(27, 94, 94, 0.15);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-box {
  width: 50px;
  height: 50px;
  background: #ffffff;
  border-radius: 12px;
  object-fit: contain;
  padding: 5px;
  flex-shrink: 0;
}

.brand-text {
  min-width: 0;
}

.app-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 4px;
  line-height: 1.2;
}

.app-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  line-height: 1.2;
}

.nav-links {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.88);
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  font-size: 14px;
}

.nav-link:hover,
.nav-link.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.link-icon {
  font-size: 16px;
  width: 22px;
  text-align: center;
}

.link-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.lang-toggle,
.logout-btn {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.lang-toggle:hover,
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.logout-btn {
  border-color: var(--color-gold);
  background: rgba(166, 139, 91, 0.2);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-inline-start: 260px;
  min-height: 100vh;
}

.page-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    position: relative;
    inset: auto;
  }

  .main {
    margin-inline-start: 0;
  }

  .app-layout {
    flex-direction: column;
  }

  .nav-links {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .nav-link {
    flex: 1;
    min-width: 140px;
  }
}
</style>
