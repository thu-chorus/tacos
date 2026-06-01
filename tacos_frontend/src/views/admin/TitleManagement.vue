<template>
  <div class="page-container">
    <div class="board-card">
      <div class="board-card-content">
        <div class="header">
          <div class="header-text">
            <h3>称号管理</h3>
            <p class="description">创建、编辑、删除称号，并为队员授予或移除称号</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content">
        <div class="header">
          <h3>称号列表</h3>
          <div class="actions">
            <button class="btn-modern warning sm-btn" @click="handleUpdateBirthdayTitles">
              更新本月寿星
            </button>
            <button class="btn-modern primary sm-btn" @click="openCreate">新建称号</button>
          </div>
        </div>

        <div class="table-wrapper" :aria-busy="loading" style="margin-top: 10px">
          <div v-if="loading" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <table class="data-table" v-else>
            <thead>
              <tr>
                <th style="min-width: 140px">名称</th>
                <th style="min-width: 180px">外观</th>
                <th style="min-width: 100px">拥有人数</th>
                <th class="sticky-right" style="min-width: 80px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="tableData.length === 0">
                <td colspan="4" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in tableData" :key="row.id">
                <td>{{ row.name }}</td>
                <td>
                  <TitleBadge :title="row" />
                </td>
                <td>{{ row.owners_count }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern warning xsm-btn" @click="goDetail(row)">管理</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <Pagination
          :current-page="pagination.page"
          :total-pages="totalPages"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          @update:current-page="handleCurrentChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </div>

    <!-- 新建/编辑称号对话框 -->
    <el-dialog
      v-model="editing.visible"
      :title="editing.id ? '编辑称号' : '新建称号'"
      :width="dialogWidth"
    >
      <el-form :model="editing.form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="editing.form.name" placeholder="请输入称号名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            type="textarea"
            v-model="editing.form.description"
            placeholder="请输入称号描述"
          />
        </el-form-item>
        <el-form-item label="外观JSON">
          <el-input
            type="textarea"
            v-model="editing.form.appearance"
            :rows="8"
            placeholder="输入合法 JSON"
          />
        </el-form-item>
        <el-form-item label="创建日期">
          <el-date-picker
            v-model="editing.form.created_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="留空默认当天"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="editing.visible = false"
          style="margin-right: 8px"
        >
          取消
        </button>
        <button class="btn-modern primary sm-btn" :disabled="savingTitle" @click="saveTitle">
          {{ savingTitle ? '保存中...' : '保存' }}
        </button>
      </template>
    </el-dialog>

    <!-- 更新本月寿星确认对话框 -->
    <ConfirmDialog
      v-model:visible="birthdayConfirmDialog.visible"
      title="更新本月寿星"
      description="确认更新本月寿星称号？这将清空现有的授予记录并重新分配给本月生日的队员。"
      confirm-text="确认更新"
      cancel-text="取消"
      :danger="false"
      @confirm="handleConfirmBirthdayUpdate"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { notify } from '@/utils/notify'
import { getTitleList, createTitle, updateBirthdayTitles } from '@/api/personnel'
import TitleBadge from '@/components/common/TitleBadge.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'TitleManagement',
  components: { TitleBadge, Pagination, ConfirmDialog },
  setup() {
    const router = useRouter()

    const loading = ref(false)
    const savingTitle = ref(false)
    const allTitles = ref([])
    let listRequestSeq = 0

    const pagination = reactive({
      page: 1,
      pageSize: 20,
      total: 0
    })

    const editing = reactive({
      visible: false,
      id: null,
      form: {
        name: '',
        description: '',
        appearance: '{\n  "bg_color": "#5B8DEF",\n  "text_color": "#FFFFFF"\n}',
        created_date: ''
      }
    })

    // 更新本月寿星确认对话框
    const birthdayConfirmDialog = reactive({
      visible: false
    })

    // 加载称号列表
    const loadTitles = async () => {
      const requestSeq = ++listRequestSeq
      loading.value = true
      try {
        const res = await getTitleList({ page_size: 1000 })
        if (requestSeq !== listRequestSeq) {
          return
        }
        allTitles.value = Array.isArray(res.data?.results) ? res.data.results : res.data || []
        pagination.total = allTitles.value.length
        // 确保当前页不超出范围
        const maxPage = Math.max(1, Math.ceil(pagination.total / pagination.pageSize) || 1)
        if (pagination.page > maxPage) {
          pagination.page = maxPage
        }
      } finally {
        if (requestSeq === listRequestSeq) {
          loading.value = false
        }
      }
    }

    // 分页后的表格数据
    const tableData = computed(() => {
      const start = (pagination.page - 1) * pagination.pageSize
      return allTitles.value.slice(start, start + pagination.pageSize)
    })

    const totalPages = computed(() => {
      const size = Number(pagination.pageSize) || 10
      if (!pagination.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pagination.total / size))
    })

    const handleSizeChange = val => {
      pagination.pageSize = val
      const maxPage = Math.max(1, Math.ceil(pagination.total / pagination.pageSize) || 1)
      if (pagination.page > maxPage) {
        pagination.page = maxPage
      }
    }

    const handleCurrentChange = val => {
      pagination.page = val
    }

    // 跳转到称号详情页
    const goDetail = row => {
      router.push(`/titles/${row.id}`)
    }

    // 新建称号
    const openCreate = () => {
      editing.visible = true
      editing.id = null
      editing.form = {
        name: '',
        description: '',
        appearance: '{\n  "bg_color": "#5B8DEF",\n  "text_color": "#FFFFFF"\n}',
        created_date: ''
      }
    }

    // 保存称号（仅用于新建）
    const saveTitle = async () => {
      if (!editing.form.name?.trim()) {
        notify.error('请输入称号名称')
        return
      }
      try {
        savingTitle.value = true
        let appearance
        try {
          appearance = editing.form.appearance ? JSON.parse(editing.form.appearance) : {}
        } catch (e) {
          notify.error('外观JSON不合法')
          return
        }
        const payload = {
          name: editing.form.name,
          description: editing.form.description,
          appearance,
          created_date: editing.form.created_date || undefined
        }
        await createTitle(payload)
        notify.success('创建成功')
        editing.visible = false
        await loadTitles()
      } finally {
        savingTitle.value = false
      }
    }

    // 更新本月寿星 - 打开确认对话框
    const handleUpdateBirthdayTitles = () => {
      const birthdayTitle = allTitles.value.find(t => t.name.includes('本月寿星'))
      if (!birthdayTitle) {
        notify.warning('请先创建"本月寿星"称号')
        return
      }
      birthdayConfirmDialog.visible = true
    }

    // 确认更新本月寿星
    const handleConfirmBirthdayUpdate = async () => {
      try {
        const result = await updateBirthdayTitles({})
        notify.success(
          `更新成功！为 ${result.data.updated_count} 名队员授予了"${result.data.title_name}"称号`
        )
        birthdayConfirmDialog.visible = false
        await loadTitles()
      } catch (error) {
        console.error('更新生日称号失败：', error)
        notify.error(`更新失败：${error.response?.data?.message || error.message}`)
      }
    }

    // 响应式对话框宽度
    const dialogWidth = ref('560px')
    const computeDialogWidth = () => {
      const vw = window.innerWidth || 1024
      if (vw <= 360) {
        dialogWidth.value = '96vw'
      } else if (vw <= 768) {
        dialogWidth.value = '94vw'
      } else if (vw <= 1024) {
        dialogWidth.value = '700px'
      } else {
        dialogWidth.value = '780px'
      }
    }

    onMounted(() => {
      computeDialogWidth()
      window.addEventListener('resize', computeDialogWidth, { passive: true })
      loadTitles()
    })

    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidth)
    })

    return {
      loading,
      savingTitle,
      tableData,
      pagination,
      totalPages,
      editing,
      dialogWidth,
      handleSizeChange,
      handleCurrentChange,
      goDetail,
      openCreate,
      saveTitle,
      handleUpdateBirthdayTitles,
      birthdayConfirmDialog,
      handleConfirmBirthdayUpdate
    }
  }
}
</script>

<style lang="scss" scoped>
:deep(.el-dialog) {
  border-radius: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

:deep(.el-dialog__header) {
  padding: 10px 12px;
  margin-right: 0;
  margin-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

:deep(.el-dialog__title) {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

:deep(.el-dialog__body) {
  padding: 4px 12px;
}

:deep(.el-dialog__footer) {
  padding: 10px 12px 0px 12px;
  border-top: 1px solid var(--border);
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

.row-actions {
  display: inline-flex;
  gap: 8px;
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

.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
}

.table-wrapper {
  width: 100%;
  overflow: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead th {
  text-align: left;
  font-weight: 600;
  color: #374151;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  background: var(--background);
}

.data-table tbody td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.data-table tbody tr:hover {
  background: var(--muted);
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
</style>
