<template>
  <AppLayout>
    <main class="content">
      <h1>{{ $t('complaints.new') }}</h1>
      <form @submit.prevent="submit">
        <input v-model="form.title_ar" :placeholder="$t('complaint.titleArPlaceholder')" required />
        <input v-model="form.title_en" :placeholder="$t('complaint.titleEnPlaceholder')" />
        <textarea v-model="form.description" :placeholder="$t('complaint.descriptionPlaceholder')" required rows="5"></textarea>
        <select v-model="form.category" required>
          <option value="">{{ $t('complaint.selectCategory') }}</option>
          <option v-for="key in Object.keys($tm('complaint.category'))" :key="key" :value="key">{{ $t(`complaint.category.${key}`) }}</option>
        </select>
        <select v-model="form.priority" required>
          <option v-for="key in Object.keys($tm('complaint.priority'))" :key="key" :value="key">{{ $t(`complaint.priority.${key}`) }}</option>
        </select>
        <button type="submit" class="btn-primary">{{ $t('common.save') }}</button>
      </form>
    </main>
  </AppLayout>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useComplaintStore } from '../stores/complaints'
import AppLayout from '../components/AppLayout.vue'

const router = useRouter()
const store = useComplaintStore()
const form = reactive({ title_ar: '', title_en: '', description: '', category: '', priority: 'normal' })

async function submit() {
  await store.create(form)
  router.push('/complaints')
}
</script>
