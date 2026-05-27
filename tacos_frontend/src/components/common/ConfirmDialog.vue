<template>
  <teleport to="body">
    <div v-if="visible" class="cd-overlay" @click.self="onCancel">
      <div
        class="cd-container"
        :style="{ width }"
        role="dialog"
        aria-modal="true"
        :aria-label="title || '确认操作'"
      >
        <div class="cd-header" v-if="title">
          <div class="cd-title">{{ title }}</div>
        </div>
        <div v-if="description" class="cd-body">
          <div class="cd-desc">{{ description }}</div>
        </div>
        <div class="cd-footer">
          <button class="btn-modern ghost sm-btn" @click="onCancel">{{ cancelText }}</button>
          <button
            class="btn-modern sm-btn"
            :class="danger ? 'danger' : 'primary'"
            @click="onConfirm"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
export default {
  name: 'ConfirmDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    width: {
      type: String,
      default: '280px'
    },
    title: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    confirmText: {
      type: String,
      default: '确定'
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    danger: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'confirm', 'cancel'],
  setup(_props, { emit }) {
    const onCancel = () => {
      emit('update:visible', false)
      emit('cancel')
    }
    const onConfirm = () => {
      emit('confirm')
    }
    return { onCancel, onConfirm }
  }
}
</script>

<style scoped>
.cd-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}
.cd-container {
  max-width: 92vw;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  padding: 10px 12px;
}
.cd-header {
  padding: 10px 12px;
}
.cd-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}
.cd-body {
  padding: 8px 12px;
}
.cd-desc {
  color: #6b7280;
  line-height: 1.6;
  white-space: pre-wrap;
  margin: 0;
}
.cd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 12px;
}
</style>
