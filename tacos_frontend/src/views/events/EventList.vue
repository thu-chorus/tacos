<template>
  <div class="page-container">
    <div class="board-card">
      <div class="board-card-content">
        <div class="header">
          <div class="header-text">
            <h3>活动列表</h3>
            <p class="description">查看与管理活动信息</p>
          </div>
          <div class="actions">
            <button v-if="isAdmin" class="btn-modern primary sm-btn" @click="goCreate">
              创建活动
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="margin-bottom: -10px">
        <el-form :model="urlState" inline @keyup.enter="handleSearch">
          <el-form-item label="关键字">
            <el-input
              v-model="urlState.keyword"
              placeholder="活动名称"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item label="面向范围">
            <el-select v-model="urlState.scope" placeholder="全部" clearable style="width: 150px">
              <el-option label="面向全体" value="ALL" />
              <el-option label="面向一队" value="FIRST" />
              <el-option label="面向二队" value="SECOND" />
              <el-option label="面向部分" value="PARTIAL" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期范围">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <el-form-item>
            <button
              class="btn-modern primary sm-btn"
              style="margin-right: 10px"
              type="button"
              @click="handleSearch"
            >
              搜索
            </button>
            <button class="btn-modern ghost sm-btn" type="button" @click="handleReset">重置</button>
          </el-form-item>
        </el-form>
      </div>
    </div>

    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 10px">
          <h3>我参加的活动</h3>
          <div class="actions"><ViewToggle v-model="myViewMode" /></div>
        </div>
        <div
          v-if="myViewMode === 'table'"
          class="table-wrapper"
          :aria-busy="loading"
          style="margin-top: 10px"
        >
          <div v-if="loading" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <table class="data-table" v-else>
            <thead>
              <tr>
                <th style="min-width: 220px">名称</th>
                <th style="min-width: 120px">状态</th>
                <th style="min-width: 160px">面向</th>
                <th style="min-width: 80px">角色</th>
                <th style="min-width: 140px">开始日期</th>
                <th style="min-width: 140px">结束日期</th>
                <th class="sticky-right" style="min-width: 120px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="myTableData.length === 0">
                <td colspan="7" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in myTableData" :key="row.id">
                <td>
                  <router-link
                    :to="`/events/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                    >{{ row.name }}</router-link
                  >
                </td>
                <td>
                  <el-tag :type="getStatusType(getStatus(row))">{{ getStatus(row) }}</el-tag>
                </td>
                <td>
                  <el-tag :type="getVisibilityType(row.visibility)">{{
                    getVisibilityLabel(row.visibility)
                  }}</el-tag>
                </td>
                <td>
                  <el-tag
                    :type="
                      row.relation === 'event_admin'
                        ? 'warning'
                        : row.relation === 'member'
                          ? 'success'
                          : 'info'
                    "
                  >
                    {{
                      row.relation === 'event_admin'
                        ? '管理员'
                        : row.relation === 'member'
                          ? '成员'
                          : '未参加'
                    }}
                  </el-tag>
                </td>
                <td>{{ formatDate(row.start_date) }}</td>
                <td>{{ formatDate(row.end_date) }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="handleView(row)">查看</button>
                    <button
                      v-if="isAdmin || row.relation === 'event_admin'"
                      class="btn-modern warning xsm-btn"
                      @click="handleEdit(row)"
                    >
                      编辑
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
            <div v-if="myTableData.length === 0" class="empty-cell">暂无数据</div>
            <div v-else class="cards-grid">
              <div class="event-card" v-for="row in myTableData" :key="row.id">
                <div class="card-head">
                  <div class="left">
                    <div class="title">
                      <router-link
                        :to="`/events/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                        >{{ row.name }}</router-link
                      >
                    </div>
                    <div class="meta">
                      {{ formatDate(row.start_date) }} · {{ formatDate(row.end_date) }}
                    </div>
                  </div>
                  <div class="row-actions">
                    <button
                      class="btn-modern ghost xsm-btn"
                      style="width: 38px"
                      @click="handleView(row)"
                    >
                      查看
                    </button>
                    <button
                      v-if="isAdmin || row.relation === 'event_admin'"
                      class="btn-modern primary xsm-btn"
                      style="width: 38px"
                      @click="handleEdit(row)"
                    >
                      编辑
                    </button>
                  </div>
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="label">状态</div>
                    <div class="value">
                      <el-tag :type="getStatusType(getStatus(row))">{{ getStatus(row) }}</el-tag>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="label">面向</div>
                    <div class="value">
                      <el-tag :type="getVisibilityType(row.visibility)">{{
                        getVisibilityLabel(row.visibility)
                      }}</el-tag>
                    </div>
                  </div>
                  <div class="info-item" style="grid-column: span 2">
                    <div class="label">角色</div>
                    <div class="value">
                      <el-tag
                        :type="
                          row.relation === 'event_admin'
                            ? 'warning'
                            : row.relation === 'member'
                              ? 'success'
                              : 'info'
                        "
                      >
                        {{
                          row.relation === 'event_admin'
                            ? '管理员'
                            : row.relation === 'member'
                              ? '成员'
                              : '未参加'
                        }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <Pagination
          :current-page="urlState.myPage"
          :total-pages="myTotalPages"
          :page-size="urlState.myPageSize"
          :total="myTotal"
          @update:current-page="handleMyCurrentChange"
          @update:page-size="handleMySizeChange"
        />
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
      <div class="card-content">
        <div class="header" style="margin-bottom: 10px">
          <h3>未参加的活动</h3>
          <div class="actions"><ViewToggle v-model="otherViewMode" /></div>
        </div>
        <div
          v-if="otherViewMode === 'table'"
          class="table-wrapper"
          :aria-busy="loading"
          style="margin-top: 10px"
        >
          <div v-if="loading" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <table class="data-table" v-else>
            <thead>
              <tr>
                <th style="min-width: 220px">名称</th>
                <th style="min-width: 120px">状态</th>
                <th style="min-width: 160px">面向</th>
                <th style="min-width: 140px">开始日期</th>
                <th style="min-width: 140px">结束日期</th>
                <th class="sticky-right" style="min-width: 120px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="otherTableData.length === 0">
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in otherTableData" :key="row.id">
                <td>
                  <router-link
                    :to="`/events/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                    >{{ row.name }}</router-link
                  >
                </td>
                <td>
                  <el-tag :type="getStatusType(getStatus(row))">{{ getStatus(row) }}</el-tag>
                </td>
                <td>
                  <el-tag :type="getVisibilityType(row.visibility)">{{
                    getVisibilityLabel(row.visibility)
                  }}</el-tag>
                </td>
                <td>{{ formatDate(row.start_date) }}</td>
                <td>{{ formatDate(row.end_date) }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="handleView(row)">查看</button>
                    <button
                      v-if="isAdmin || row.relation === 'event_admin'"
                      class="btn-modern warning xsm-btn"
                      @click="handleEdit(row)"
                    >
                      编辑
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
            <div v-if="otherTableData.length === 0" class="empty-cell">暂无数据</div>
            <div v-else class="cards-grid">
              <div class="event-card" v-for="row in otherTableData" :key="row.id">
                <div class="card-head">
                  <div class="left">
                    <div class="title">
                      <router-link
                        :to="`/events/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                        >{{ row.name }}</router-link
                      >
                    </div>
                    <div class="meta">
                      {{ formatDate(row.start_date) }} · {{ formatDate(row.end_date) }}
                    </div>
                  </div>
                  <div class="row-actions">
                    <button
                      class="btn-modern ghost xsm-btn"
                      style="width: 38px"
                      @click="handleView(row)"
                    >
                      查看
                    </button>
                    <button
                      v-if="isAdmin || row.relation === 'event_admin'"
                      class="btn-modern primary xsm-btn"
                      style="width: 38px"
                      @click="handleEdit(row)"
                    >
                      编辑
                    </button>
                  </div>
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="label">状态</div>
                    <div class="value">
                      <el-tag :type="getStatusType(getStatus(row))">{{ getStatus(row) }}</el-tag>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="label">面向</div>
                    <div class="value">
                      <el-tag :type="getVisibilityType(row.visibility)">{{
                        getVisibilityLabel(row.visibility)
                      }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <Pagination
          :current-page="urlState.otherPage"
          :total-pages="otherTotalPages"
          :page-size="urlState.otherPageSize"
          :total="otherTotal"
          @update:current-page="handleOtherCurrentChange"
          @update:page-size="handleOtherSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { getEventList } from '@/api/events'
import { formatDate } from '@/utils/format'
import Pagination from '@/components/common/Pagination.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import { useUrlState } from '@/utils/useUrlState'

export default {
  name: 'EventList',
  components: { Pagination, ViewToggle },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const loading = ref(false)
    const myViewMode = ref('table')
    const otherViewMode = ref('table')
    const allEvents = ref([])

    // 使用 useUrlState 同步筛选和分页状态到 URL
    const { state: urlState, resetState: resetUrlState } = useUrlState({
      defaults: {
        keyword: '',
        scope: '',
        dateStart: '',
        dateEnd: '',
        myPage: 1,
        myPageSize: 20,
        otherPage: 1,
        otherPageSize: 20
      },
      types: {
        myPage: 'number',
        myPageSize: 'number',
        otherPage: 'number',
        otherPageSize: 'number'
      }
    })

    // 计算日期范围用于 el-date-picker
    const dateRange = computed({
      get: () => {
        if (urlState.value.dateStart && urlState.value.dateEnd) {
          return [urlState.value.dateStart, urlState.value.dateEnd]
        }
        return []
      },
      set: val => {
        if (Array.isArray(val) && val.length === 2) {
          urlState.value = { ...urlState.value, dateStart: val[0], dateEnd: val[1] }
        } else {
          urlState.value = { ...urlState.value, dateStart: '', dateEnd: '' }
        }
      }
    })

    const myTotal = ref(0)
    const otherTotal = ref(0)

    const buildParams = (page = 1, pageSize = 200) => {
      const params = {
        page,
        page_size: pageSize
      }
      if (urlState.value.keyword && urlState.value.keyword.trim()) {
        params.search = urlState.value.keyword.trim()
      }
      if (typeof urlState.value.scope === 'string' && urlState.value.scope) {
        params.visibility = urlState.value.scope
      }
      if (urlState.value.dateStart && urlState.value.dateEnd) {
        // 区间重叠：活动开始 <= 查询结束 且 活动结束 >= 查询开始
        params.start_date__lte = urlState.value.dateEnd
        params.end_date__gte = urlState.value.dateStart
      }
      return params
    }

    const loadData = async () => {
      loading.value = true
      try {
        // 全量拉取（按页累计），以便前端拆分为两个列表并各自分页
        const aggregated = []
        let page = 1
        const pageSize = 200
        let total = Infinity
        while ((page - 1) * pageSize < total) {
          const res = await getEventList(buildParams(page, pageSize))
          const results = Array.isArray(res.data?.results) ? res.data.results : []
          total = Number(res.data?.count || 0)
          aggregated.push(...results)
          if (results.length < pageSize) {
            break
          }
          page += 1
          // 安全阈值，避免过大数据导致长时间阻塞
          if (page > 50) {
            break
          }
        }
        allEvents.value = aggregated
      } finally {
        loading.value = false
      }
    }

    const handleSearch = () => {
      urlState.value = { ...urlState.value, myPage: 1, otherPage: 1 }
      loadData()
    }
    const handleReset = () => {
      resetUrlState()
      loadData()
    }

    const handleMySizeChange = val => {
      urlState.value = { ...urlState.value, myPageSize: val }
    }
    const handleMyCurrentChange = val => {
      urlState.value = { ...urlState.value, myPage: val }
    }
    const handleOtherSizeChange = val => {
      urlState.value = { ...urlState.value, otherPageSize: val }
    }
    const handleOtherCurrentChange = val => {
      urlState.value = { ...urlState.value, otherPage: val }
    }

    const handleView = row => {
      router.push(`/events/${row.id}?ref=${encodeURIComponent(route.fullPath)}`)
    }
    const handleEdit = row => {
      router.push(`/events/${row.id}/edit?ref=${encodeURIComponent(route.fullPath)}`)
    }
    const goCreate = () => {
      router.push(`/events/create?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const getVisibilityLabel = v =>
      ({ ALL: '面向全体', FIRST: '面向一队', SECOND: '面向二队', PARTIAL: '面向部分' })[v] ||
      '面向部分'
    const getVisibilityType = v =>
      ({ ALL: 'success', FIRST: 'danger', SECOND: 'primary', PARTIAL: 'info' })[v] || 'info'

    const getTodayDateString = () => {
      try {
        const { default: dayjs } = require('dayjs')
        return dayjs.tz().format('YYYY-MM-DD')
      } catch {
        const d = new Date()
        const yyyy = String(d.getFullYear())
        const mm = String(d.getMonth() + 1).padStart(2, '0')
        const dd = String(d.getDate()).padStart(2, '0')
        return `${yyyy}-${mm}-${dd}`
      }
    }

    const getStatus = row => {
      const today = getTodayDateString()
      const start = (row?.start_date || '').slice(0, 10)
      const end = (row?.end_date || '').slice(0, 10)
      if (!start || !end) {
        return '进行中'
      }
      if (start > today) {
        return '未开始'
      }
      if (end < today) {
        return '已结束'
      }
      return '进行中'
    }

    const getStatusType = status =>
      ({ 进行中: 'success', 未开始: 'warning', 已结束: 'info' })[status] || 'info'

    const myAll = computed(() =>
      (allEvents.value || []).filter(
        ev => ev?.relation === 'member' || ev?.relation === 'event_admin'
      )
    )
    const otherAll = computed(() =>
      (allEvents.value || []).filter(ev => !ev?.relation || ev?.relation === 'not_member')
    )

    const myTableData = computed(() => {
      const start = (urlState.value.myPage - 1) * urlState.value.myPageSize
      return myAll.value.slice(start, start + urlState.value.myPageSize)
    })
    const otherTableData = computed(() => {
      const start = (urlState.value.otherPage - 1) * urlState.value.otherPageSize
      return otherAll.value.slice(start, start + urlState.value.otherPageSize)
    })

    watch(
      [myAll, otherAll],
      ([ma, oa]) => {
        myTotal.value = (ma && ma.length) || 0
        otherTotal.value = (oa && oa.length) || 0
        // 越界修正
        const myMaxPage = Math.max(1, Math.ceil(myTotal.value / urlState.value.myPageSize) || 1)
        const otherMaxPage = Math.max(
          1,
          Math.ceil(otherTotal.value / urlState.value.otherPageSize) || 1
        )
        if (urlState.value.myPage > myMaxPage) {
          urlState.value = { ...urlState.value, myPage: myMaxPage }
        }
        if (urlState.value.otherPage > otherMaxPage) {
          urlState.value = { ...urlState.value, otherPage: otherMaxPage }
        }
      },
      { immediate: true }
    )

    // 监听 URL 状态变化重新加载数据
    let isFirstLoad = true
    watch(
      () => [
        urlState.value.keyword,
        urlState.value.scope,
        urlState.value.dateStart,
        urlState.value.dateEnd
      ],
      () => {
        if (!isFirstLoad) {
          loadData()
        }
      },
      { deep: true }
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

    const myTotalPages = computed(() => {
      const size = Number(urlState.value.myPageSize) || 10
      if (!myTotal.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(myTotal.value / size))
    })
    const otherTotalPages = computed(() => {
      const size = Number(urlState.value.otherPageSize) || 10
      if (!otherTotal.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(otherTotal.value / size))
    })

    return {
      loading,
      myViewMode,
      otherViewMode,
      myTableData,
      otherTableData,
      urlState,
      dateRange,
      myTotal,
      otherTotal,
      isAdmin,
      handleSearch,
      handleReset,
      handleMySizeChange,
      handleMyCurrentChange,
      handleOtherSizeChange,
      handleOtherCurrentChange,
      handleView,
      handleEdit,
      goCreate,
      getVisibilityLabel,
      getVisibilityType,
      getStatus,
      getStatusType,
      formatDate,
      myTotalPages,
      otherTotalPages
    }
  }
}
</script>

<style scoped>
.row-actions {
  display: inline-flex;
  gap: 8px;
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
.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
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

.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
.event-card {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  background: #fff;
}
.event-card .card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  margin-top: 6px;
}
.event-card .title {
  font-weight: 600;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.event-card .meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.event-card .info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 6px;
}
.event-card .info-item {
  display: flex;
  flex-direction: column;
}
.event-card .label {
  font-size: 12px;
  color: #6b7280;
}
.event-card .value {
  font-size: 14px;
  color: #374151;
}

@media (max-width: 768px) {
  .card-content :deep(.el-form) .el-form-item {
    width: 100%;
    margin-bottom: 10px;
  }
  .card-content :deep(.el-input),
  .card-content :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
