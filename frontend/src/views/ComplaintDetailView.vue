<template>
  <div>
    <AppHeader />
    <main class="content">
      <button @click="$router.back()">← Back</button>
      <h1>Complaint Details</h1>
      <div class="detail-card">
        <p><strong>Number:</strong> INS-2026-0891</p>
        <p><strong>Title:</strong> مخالفة في إجراءات التعاقد</p>
        <p><strong>Status:</strong> <span class="badge urgent">Urgent</span></p>
        <p><strong>Description:</strong> تم التعاقد دون إجراء مناقصة علنية</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
</script>
