<template>
  <div class="landing-page">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo-box">م</div>
        <h1 class="app-title">{{ $t('landing.title') }}</h1>
        <p class="app-subtitle">{{ $t('landing.subtitle') }}</p>
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
        <button v-if="isAuthenticated" class="logout-btn" @click="logout">
          {{ $t('landing.logout') }}
        </button>
      </div>
    </aside>

    <main class="content">
      <div class="hero">
        <h2>{{ $t('landing.welcome') }}</h2>
        <p>{{ $t('landing.description') }}</p>
        <router-link to="/dashboard" class="cta-button">
          {{ $t('landing.enterDashboard') }}
        </router-link>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()

const isAuthenticated = computed(() => !!localStorage.getItem('access_token'))

const links = computed(() => [
  { to: '/dashboard', label: t('dashboard.title'), icon: '▣' },
  { to: '/complaints', label: t('complaints.title'), icon: '☰' },
  { to: '/complaints/new', label: t('complaints.new'), icon: '✎' },
  { to: '/reports', label: t('landing.reports'), icon: '▤' },
  { to: '/audit', label: t('landing.audit'), icon: '◷' },
  { to: '/login', label: isAuthenticated.value ? t('landing.switchUser') : t('landing.login'), icon: '⎆' }
])

function toggleLocale() {
  const next = locale.value === 'ar' ? 'en' : 'ar'
  locale.value = next
  localStorage.setItem('locale', next)
  document.documentElement.setAttribute('lang', next)
  document.documentElement.setAttribute('dir', next === 'ar' ? 'rtl' : 'ltr')
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('temp_token')
  router.push('/login')
}
</script>

<style scoped>
.landing-page {
  display: flex;
  min-height: 100vh;
  background: #f8f7f4;
}

.sidebar {
  width: 280px;
  background: #1B5E5E;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  padding: 32px 24px;
  box-shadow: 4px 0 16px rgba(27, 94, 94, 0.15);
}

.brand {
  text-align: center;
  margin-bottom: 40px;
}

.logo-box {
  width: 72px;
  height: 72px;
  background: #A68B6A;
  color: #ffffff;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  margin: 0 auto 16px;
}

.app-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 6px;
}

.app-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
}

.nav-links {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
}

.nav-link:hover,
.nav-link.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.link-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.link-label {
  font-size: 15px;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: auto;
}

.lang-toggle,
.logout-btn {
  width: 100%;
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.lang-toggle:hover,
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.logout-btn {
  border-color: #A68B6A;
  background: rgba(166, 139, 106, 0.2);
}

.content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.hero {
  max-width: 560px;
  text-align: center;
}

.hero h2 {
  font-size: 36px;
  color: #1B5E5E;
  margin-bottom: 16px;
}

.hero p {
  font-size: 17px;
  color: #4a5a5a;
  line-height: 1.7;
  margin-bottom: 28px;
}

.cta-button {
  display: inline-block;
  padding: 14px 32px;
  background: #A68B6A;
  color: #ffffff;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  transition: background 0.2s;
}

.cta-button:hover {
  background: #8f7658;
}

@media (max-width: 768px) {
  .landing-page {
    flex-direction: column;
  }

  .sidebar {
    width: auto;
    padding: 20px;
  }

  .nav-links {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
  }

  .nav-link {
    flex: 1;
    min-width: 120px;
  }
}
</style>
