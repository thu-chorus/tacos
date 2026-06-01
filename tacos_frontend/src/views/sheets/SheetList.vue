<template>
  <div class="page-container">
    <div class="board-card">
      <div class="board-card-content">
        <div class="header">
          <div class="header-text">
            <h3>我的乐谱库</h3>
            <p class="description">浏览和下载乐谱</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="margin-bottom: -10px">
        <el-form :model="urlState" inline @keyup.enter="handleSearch">
          <el-form-item label="曲名">
            <el-input
              v-model="urlState.title"
              placeholder="请输入曲名"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item label="作曲">
            <el-input
              v-model="urlState.composer"
              placeholder="请输入作曲"
              clearable
              style="max-width: 220px"
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
          <h3>乐谱列表</h3>
          <div class="actions">
            <ViewToggle v-model="viewMode" />
            <button v-if="isAdmin" class="btn-modern primary sm-btn" @click="goUpload">
              上传乐谱
            </button>
          </div>
        </div>

        <div
          v-if="viewMode === 'table'"
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
                <th style="min-width: 160px">曲名</th>
                <th style="min-width: 100px">作曲</th>
                <th style="min-width: 100px">作词</th>
                <th style="min-width: 100px">编曲</th>
                <th style="min-width: 90px">版权限制</th>
                <th class="sticky-right" style="min-width: 160px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="tableData.length === 0">
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in tableData" :key="row.id">
                <td>
                  <router-link
                    :to="`/sheets/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                    >{{ row.title }}</router-link
                  >
                  <el-tooltip
                    v-if="row.copyright_notice"
                    effect="dark"
                    :content="row.copyright_notice"
                    placement="top"
                  >
                    <i class="el-icon-info" style="margin-left: 6px; color: #909399" />
                  </el-tooltip>
                </td>
                <td>{{ row.composer }}</td>
                <td>{{ row.lyricist }}</td>
                <td>{{ row.arranger }}</td>
                <td>
                  <el-tag :type="row.is_restricted ? 'danger' : 'success'">
                    {{ row.is_restricted ? '受限' : '公开' }}
                  </el-tag>
                </td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="viewDetail(row)">详情</button>
                    <button class="btn-modern primary xsm-btn" @click="download(row)">下载</button>
                    <button
                      v-if="isAdmin"
                      class="btn-modern warning xsm-btn"
                      @click="editSheet(row)"
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
            <div v-if="tableData.length === 0" class="empty-cell">暂无数据</div>
            <div v-else class="cards-grid">
              <div class="sheet-card" v-for="row in tableData" :key="row.id">
                <div class="card-head">
                  <div class="left">
                    <div class="title">
                      <router-link
                        :to="`/sheets/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                        >{{ row.title }}</router-link
                      >
                      <el-tooltip
                        v-if="row.copyright_notice"
                        effect="dark"
                        :content="row.copyright_notice"
                        placement="top"
                      >
                        <i class="el-icon-info" style="margin-left: 6px; color: #909399" />
                      </el-tooltip>
                    </div>
                  </div>
                  <div class="row-actions">
                    <button
                      class="btn-modern ghost xsm-btn"
                      style="width: 38px"
                      @click="viewDetail(row)"
                    >
                      详情
                    </button>
                    <button
                      class="btn-modern primary xsm-btn"
                      style="width: 38px"
                      @click="download(row)"
                    >
                      下载
                    </button>
                    <button
                      v-if="isAdmin"
                      class="btn-modern warning xsm-btn"
                      style="width: 38px"
                      @click="editSheet(row)"
                    >
                      编辑
                    </button>
                  </div>
                </div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="label">作曲</div>
                    <div class="value">{{ row.composer || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">作词</div>
                    <div class="value">{{ row.lyricist || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">编曲</div>
                    <div class="value">{{ row.arranger || '-' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="label">版权限制</div>
                    <div class="value">
                      <el-tag :type="row.is_restricted ? 'danger' : 'success'">{{
                        row.is_restricted ? '受限' : '公开'
                      }}</el-tag>
                    </div>
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
import { notify } from '@/utils/notify'
import { getSheetList, initiateDownload, getDownloadTask } from '@/api/sheets'
import { formatDateTime } from '@/utils/format'
import Pagination from '@/components/common/Pagination.vue'
import ViewToggle from '@/components/common/ViewToggle.vue'
import { useUrlState } from '@/utils/useUrlState'

export default {
  name: 'SheetList',
  components: { Pagination, ViewToggle },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const viewMode = ref('table')

    const loading = ref(true)
    let listRequestSeq = 0

    // 使用 useUrlState 同步筛选和分页状态到 URL
    const { state: urlState, resetState: resetUrlState } = useUrlState({
      defaults: {
        title: '',
        composer: '',
        page: 1,
        pageSize: 20
      },
      types: {
        page: 'number',
        pageSize: 'number'
      }
    })

    const totalCount = ref(0)
    const sheets = ref([])

    const loadData = async () => {
      const requestSeq = ++listRequestSeq
      loading.value = true
      try {
        const res = await getSheetList({
          title__icontains: (urlState.value.title && urlState.value.title.trim()) || undefined,
          composer__icontains:
            (urlState.value.composer && urlState.value.composer.trim()) || undefined,
          page: urlState.value.page,
          page_size: urlState.value.pageSize
        })
        if (requestSeq !== listRequestSeq) {
          return
        }
        const results = Array.isArray(res.data?.results) ? res.data.results : []
        sheets.value = results
        totalCount.value = Number(res.data?.count || results.length || 0)
        const maxPage = Math.max(1, Math.ceil(totalCount.value / urlState.value.pageSize) || 1)
        if (urlState.value.page > maxPage) {
          urlState.value = { ...urlState.value, page: maxPage }
          await loadData()
        }
      } catch (e) {
        if (requestSeq !== listRequestSeq) {
          return
        }
        if (e?.response?.status === 404 && urlState.value.page !== 1) {
          urlState.value = { ...urlState.value, page: 1 }
          await loadData()
          return
        }
        console.error(e)
      } finally {
        if (requestSeq === listRequestSeq) {
          loading.value = false
        }
      }
    }

    const handleSearch = () => {
      urlState.value = { ...urlState.value, page: 1 }
      loadData()
    }
    const handleReset = () => {
      resetUrlState()
      loadData()
    }
    const handleSizeChange = val => {
      urlState.value = { ...urlState.value, pageSize: val }
      loadData()
    }
    const handleCurrentChange = val => {
      urlState.value = { ...urlState.value, page: val }
      loadData()
    }

    const goUpload = () => {
      router.push(`/sheets/upload?ref=${encodeURIComponent(route.fullPath)}`)
    }
    const viewDetail = row => {
      router.push(`/sheets/${row.id}?ref=${encodeURIComponent(route.fullPath)}`)
    }
    const editSheet = row => {
      router.push(`/sheets/${row.id}/edit?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const download = async row => {
      const loadingMsg = notify.loading('正在生成带水印的PDF，请稍候...')

      try {
        const initResp = await initiateDownload(row.id)
        const taskId = initResp.data?.task_id

        if (!taskId) {
          throw new Error('无法获取任务ID')
        }

        const pollTask = async () => {
          try {
            const resp = await getDownloadTask(taskId, false)

            const contentType = resp.headers['content-type'] || resp.headers['Content-Type']

            if (contentType && contentType.includes('application/json')) {
              const text = await resp.data.text()
              const jsonData = JSON.parse(text)

              if (jsonData.data?.status === 'PENDING' || jsonData.data?.status === 'PROCESSING') {
                setTimeout(pollTask, 1000)
              } else if (jsonData.data?.status === 'FAILED') {
                loadingMsg.close()
                notify.error(jsonData.message || '生成水印失败')
              } else {
                loadingMsg.close()
                notify.error('任务状态异常')
              }
            } else {
              loadingMsg.close()

              const blob = new Blob([resp.data], { type: 'application/pdf' })
              let filename = `${row.title}.pdf`

              const cd = resp.headers['content-disposition'] || resp.headers['Content-Disposition']
              if (cd && cd.includes('filename=')) {
                const match =
                  cd.match(/filename\*=UTF-8''([^;\n]+)/) || cd.match(/filename="?([^";\n]+)"?/)
                if (match && match[1]) {
                  filename = decodeURIComponent(match[1])
                }
              }

              const url = window.URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = filename
              document.body.appendChild(a)
              a.click()
              a.remove()
              window.URL.revokeObjectURL(url)

              notify.success('下载成功')
            }
          } catch (pollError) {
            loadingMsg.close()
            console.error('Polling error:', pollError)
            notify.error('下载失败，请重试')
          }
        }

        pollTask()
      } catch (e) {
        loadingMsg.close()
        console.error('Download error:', e)
        notify.error('下载失败')
      }
    }

    // 监听 URL 状态变化重新加载数据
    let isFirstLoad = true
    watch(
      () => [urlState.value.title, urlState.value.composer],
      () => {
        if (!isFirstLoad) {
          urlState.value = { ...urlState.value, page: 1 }
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

    const totalPages = computed(() => {
      const size = Number(urlState.value.pageSize) || 10
      if (!totalCount.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(totalCount.value / size))
    })

    const tableData = computed(() => {
      return sheets.value || []
    })

    return {
      loading,
      viewMode,
      urlState,
      totalCount,
      tableData,
      isAdmin,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      goUpload,
      viewDetail,
      editSheet,
      download,
      formatDateTime,
      totalPages
    }
  }
}
</script>

<style lang="scss" scoped>
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

@media (max-width: 768px) {
  .card-content :deep(.el-form) .el-form-item {
    width: 100%;
    margin-bottom: 10px;
  }
  .card-content :deep(.el-input) {
    width: 100% !important;
  }
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
.sheet-card {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  background: #fff;
}
.sheet-card .card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  margin-top: 6px;
}
.sheet-card .title {
  font-weight: 600;
  color: #111827;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.sheet-card .meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.sheet-card .info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 6px;
}
.sheet-card .info-item {
  display: flex;
  flex-direction: column;
}
.sheet-card .label {
  font-size: 12px;
  color: #6b7280;
}
.sheet-card .value {
  font-size: 14px;
  color: #374151;
}
</style>
