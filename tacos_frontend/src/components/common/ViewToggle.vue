<template>
  <div class="view-toggle" role="tablist" aria-label="视图切换">
    <button
      class="btn-modern sbtn seg-btn"
      :class="{ active: modelValue === 'table' }"
      role="tab"
      :aria-selected="modelValue === 'table'"
      @click="$emit('update:modelValue', 'table')"
      title="表格视图"
      aria-label="表格视图"
    >
      <svg class="seg-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="6" cy="7" r="1.6" fill="currentColor" stroke="none" />
        <line
          x1="9.5"
          y1="7"
          x2="20"
          y2="7"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        />
        <circle cx="6" cy="12" r="1.6" fill="currentColor" stroke="none" />
        <line
          x1="9.5"
          y1="12"
          x2="20"
          y2="12"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        />
        <circle cx="6" cy="17" r="1.6" fill="currentColor" stroke="none" />
        <line
          x1="9.5"
          y1="17"
          x2="20"
          y2="17"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        />
      </svg>
      <span class="sr-only">表格视图</span>
    </button>
    <button
      class="btn-modern sm-btn seg-btn"
      :class="{ active: modelValue === 'card' }"
      role="tab"
      :aria-selected="modelValue === 'card'"
      @click="$emit('update:modelValue', 'card')"
      title="卡片视图"
      aria-label="卡片视图"
    >
      <svg class="seg-icon" viewBox="0 0 24 24" aria-hidden="true">
        <rect x="4.5" y="4.5" width="7" height="7" rx="1.5" />
        <rect x="13" y="4.5" width="7" height="7" rx="1.5" />
        <rect x="4.5" y="13" width="7" height="7" rx="1.5" />
        <rect x="13" y="13" width="7" height="7" rx="1.5" />
      </svg>
      <span class="sr-only">卡片视图</span>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ViewToggle',
  props: {
    modelValue: {
      type: String,
      default: 'table',
      validator: value => ['table', 'card'].includes(value)
    }
  },
  emits: ['update:modelValue']
}
</script>

<style lang="scss" scoped>
.view-toggle {
  display: inline-flex;
  gap: 6px;
  margin-right: 8px;
  background: #f3f4f6;
  padding: 2px;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 1px, 1px);
  white-space: nowrap;
  border: 0;
}

.seg-btn {
  border: none;
  background: transparent;
  color: #374151;
  padding: 6px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;

  .seg-icon {
    width: 18px;
    height: 18px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.5;
  }

  &:hover {
    background: #e5e7eb;
  }

  &.active {
    background: #ffffff;
    color: #111827;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  }

  &:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
