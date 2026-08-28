<template>
  <div id="app" :dir="locale === 'ar' ? 'rtl' : 'ltr'">
    <router-view />
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { locale } = useI18n()
</script>

<style>
@import './assets/styles/main.css';
</style>
