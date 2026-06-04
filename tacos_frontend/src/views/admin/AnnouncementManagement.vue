<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header">
          <h3>系统公告管理</h3>
          <div class="actions">
            <ViewToggle v-model="viewMode" />
            <button class="btn-modern primary sm-btn" @click="openCreate">
              <i-lucide-plus class="btn-icon" />
              <span>新增公告</span>
            </button>
          </div>
        </div>

        <div
          class="table-wrapper"
          v-if="viewMode === 'table'"
          :aria-busy="loading"
          style="margin-top: 10px"
        >
          <div v-if="loading" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <table class="data-table" v-else>
            <colgroup>
              <col class="table-col-time" />
              <col class="table-col-title" />
              <col class="table-col-content" />
              <col class="table-col-action" />
            </colgroup>
            <thead>
              <tr>
                <th class="time-col">发布时间</th>
                <th class="title-col">公告标题</th>
                <th class="content-col">公告内容</th>
                <th class="sticky-right action-col">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="announcements.length === 0">
                <td colspan="4" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in announcements" :key="row.id">
                <td class="time-col">{{ formatDateTime(row.publish_time) }}</td>
                <td class="title-col" style="font-weight: bold">
                  {{ row.title || '(无标题)' }}
                </td>
                <td class="content-col content-cell">{{ row.content }}</td>
                <td class="sticky-right action-col">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="openEdit(row)">
                      <i-lucide-pencil class="btn-icon" />
                      <span>编辑</span>
                    </button>
                    <button class="btn-modern danger xsm-btn" @click="confirmDelete(row)">
                      <i-lucide-trash-2 class="btn-icon" />
                      <span>删除</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="cards-wrapper" :aria-busy="loading" style="margin-top: 20px">
          <div v-if="loading" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <div v-else>
            <div v-if="announcements.length === 0" class="empty-cell">暂无数据</div>
            <div v-else class="cards-grid">
              <div class="announcement-card" v-for="row in announcements" :key="row.id">
                <div class="card-head">
                  <div class="time">{{ formatDateTime(row.publish_time) }}</div>
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="openEdit(row)">
                      <i-lucide-pencil class="btn-icon" />
                      <span>编辑</span>
                    </button>
                    <button class="btn-modern danger xsm-btn" @click="confirmDelete(row)">
                      <i-lucide-trash-2 class="btn-icon" />
                      <span>删除</span>
                    </button>
                  </div>
                </div>
                <div class="title">{{ row.title || '(无标题)' }}</div>
                <div class="content">{{ row.content }}</div>
              </div>
            </div>
          </div>
        </div>

        <Pagination
          :current-page="query.page"
          :total-pages="totalPages"
          :page-size="query.page_size"
          :total="total"
          @update:current-page="handlePageChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </div>

    <div v-if="dialogVisible" class="modal-overlay" @click.self="dialogVisible = false">
      <div class="card" style="width: 80%; max-width: 640px">
        <div class="card-content">
          <div class="modal-header">
            <h3>{{ editing ? '编辑公告' : '新增公告' }}</h3>
          </div>
          <div style="height: 1px; background: var(--border, #e5e7eb); margin: 10px 0" />
          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">公告标题</label>
              <textarea
                class="input-modern"
                v-model="form.title"
                rows="2"
                maxlength="200"
                placeholder="请输入公告标题"
              />
            </div>
            <div class="form-item">
              <label class="form-label">发布时间</label>
              <el-date-picker
                v-model="form.publish_time"
                type="datetime"
                placeholder="选择发布时间"
                format="YYYY-MM-DD HH:mm:ss"
              />
            </div>
            <div class="form-item">
              <label class="form-label">公告内容</label>
              <textarea
                class="input-modern"
                v-model="form.content"
                rows="6"
                maxlength="5000"
                placeholder="请输入公告内容"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-modern ghost" @click="dialogVisible = false">
              <i-lucide-x class="btn-icon" />
              <span>取消</span>
            </button>
            <button class="btn-modern primary" @click="submit">
              <i-lucide-save class="btn-icon" />
              <span>保存</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除公告确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteConfirmDialog.visible"
      title="删除公告"
      description="确认删除该公告吗？"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import {
  getAnnouncements,
  createAnnouncement,
  updateAnnouncement,
  deleteAnnouncement
} from '@/api/common'
import { formatDateTime } from '@/utils/format'
import notify from '@/utils/notify'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import ViewToggle from '@/components/common/ViewToggle.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

dayjs.extend(utc)
dayjs.extend(timezone)

