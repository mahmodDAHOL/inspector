<template>
  <AppLayout>
    <main class="content">
      <h1>Audit Log</h1>
      <table>
        <thead><tr><th>Time</th><th>User</th><th>Action</th><th>Table</th></tr></thead>
        <tbody>
          <tr><td>2026-08-28 10:00</td><td>admin</td><td>INSERT</td><td>complaints</td></tr>
        </tbody>
      </table>
    </main>
  </AppLayout>
</template>

<script setup>
import AppLayout from '../components/AppLayout.vue'
</script>
