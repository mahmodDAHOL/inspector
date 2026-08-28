<template>
  <div class="not-found">
    <h1>404</h1>
    <p>Page not found</p>
    <button @click="$router.push('/')">Go Home</button>
  </div>
</template>

<style scoped>
.not-found { text-align: center; padding: 100px 20px; }
h1 { font-size: 72px; color: var(--color-primary); }
</style>
