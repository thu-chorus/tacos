<template>
  <div class="page-loading" role="status" aria-live="polite">
    <span class="loading-spinner" aria-hidden="true" />
    <span class="loading-text">{{ text }}</span>
  </div>
</template>

<script>
export default {
  name: 'PageLoading',
  props: {
    text: {
      type: String,
      default: '加载中...'
    }
  }
}
</script>

<style scoped>
.page-loading {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-text {
  color: #6b7280;
  font-size: 14px;
}
</style>
