<template>
  <div class="page-container">
    <div class="board-card">
      <div class="board-card-content">
        <div class="header">
          <div class="header-text">
            <h3>队员列表</h3>
            <p class="description">查看和管理合唱队员信息</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="margin-bottom: -10px">
        <el-form :model="urlState" inline @keyup.enter="handleSearch">
          <el-form-item label="姓名">
            <el-input
              v-model="urlState.name"
              placeholder="请输入队员姓名"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item v-if="isAdmin" label="学号">
            <el-input
              v-model="urlState.userId"
              placeholder="请输入学号"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item label="声部">
            <el-select
              v-model="urlState.voicePart"
              placeholder="请选择声部"
              clearable
              style="width: 150px"
            >
              <el-option label="S1" value="S1" />
              <el-option label="S2" value="S2" />
              <el-option label="A1" value="A1" />
              <el-option label="A2" value="A2" />
              <el-option label="T1" value="T1" />
              <el-option label="T2" value="T2" />
              <el-option label="B1" value="B1" />
              <el-option label="B2" value="B2" />
              <el-option label="Other" value="Other" />
            </el-select>
          </el-form-item>
          <el-form-item label="梯队">
            <el-select
              v-model="urlState.tier"
              placeholder="请选择梯队"
              clearable
              style="width: 120px"
            >
              <el-option label="一队" value="一队" />
              <el-option label="二队" value="二队" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="isAdmin" label="状态">
            <el-select
              v-model="urlState.status"
              placeholder="请选择状态"
              clearable
              style="width: 120px"
            >
              <el-option
                v-for="s in MEMBER_STATUSES"
                :key="s.value"
                :label="s.label"
                :value="s.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="院系">
            <el-select
              v-model="urlState.department"
              placeholder="请选择院系"
              clearable
              filterable
              :reserve-keyword="false"
              style="width: 200px"
            >
              <el-option v-for="d in DEPARTMENTS" :key="d" :label="d" :value="d" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="isAdmin" label="生日月份">
            <el-select
              v-model="urlState.birthdayMonth"
              placeholder="请选择月份"
              clearable
              style="width: 120px"
            >
              <el-option label="1月" value="1" />
              <el-option label="2月" value="2" />
              <el-option label="3月" value="3" />
              <el-option label="4月" value="4" />
              <el-option label="5月" value="5" />
              <el-option label="6月" value="6" />
              <el-option label="7月" value="7" />
              <el-option label="8月" value="8" />
              <el-option label="9月" value="9" />
              <el-option label="10月" value="10" />
              <el-option label="11月" value="11" />
              <el-option label="12月" value="12" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <button
              class="btn-modern primary sm-btn"
              style="margin-right: 10px"
              type="button"
              @click="handleSearch"
            >
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
          <h3>队员信息</h3>
          <div class="actions">
            <ViewToggle v-model="viewMode" />
            <button
              v-if="isAdmin"
              class="btn-modern ghost sm-btn"
              @click="handleExport"
              :disabled="exporting"
            >
              <i-lucide-download class="btn-icon" />
              <span>导出</span>
            </button>
            <button v-if="isAdmin" class="btn-modern primary sm-btn" @click="handleAdd">
              <i-lucide-user-plus class="btn-icon" />
              <span>新增队员</span>
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
              <col class="table-col-member" />
              <col v-if="isAdmin" class="table-col-user-id" />
              <col class="table-col-voice" />
              <col class="table-col-tier" />
              <col class="table-col-status" />
              <col class="table-col-department" />
              <col class="table-col-action" />
            </colgroup>
            <thead>
              <tr>
                <th class="member-col">队员</th>
                <th v-if="isAdmin" class="user-id-col">学号</th>
                <th class="center-col">声部</th>
                <th class="center-col">梯队</th>
                <th class="center-col">状态</th>
                <th class="department-col">院系</th>
                <th class="sticky-right action-col">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="tableData.length === 0">
                <td :colspan="isAdmin ? 7 : 6" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in tableData" :key="row.id">
                <td class="member-col">
                  <div class="member-profile table-profile">
                    <router-link
                      class="member-avatar sm"
                      :to="`/personnel/members/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                    >
                      <img
                        v-if="row.avatar"
                        :src="row.avatar"
                        :alt="`${row.name || '队员'}头像`"
                        loading="lazy"
                        decoding="async"
                        @error="handleAvatarError(row)"
                      />
                      <span v-else>{{ getMemberInitial(row) }}</span>
                    </router-link>
                    <div class="member-profile-main">
                      <router-link
                        class="member-name-link"
                        :to="`/personnel/members/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                        >{{ row.name || '-' }}</router-link
                      >
                    </div>
                  </div>
                </td>
                <td v-if="isAdmin" class="user-id-col">{{ row.user_id || '-' }}</td>
                <td class="center-col">
                  <el-tag :type="getVoicePartType(row.voice_part)">
                    {{ row.voice_part || '-' }}
                  </el-tag>
                </td>
                <td class="center-col">
                  <el-tag :type="row.tier === '一队' ? 'danger' : 'primary'">
                    {{ row.tier || '-' }}
                  </el-tag>
                </td>
                <td class="center-col">
                  <el-tag :type="getMemberStatusType(row.status)">
                    {{ getMemberStatusLabel(row.status) }}
                  </el-tag>
                </td>
                <td class="department-col">
                  <span v-if="row.department === '其他'">{{ row.department_other || '其他' }}</span>
                  <span v-else>{{ row.department || '-' }}</span>
                </td>
                <td class="sticky-right action-col">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="handleView(row)">
                      <i-lucide-eye class="btn-icon" />
                      <span>查看</span>
                    </button>
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
              <div class="member-card" v-for="row in tableData" :key="row.id">
                <div class="member-card-row">
                  <router-link
                    class="member-avatar lg"
                    :to="`/personnel/members/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                  >
                    <img
                      v-if="row.avatar"
                      :src="row.avatar"
                      :alt="`${row.name || '队员'}头像`"
                      loading="lazy"
                      decoding="async"
                      @error="handleAvatarError(row)"
                    />
                    <span v-else>{{ getMemberInitial(row) }}</span>
                  </router-link>

                  <div class="member-card-body">
                    <router-link
                      class="member-card-name"
                      :to="`/personnel/members/${row.id}?ref=${encodeURIComponent($route.fullPath)}`"
                      >{{ row.name || '-' }}</router-link
                    >
                    <div class="member-card-fields">
                      <div v-if="isAdmin" class="member-card-field">
                        <span class="member-card-label">学号</span>
                        <span class="member-card-value">{{ row.user_id || '-' }}</span>
                      </div>
                      <div class="member-card-field">
                        <span class="member-card-label">声部</span>
                        <el-tag size="small" :type="getVoicePartType(row.voice_part)">
                          {{ row.voice_part || '-' }}
                        </el-tag>
                      </div>
                      <div class="member-card-field">
                        <span class="member-card-label">梯队</span>
                        <el-tag size="small" :type="row.tier === '一队' ? 'danger' : 'primary'">
                          {{ row.tier || '-' }}
                        </el-tag>
                      </div>
                      <div class="member-card-field">
                        <span class="member-card-label">状态</span>
                        <el-tag size="small" :type="getMemberStatusType(row.status)">
                          {{ getMemberStatusLabel(row.status) }}
                        </el-tag>
                      </div>
                      <div class="member-card-field department-field">
                        <span class="member-card-label">院系</span>
                        <span class="member-card-value">{{ getMemberDepartment(row) }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="row-actions member-card-actions">
                    <button class="btn-modern ghost xsm-btn" @click="handleView(row)">
                      <i-lucide-eye class="btn-icon" />
                      <span>查看</span>
                    </button>
                    <button
                      v-if="isAdmin"
                      class="btn-modern primary xsm-btn"
                      @click="handleEdit(row)"
                    >
                      <i-lucide-pencil class="btn-icon" />
                      <span>编辑</span>
                    </button>
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
import { getMemberList, exportMembers } from '@/api/personnel'
import { DEPARTMENTS, MEMBER_STATUSES } from '@/utils/constants'
import { downloadFile, getFilenameFromContentDisposition } from '@/utils/download'
import ViewToggle from '@/components/common/ViewToggle.vue'
import Pagination from '@/components/common/Pagination.vue'
import { useUrlState } from '@/utils/useUrlState'

export default {
  name: 'MemberList',
  components: {
    ViewToggle,
    Pagination
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()

    const loading = ref(true)
    const viewMode = ref('table') // 'table' | 'card'
    let listRequestSeq = 0

    // 使用 useUrlState 同步筛选和分页状态到 URL
    const { state: urlState, resetState: resetUrlState } = useUrlState({
      defaults: {
        name: '',
        userId: '',
        voicePart: '',
        tier: '',
        status: '',
        birthdayMonth: '',
        department: '',
        page: 1,
        pageSize: 20
      },
      types: {
        page: 'number',
        pageSize: 'number'
      }
    })

    const totalCount = ref(0)

    const members = ref([])
    const exporting = ref(false)

    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const getVoicePartType = voicePart => {
      const typeMap = {
        S1: 'danger',
        S2: 'danger',
        A1: 'warning',
        A2: 'warning',
        T1: 'success',
        T2: 'success',
        B1: 'primary',
        B2: 'primary',
        Other: 'info'
      }
      return typeMap[voicePart] || 'info'
    }

    const getMemberStatus = status => {
      return MEMBER_STATUSES.find(item => item.value === status) || MEMBER_STATUSES[0]
    }

    const getMemberStatusLabel = status => getMemberStatus(status).label
    const getMemberStatusType = status => getMemberStatus(status).type || 'info'
    const getMemberInitial = row => {
      const name = String(row?.name || row?.user_id || 'T').trim()
      return name ? name.substring(0, 1).toUpperCase() : 'T'
    }
    const getMemberDepartment = row => {
      if (row?.department === '其他') {
        return row.department_other || '其他'
      }
      return row?.department || '未填写院系'
    }
    const handleAvatarError = row => {
      if (row) {
        row.avatar = ''
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

    const handleAdd = () => {
      router.push(`/personnel/members/create?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const handleExport = async () => {
      exporting.value = true
      notify.info('正在导出队员信息，请稍候...')
      try {
        const resp = await exportMembers({
          name__icontains: urlState.value.name || undefined,
          user_id: urlState.value.userId || undefined,
          voice_part: urlState.value.voicePart || undefined,
          tier: urlState.value.tier || undefined,
          status: urlState.value.status || undefined,
          birthday_month: urlState.value.birthdayMonth || undefined,
          department: urlState.value.department || undefined
        })
        const filename =
          getFilenameFromContentDisposition(resp.headers?.['content-disposition']) ||
          'members_export.xlsx'
        downloadFile(resp.data, filename)
        notify.success('导出成功')
      } catch (e) {
        notify.error('导出失败')
        console.error('导出失败', e)
      } finally {
        exporting.value = false
      }
    }

    const handleView = row => {
      router.push(`/personnel/members/${row.id}?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const handleEdit = row => {
      router.push(`/personnel/members/${row.id}/edit?ref=${encodeURIComponent(route.fullPath)}`)
    }

    const handleSizeChange = val => {
      const newPageSize = val
      const maxPage = Math.max(1, Math.ceil(totalCount.value / newPageSize) || 1)
      const newPage = urlState.value.page > maxPage ? maxPage : urlState.value.page
      urlState.value = { ...urlState.value, pageSize: newPageSize, page: newPage }
      loadData()
    }

    const handleCurrentChange = val => {
      urlState.value = { ...urlState.value, page: val }
      loadData()
    }

    const loadData = async () => {
      const requestSeq = ++listRequestSeq
      loading.value = true
      try {
        const response = await getMemberList({
          name__icontains: urlState.value.name || undefined,
          user_id: urlState.value.userId || undefined,
          voice_part: urlState.value.voicePart || undefined,
          tier: urlState.value.tier || undefined,
          status: urlState.value.status || undefined,
          birthday_month: urlState.value.birthdayMonth || undefined,
          department: urlState.value.department || undefined,
          page: urlState.value.page,
          page_size: urlState.value.pageSize
        })
        if (requestSeq !== listRequestSeq) {
          return
        }
        const results = Array.isArray(response.data?.results) ? response.data.results : []
        members.value = results
        totalCount.value = Number(response.data?.count || results.length || 0)
        const maxPage = Math.max(1, Math.ceil(totalCount.value / urlState.value.pageSize) || 1)
        if (urlState.value.page > maxPage) {
          urlState.value = { ...urlState.value, page: maxPage }
          await loadData()
        }
      } catch (error) {
        if (requestSeq !== listRequestSeq) {
          return
        }
        if (error?.response?.status === 404 && urlState.value.page !== 1) {
          urlState.value = { ...urlState.value, page: 1 }
          await loadData()
          return
        }
        console.error('Failed to load member list:', error)
      } finally {
        if (requestSeq === listRequestSeq) {
          loading.value = false
        }
      }
    }

    // 监听 URL 状态变化重新加载数据（处理浏览器前进/后退）
    let isFirstLoad = true
    watch(
      () => [
        urlState.value.name,
        urlState.value.userId,
        urlState.value.voicePart,
        urlState.value.tier,
        urlState.value.status,
        urlState.value.birthdayMonth,
        urlState.value.department
      ],
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

    const tableData = computed(() => {
      return members.value || []
    })

    const totalPages = computed(() => {
      const size = Number(urlState.value.pageSize) || 10
      if (!totalCount.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(totalCount.value / size))
    })

    return {
      loading,
      viewMode,
      urlState,
      totalCount,
      tableData,
      isAdmin,
      DEPARTMENTS,
      totalPages,
      getVoicePartType,
      getMemberStatusLabel,
      getMemberStatusType,
      getMemberInitial,
      getMemberDepartment,
      handleAvatarError,
      MEMBER_STATUSES,
      handleSearch,
      handleReset,
      handleAdd,
      handleExport,
      handleView,
      handleEdit,
      handleSizeChange,
      handleCurrentChange,
      exporting
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

.member-profile {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 12px;
}

.table-profile {
  max-width: 190px;
}

.member-profile-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name-link {
  color: var(--el-color-primary);
}

.member-card-name {
  color: #111827;
}

.member-name-link,
.member-card-name {
  font-weight: 600;
  line-height: 1.35;
  text-decoration: none;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.member-name-link:hover,
.member-card-name:hover {
  color: var(--el-color-primary);
}

.member-card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-avatar {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  border-radius: 50%;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: var(--el-color-primary);
  border: 1px solid var(--border);
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.member-avatar:hover {
  border-color: rgba(59, 130, 246, 0.45);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.member-avatar.sm {
  width: 32px;
  height: 32px;
  flex-basis: 32px;
  font-size: 13px;
}

.member-avatar.lg {
  width: 52px;
  height: 52px;
  flex-basis: 52px;
  font-size: 19px;
}

.member-avatar img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  background: #fff;
}

.cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
.member-card {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 18px;
  background: #fff;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}

.member-card:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.member-card-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.member-card-name {
  max-width: 180px;
  font-size: 15px;
}

.member-card-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  align-items: center;
  column-gap: 18px;
  row-gap: 10px;
  width: 100%;
}

.member-card-field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
}

.member-card-label {
  color: #9ca3af;
  font-size: 12px;
  line-height: 1;
}

.member-card-value {
  max-width: 100%;
  color: #374151;
  font-size: 13px;
  line-height: 1.35;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.member-card-actions {
  margin-left: auto;
  padding-top: 4px;
  flex-shrink: 0;
}

@media (min-width: 900px) {
  .department-field {
    grid-column: span 2;
  }
}

@media (max-width: 640px) {
  .member-card-row {
    flex-wrap: wrap;
  }

  .member-card-body {
    flex-basis: calc(100% - 66px);
  }

  .member-card-actions {
    width: 100%;
    margin-left: 66px;
    justify-content: flex-start;
  }

  .member-card-fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-profile {
    max-width: 190px;
  }
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

.table-wrapper {
  width: 100%;
  overflow: auto;
}
.data-table {
  width: 100%;
  min-width: 1072px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
}
.data-table .table-col-member {
  width: 190px;
}
.data-table .table-col-user-id {
  width: 120px;
}
.data-table .table-col-voice,
.data-table .table-col-tier,
.data-table .table-col-status {
  width: 132px;
}
.data-table .table-col-department {
  width: 230px;
}
.data-table .table-col-action {
  width: 132px;
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
.data-table .member-col {
  padding-left: 16px;
}
.data-table .user-id-col,
.data-table .department-col {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.data-table .department-col {
  padding-left: 48px;
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
</style>
