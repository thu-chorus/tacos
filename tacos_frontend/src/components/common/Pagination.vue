<template>
  <div class="pagination">
    <div class="pagination-center">
      <button
        class="btn-modern ghost xsm-btn pagination-btn"
        :disabled="currentPage <= 1"
        @click="handlePrevPage"
        title="上一页"
        aria-label="上一页"
      >
        <svg class="pagination-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <span class="page-info" style="font-size: 14px"
        >第 {{ currentPage }} / {{ totalPages }} 页</span
      >
      <button
        class="btn-modern ghost xsm-btn pagination-btn"
        :disabled="currentPage >= totalPages"
        @click="handleNextPage"
        title="下一页"
        aria-label="下一页"
      >
        <svg class="pagination-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
    <div class="pagination-center">
      <span class="page-info">每页</span>
      <select class="input-modern size-select" :value="pageSize" @change="handleSizeChange">
        <option :value="10">10</option>
        <option :value="20">20</option>
        <option :value="50">50</option>
      </select>
      <span class="page-info">条，共 {{ total }} 条</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    currentPage: {
      type: Number,
      required: true,
      default: 1
    },
    totalPages: {
      type: Number,
      required: true,
      default: 1
    },
    pageSize: {
      type: Number,
      required: true,
      default: 10
    },
    total: {
      type: Number,
      required: true,
      default: 0
    }
  },
  emits: ['update:currentPage', 'update:pageSize'],
  methods: {
    handlePrevPage() {
      if (this.currentPage > 1) {
        this.$emit('update:currentPage', this.currentPage - 1)
      }
    },
    handleNextPage() {
      if (this.currentPage < this.totalPages) {
        this.$emit('update:currentPage', this.currentPage + 1)
      }
    },
    handleSizeChange(e) {
      this.$emit('update:pageSize', Number(e.target.value))
    }
  }
}
</script>

<style lang="scss" scoped>
.pagination {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
}

.pagination-center {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.page-info {
  font-size: 13px;
  color: #6b7280;
}

.size-select {
  width: 48px;
  height: 24px;
  font-size: 12px;
  padding: 2px 6px;
}

.pagination-btn {
  padding: 6px;
  min-width: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.2s ease;
  border-radius: 6px;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &:hover:not(:disabled) {
    background: #f3f4f6;
  }
}

.pagination-icon {
  width: 16px;
  height: 16px;
  stroke: currentColor;
  fill: none;
  stroke-width: 2;
}
</style>
