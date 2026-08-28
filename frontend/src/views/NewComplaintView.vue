<template>
  <AppLayout>
    <main class="content">
      <h1>New Complaint</h1>
      <form @submit.prevent="submit">
        <input v-model="form.title_ar" placeholder="Title (AR)" required />
        <textarea v-model="form.description" placeholder="Description" required rows="5"></textarea>
        <select v-model="form.category" required>
          <option value="">Select Category</option>
          <option value="financial_fraud">Financial Fraud</option>
          <option value="procurement_violation">Procurement Violation</option>
          <option value="bribery">Bribery</option>
        </select>
        <button type="submit" class="btn-primary">Save</button>
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
const form = reactive({ title_ar: '', description: '', category: '', priority: 'normal' })

async function submit() {
  await store.create(form)
  router.push('/complaints')
}
</script>