export default {
  name: 'AnnouncementManagement',
  components: {
    ViewToggle,
    Pagination,
    ConfirmDialog
  },
  setup() {
    const announcements = ref([])
    const total = ref(0)
    const loading = ref(true)
    const dialogVisible = ref(false)
    const editing = ref(false)
    const currentId = ref(null)
    const viewMode = ref('table') // 'table' | 'card'
    let listRequestSeq = 0

    // 删除确认对话框
    const deleteConfirmDialog = reactive({
      visible: false,
      row: null
    })

    const query = reactive({
      page: 1,
      page_size: 10
    })

    const form = reactive({
      title: '',
      publish_time: '',
      content: ''
    })

    const totalPages = computed(() => {
      const size = Number(query.page_size) || 10
      if (!total.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(total.value / size))
    })

    const loadList = async () => {
      const requestSeq = ++listRequestSeq
      loading.value = true
      try {
        const res = await getAnnouncements(query)
        if (requestSeq !== listRequestSeq) {
          return
        }
        announcements.value = res.data?.results || []
        total.value = res.data?.count || 0
      } finally {
        if (requestSeq === listRequestSeq) {
          loading.value = false
        }
      }
    }

    const resetForm = () => {
      form.title = ''
      form.publish_time = ''
      form.content = ''
    }

    const openCreate = () => {
      editing.value = false
      currentId.value = null
      resetForm()
      // 使用 Date 对象作为 v-model，避免重复时区转换
      form.publish_time = new Date()
      dialogVisible.value = true
    }

    const openEdit = row => {
      editing.value = true
      currentId.value = row.id
      form.title = row.title || ''
      // 直接使用 Date 对象（由后端 ISO 字符串解析），避免 -8 小时回退
      form.publish_time = new Date(row.publish_time)
      form.content = row.content
      dialogVisible.value = true
    }

    const submit = async () => {
      try {
        if (!form.content || !form.content.trim()) {
          notify.error('公告内容不能为空')
          return
        }
        if (!form.publish_time) {
          notify.error('请选择发布时间')
          return
        }
        const payload = {
          title: (form.title || '').trim(),
          publish_time:
            form.publish_time instanceof Date
              ? form.publish_time.toISOString()
              : dayjs(form.publish_time).toISOString(),
          content: form.content.trim()
        }
        if (editing.value) {
          await updateAnnouncement(currentId.value, payload)
          notify.success('更新成功')
        } else {
          await createAnnouncement(payload)
          notify.success('创建成功')
        }
        dialogVisible.value = false
        await loadList()
      } catch (e) {
        // 错误提示由拦截器处理
      }
    }

    // 打开删除确认对话框
    const confirmDelete = row => {
      deleteConfirmDialog.row = row
      deleteConfirmDialog.visible = true
    }

    // 确认删除公告
    const handleConfirmDelete = async () => {
      try {
        await deleteAnnouncement(deleteConfirmDialog.row.id)
        notify.success('删除成功')
        deleteConfirmDialog.visible = false
        await loadList()
      } catch (e) {
        notify.error('删除失败')
      }
    }

    const handlePageChange = page => {
      query.page = page
      loadList()
    }

    const handleSizeChange = size => {
      query.page_size = size
      loadList()
    }

    onMounted(() => {
      loadList()
    })

    // 移除本地字符串与 ISO 互转的辅助方法，统一由 Date/ISO 处理

    return {
      announcements,
      total,
      loading,
      dialogVisible,
      editing,
      query,
      form,
      totalPages,
      openCreate,
      openEdit,
      submit,
      confirmDelete,
      deleteConfirmDialog,
      handleConfirmDelete,
      handlePageChange,
      handleSizeChange,
      formatDateTime,
      viewMode
    }
  }
}
</script>

<style lang="scss" scoped>
.page-container {
  padding: 20px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
}
.seg-btn:hover {
  background: #e5e7eb;
}
.seg-btn.active {
  background: #ffffff;
  color: #111827;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.seg-icon {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.6;
}

.table-wrapper {
  width: 100%;
  overflow: auto;
}
.loading-area {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
}
.loading-text {
  color: #6b7280;
  font-size: 14px;
}

.data-table {
  width: 100%;
  min-width: 860px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}
.data-table .table-col-time {
  width: 180px;
}
.data-table .table-col-title {
  width: 220px;
}
.data-table .table-col-content {
  width: auto;
}
.data-table .table-col-action {
  width: 160px;
}
.data-table thead th {
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--background);
  font-size: 13px;
  white-space: nowrap;
}
.data-table tbody td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  color: #374151;
  overflow-wrap: anywhere;
  word-break: break-word;
  transition: background-color 0.15s ease;
}
.data-table tbody tr:hover td {
  background: #f9fafb;
}
.data-table .time-col,
.data-table .title-col {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.data-table .content-cell {
  white-space: pre-wrap;
  line-height: 1.6;
}
.data-table .action-col {
  text-align: center;
}
.data-table .action-col .row-actions {
  justify-content: center;
}
.data-table thead th.sticky-right {
  position: sticky;
  right: 0;
  z-index: 2;
  background: var(--background);
  border-left: 1px solid var(--border);
}
.data-table tbody td.sticky-right {
  position: sticky;
  right: 0;
  z-index: 1;
  background: #fff;
  border-left: 1px solid var(--border);
}
.data-table tbody tr:hover td.sticky-right {
  background: #f9fafb;
}
.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
}

.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.announcement-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 18px;
  background: #fff;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}
.announcement-card:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}
.announcement-card .card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.announcement-card .time {
  font-size: 12px;
  color: #6b7280;
}
.announcement-card .title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #111827;
}
.announcement-card .content {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #374151;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 10px;
}
.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.card-content {
  padding: 10px 12px;
}
.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-size: 13px;
  color: #6b7280;
}
</style>
