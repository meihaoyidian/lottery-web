<template>
  <div v-if="show" class="loading-overlay">
    <div class="loading-spinner"></div>
    <span class="loading-text">加载中...</span>
  </div>
</template>

<script setup>
defineProps({ show: { type: Boolean, default: true } })
</script>

<style scoped>
.loading-overlay {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 120px 0; gap: 16px;
}
.loading-spinner {
  width: 36px; height: 36px; border: 3px solid #e8ecf2;
  border-top-color: #2563eb; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-text { font-size: 14px; color: #94a3b8; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
