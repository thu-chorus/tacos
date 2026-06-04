<template>
  <div class="page-container">
    <div class="board-card">
      <div class="board-card-content">
        <div class="header">
          <div class="header-text">
            <h3>外请教师</h3>
            <p class="description">管理外请教师信息</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="margin-bottom: -10px">
        <el-form :model="urlState" inline @submit.prevent="handleSearch">
          <el-form-item label="姓名">
            <el-input
              v-model="urlState.name"
              placeholder="请输入教师姓名"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item>
            <button class="btn-modern primary sm-btn" style="margin-right: 10px" type="submit">
              <i-lucide-search class="btn-icon" />
              <span>搜索</span>
            </button>
            <button class="btn-modern ghost sm-btn" type="button" @click="handleReset">
              <i-lucide-rotate-ccw class="btn-icon" />
              <span>重置</span>
            </button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div class="card">
      <div class="card-content">
        <div class="header">
          <h3>教师列表</h3>
          <div class="actions">
            <ViewToggle v-model="viewMode" />
            <button v-if="isAdmin" class="btn-modern primary sm-btn" @click="handleAdd">
              <i-lucide-user-plus class="btn-icon" />
              <span>新增教师</span>
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
              <col class="table-col-name" />
              <col class="table-col-id" />
              <col class="table-col-phone" />
              <col class="table-col-vehicle" />
              <col class="table-col-title" />
              <col class="table-col-affiliation" />
              <col class="table-col-address" />
              <col class="table-col-fee" />
              <col class="table-col-external" />
              <col class="table-col-action" />
            </colgroup>
            <thead>
              <tr>
                <th class="name-col">姓名</th>
                <th class="id-col">身份证号</th>
                <th class="phone-col">手机号</th>
                <th class="vehicle-col">车牌号</th>
                <th class="title-col">职称</th>
                <th class="affiliation-col">单位</th>
                <th class="address-col">地址</th>
                <th class="center-col">课时费</th>
                <th class="center-col">是否外请</th>
                <th class="sticky-right action-col">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="tableData.length === 0">
                <td colspan="10" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in tableData" :key="row.id">
                <td class="name-col">{{ row.name }}</td>
                <td class="id-col">{{ row.instructor_id }}</td>
                <td class="phone-col">{{ row.phone_number || '-' }}</td>
                <td class="vehicle-col">{{ row.vehicle_number || '-' }}</td>
                <td class="title-col">{{ row.title || '-' }}</td>
                <td class="affiliation-col">{{ row.affiliation || '-' }}</td>
                <td class="address-col">{{ row.address || '-' }}</td>
                <td class="center-col">{{ row.fee || '-' }}</td>
                <td class="center-col">{{ row.is_external ? '是' : '否' }}</td>
                <td class="sticky-right action-col">
                  <div class="row-actions">
                    <button
                      v-if="isAdmin"
                      class="btn-modern warning xsm-btn"
                      @click="handleEdit(row)"
                    >
                      <i-lucide-pencil class="btn-icon" />
                      <span>编辑</span>
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
            <div v-if="tableData.length === 0" class="empty-cell">暂无数据</div>
            <div v-else class="cards-grid">
              <div class="instructor-card" v-for="row in tableData" :key="row.id">
                <div class="card-head">
                  <div class="left">
                    <div class="name">{{ row.name }}</div>
                    <div class="meta">
                      身份证号：{{ row.instructor_id }} · {{ row.title || '无职称' }}
                    </div>
                  </div>
                  <div class="row-actions">
                    <button class="btn-modern warning xsm-btn edit-btn" @click="handleEdit(row)">
                      <i-lucide-pencil class="btn-icon" />
                      <span>编辑</span>
                    </button>
                  </div>
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="label">手机号</div>
                    <div class="value">{{ row.phone_number || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">车牌号</div>
                    <div class="value">{{ row.vehicle_number || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">单位</div>
                    <div class="value">{{ row.affiliation || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">地址</div>
                    <div class="value">{{ row.address || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">课时费</div>
                    <div class="value">{{ row.fee || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">是否外请</div>
                    <div class="value">{{ row.is_external ? '是' : '否' }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <Pagination
          :current-page="urlState.page"
          :total-pages="totalPages"
          :page-size="urlState.pageSize"
          :total="totalCount"
          @update:current-page="handleCurrentChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { getInstructorList } from '@/api/personnel'
import Pagination from '@/components/common/Pagination.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import { useUrlState } from '@/utils/useUrlState'

export default {
  name: 'InstructorList',
  components: { Pagination, ViewToggle },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const loading = ref(true)
    const viewMode = ref('table') // 'table' | 'card'
    const tableData = ref([])
    let listRequestSeq = 0

    // 使用 useUrlState 同步筛选和分页状态到 URL
    const { state: urlState, resetState: resetUrlState } = useUrlState({
      defaults: {
        name: '',
        page: 1,
        pageSize: 20
      },
      types: {
        page: 'number',
        pageSize: 'number'
      }
    })

    const totalCount = ref(0)

    const totalPages = computed(() => {
      const size = Number(urlState.value.pageSize) || 10
      if (!totalCount.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(totalCount.value / size))
    })

    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const handleSearch = () => {
      urlState.value = { ...urlState.value, page: 1 }
      loadData()
    }
    const handleReset = () => {
      resetUrlState()
      loadData()
    }
    const handleSizeChange = val => {
      urlState.value = { ...urlState.value, pageSize: val, page: 1 }
      loadData()
    }
    const handleCurrentChange = val => {
      urlState.value = { ...urlState.value, page: val }
      loadData()
    }

    const handleAdd = () => {
      router.push(`/personnel/instructors/create?ref=${encodeURIComponent(route.fullPath)}`)
    }
    const handleEdit = row => {
      router.push(`/personnel/instructors/${row.id}/edit?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const loadData = async () => {
      const requestSeq = ++listRequestSeq
      loading.value = true
      try {
        const res = await getInstructorList({
          name__icontains: urlState.value.name || undefined,
          page: urlState.value.page,
          page_size: urlState.value.pageSize
        })
        if (requestSeq !== listRequestSeq) {
          return
        }
        totalCount.value = res.data?.count || 0
        tableData.value = Array.isArray(res.data?.results) ? res.data.results : []
      } catch (e) {
        if (requestSeq !== listRequestSeq) {
          return
        }
        console.error('Failed to load instructor list:', e)
      } finally {
        if (requestSeq === listRequestSeq) {
          loading.value = false
        }
      }
    }

    // 监听 URL 状态变化重新加载数据
    let isFirstLoad = true
    watch(
      () => urlState.value.name,
      () => {
        if (!isFirstLoad) {
          loadData()
        }
      }
    )

    // 初始加载
    watch(
      () => urlState.value,
      () => {
        if (isFirstLoad) {
          isFirstLoad = false
          loadData()
        }
      },
      { immediate: true }
    )

    return {
      loading,
      viewMode,
      urlState,
      totalCount,
      tableData,
      isAdmin,
      totalPages,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleAdd,
      handleEdit
    }
  }
}
</script>

<style lang="scss" scoped>
.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.instructor-card {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 18px;
  background: #fff;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}
.instructor-card:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}
.instructor-card .card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  margin-top: 6px;
}
.instructor-card .name {
  font-weight: 600;
  color: #111827;
}
.instructor-card .meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.instructor-card .info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.instructor-card .info-item {
  display: flex;
  flex-direction: column;
}
.instructor-card .label {
  font-size: 12px;
  color: #6b7280;
}
.instructor-card .value {
  font-size: 14px;
  color: #374151;
}

.instructor-card .edit-btn {
  position: absolute;
  top: 10px;
  right: 10px;
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
  min-width: 1388px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}
.data-table .table-col-name {
  width: 112px;
}
.data-table .table-col-id {
  width: 190px;
}
.data-table .table-col-phone {
  width: 128px;
}
.data-table .table-col-vehicle {
  width: 120px;
}
.data-table .table-col-title {
  width: 112px;
}
.data-table .table-col-affiliation {
  width: 170px;
}
.data-table .table-col-address {
  width: 220px;
}
.data-table .table-col-fee,
.data-table .table-col-external {
  width: 112px;
}
.data-table .table-col-action {
  width: 112px;
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
.data-table .center-col {
  text-align: center;
}
.data-table .name-col,
.data-table .id-col,
.data-table .phone-col,
.data-table .vehicle-col,
.data-table .title-col,
.data-table .affiliation-col,
.data-table .address-col {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.data-table .action-col {
  text-align: center;
}
.data-table .action-col .row-actions {
  justify-content: center;
}

/* 操作列固定在右侧 */
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

.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.card-content {
  padding: 10px 12px;
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
</style>
