<template>
  <div class="page-container">
    <!-- 基本信息卡片 -->
    <div class="card">
      <div class="card-content">
        <div class="profile-header">
          <div class="meta">
            <div class="name">
              <TitleBadge :title="titleInfo" style="font-size: 16px" />
              <span style="margin-left: 12px">{{ titleInfo.name || '称号详情' }}</span>
            </div>
            <div class="tags" style="margin-top: 8px">
              <el-tag type="info">拥有人数：{{ titleInfo.owners_count || 0 }}</el-tag>
              <el-tag v-if="titleInfo.created_date" type="success"
                >创建于 {{ titleInfo.created_date }}</el-tag
              >
            </div>
          </div>
          <div class="actions">
            <button class="btn-modern primary sm-btn" @click="openEditDialog">编辑</button>
            <button class="btn-modern danger sm-btn" @click="openDeleteDialog">删除</button>
          </div>
        </div>
      </div>
      <div class="info-row" style="padding: 10px 12px">
        <div class="info-item">
          <div class="label">称号描述</div>
          <div class="value">{{ titleInfo.description || '暂无描述' }}</div>
        </div>
        <div class="info-item">
          <div class="label">创建日期</div>
          <div class="value">{{ titleInfo.created_date || '-' }}</div>
        </div>
      </div>
    </div>

    <!-- 拥有该称号的队员列表卡片 -->
    <div class="card" style="margin-top: 16px">
      <div class="card-content">
        <div class="header" style="margin-bottom: 10px">
          <h3>拥有该称号的队员</h3>
          <div class="actions">
            <button class="btn-modern primary sm-btn" @click="openGrantDialog">授予称号</button>
          </div>
        </div>

        <div class="table-wrapper" :aria-busy="loadingMembers">
          <div v-if="loadingMembers" class="loading-area">
            <span class="loading-spinner" />
            <span class="loading-text">加载中...</span>
          </div>
          <table class="data-table" v-else>
            <thead>
              <tr>
                <th style="min-width: 100px">学号</th>
                <th style="min-width: 100px">姓名</th>
                <th style="min-width: 80px">声部</th>
                <th style="min-width: 80px">梯队</th>
                <th style="min-width: 120px">授予日期</th>
                <th class="sticky-right" style="min-width: 80px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="membersPage.length === 0">
                <td colspan="6" class="empty-cell">暂无队员拥有该称号</td>
              </tr>
              <tr v-for="row in membersPage" :key="row.id">
                <td>{{ row.member_user_id || '-' }}</td>
                <td>
                  <router-link
                    :to="{
                      name: 'MemberDetail',
                      params: { id: row.member_public_id },
                      query: { ref: $route.fullPath }
                    }"
                  >
                    {{ row.member_name || '-' }}
                  </router-link>
                </td>
                <td>
                  <el-tag v-if="row.voice_part" :type="getVoicePartType(row.voice_part)">
                    {{ row.voice_part }}
                  </el-tag>
                  <span v-else>-</span>
                </td>
                <td>
                  <el-tag v-if="row.tier" :type="row.tier === '一队' ? 'danger' : 'primary'">
                    {{ row.tier }}
                  </el-tag>
                  <span v-else>-</span>
                </td>
                <td>{{ row.awarded_at || '-' }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern danger xsm-btn" @click="handleRemove(row)">
                      移除
                    </button>
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

    <!-- 编辑称号对话框 -->
    <el-dialog v-model="editDialog.visible" title="编辑称号" :width="dialogWidth">
      <el-form :model="editDialog.form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="editDialog.form.name" placeholder="请输入称号名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            type="textarea"
            v-model="editDialog.form.description"
            placeholder="请输入称号描述"
          />
        </el-form-item>
        <el-form-item label="外观JSON">
          <el-input
            type="textarea"
            v-model="editDialog.form.appearance"
            :rows="8"
            placeholder="输入合法 JSON"
          />
        </el-form-item>
        <el-form-item label="创建日期">
          <el-date-picker
            v-model="editDialog.form.created_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="留空默认当天"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="editDialog.visible = false"
          style="margin-right: 8px"
        >
          取消
        </button>
        <button class="btn-modern primary sm-btn" :disabled="saving" @click="handleSaveEdit">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteDialog.visible"
      title="删除称号"
      :description="`确认删除称号「${titleInfo.name}」？此操作不可撤销，所有拥有该称号的队员都将失去该称号。`"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      @confirm="handleConfirmDelete"
    />

    <!-- 移除队员称号确认对话框 -->
    <ConfirmDialog
      v-model:visible="removeDialog.visible"
      title="移除称号"
      :description="`确认移除队员「${removeDialog.memberName}」的此称号？`"
      confirm-text="确认移除"
      cancel-text="取消"
      :danger="true"
      @confirm="handleConfirmRemove"
    />

    <!-- 授予称号对话框 -->
    <el-dialog v-model="grantDialog.visible" title="授予称号" :width="dialogWidth">
      <el-form :model="grantDialog.form" label-width="100px">
        <el-form-item label="选择队员">
          <el-select
            v-model="grantDialog.form.members"
            multiple
            filterable
            remote
            :remote-method="queryMembers"
            :loading="loadingMemberOptions"
            placeholder="搜索并选择队员"
            style="width: 100%"
            @visible-change="onMembersDropdownVisibleChange"
          >
            <el-option
              v-for="m in memberOptions"
              :key="m.id"
              :label="(m.name || '') + (m.user_id ? '（' + m.user_id + '）' : '')"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="授予日期">
          <el-date-picker
            v-model="grantDialog.form.awarded_at"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="留空默认当天"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="grantDialog.visible = false"
          style="margin-right: 8px"
        >
          取消
        </button>
        <button class="btn-modern primary sm-btn" :disabled="granting" @click="handleConfirmGrant">
          {{ granting ? '授予中...' : '确认授予' }}
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@/utils/notify'
import {
  getTitleDetail,
  updateTitle,
  deleteTitle,
  getMemberTitles,
  addMemberTitle,
  removeMemberTitle,
  getMemberList
} from '@/api/personnel'
import TitleBadge from '@/components/common/TitleBadge.vue'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'TitleDetail',
  components: { TitleBadge, Pagination, ConfirmDialog },
  setup() {
    const route = useRoute()
    const router = useRouter()

    const loading = ref(false)
    const loadingMembers = ref(false)
    const saving = ref(false)
    const granting = ref(false)
    const titleInfo = ref({})
    const allMemberTitles = ref([])

    const pagination = reactive({
      page: 1,
      pageSize: 10,
      total: 0
    })

    // 编辑对话框
    const editDialog = reactive({
      visible: false,
      form: {
        name: '',
        description: '',
        appearance: '',
        created_date: ''
      }
    })

    // 删除对话框
    const deleteDialog = reactive({
      visible: false
    })

    // 移除队员称号对话框
    const removeDialog = reactive({
      visible: false,
      memberName: '',
      rowId: null
    })

    // 授予称号对话框
    const grantDialog = reactive({
      visible: false,
      form: {
        members: [],
        awarded_at: ''
      }
    })

    // 队员选择器选项
    const memberOptions = ref([])
    const loadingMemberOptions = ref(false)

    // 排序规则
    const TIER_ORDER = { 一队: 0, 二队: 1 }
    const VOICE_PART_ORDER = { S1: 0, S2: 1, A1: 2, A2: 3, T1: 4, T2: 5, B1: 6, B2: 7, Other: 8 }
    const nameCollator = new Intl.Collator(['zh-Hans-u-co-pinyin', 'zh-Hans', 'zh-CN', 'en'], {
      sensitivity: 'base',
      numeric: true
    })

    const compareMemberTitles = (a, b) => {
      // 先按梯队排序
      const tierA = Object.prototype.hasOwnProperty.call(TIER_ORDER, a.tier)
        ? TIER_ORDER[a.tier]
        : 99
      const tierB = Object.prototype.hasOwnProperty.call(TIER_ORDER, b.tier)
        ? TIER_ORDER[b.tier]
        : 99
      if (tierA !== tierB) {
        return tierA - tierB
      }

      // 再按声部排序
      const vpA = Object.prototype.hasOwnProperty.call(VOICE_PART_ORDER, a.voice_part)
        ? VOICE_PART_ORDER[a.voice_part]
        : 99
      const vpB = Object.prototype.hasOwnProperty.call(VOICE_PART_ORDER, b.voice_part)
        ? VOICE_PART_ORDER[b.voice_part]
        : 99
      if (vpA !== vpB) {
        return vpA - vpB
      }

      // 再按姓名排序
      const nameA = (a.member_name || '').toString()
      const nameB = (b.member_name || '').toString()
      const nameCmp = nameCollator.compare(nameA, nameB)
      if (nameCmp !== 0) {
        return nameCmp
      }

      // 最后按学号排序
      const idA = (a.member_user_id || '').toString()
      const idB = (b.member_user_id || '').toString()
      return idA.localeCompare(idB)
    }

    // 加载称号详情
    const loadTitleDetail = async () => {
      loading.value = true
      try {
        const res = await getTitleDetail(route.params.id)
        titleInfo.value = res.data || {}
      } catch (error) {
        console.error('加载称号详情失败：', error)
        notify.error('加载称号详情失败')
      } finally {
        loading.value = false
      }
    }

    // 加载拥有该称号的队员列表
    const loadMemberTitles = async () => {
      loadingMembers.value = true
      try {
        const res = await getMemberTitles({ title_id: route.params.id, page_size: 1000 })
        const items = Array.isArray(res.data?.results) ? res.data.results : res.data || []

        // 为每个成员获取详细信息（声部、梯队）
        // 由于 member-titles 接口可能不返回声部梯队信息，我们需要额外处理
        // 先获取所有成员的完整信息
        const memberIds = [...new Set(items.map(item => item.member_public_id).filter(Boolean))]

        // 批量获取成员信息
        const memberInfoMap = {}
        if (memberIds.length > 0) {
          try {
            const memberRes = await getMemberList({ page_size: 1000 })
            const members = Array.isArray(memberRes.data?.results)
              ? memberRes.data.results
              : memberRes.data || []
            members.forEach(m => {
              if (m.id) {
                memberInfoMap[m.id] = m
              }
            })
          } catch (e) {
            // 忽略错误，使用空的成员信息
          }
        }

        // 合并成员信息
        allMemberTitles.value = items.map(item => {
          const memberInfo = memberInfoMap[item.member_public_id] || {}
          return {
            ...item,
            voice_part: memberInfo.voice_part || '',
            tier: memberInfo.tier || ''
          }
        })

        // 排序
        allMemberTitles.value.sort(compareMemberTitles)
        pagination.total = allMemberTitles.value.length

        // 确保当前页不超出范围
        const maxPage = Math.max(1, Math.ceil(pagination.total / pagination.pageSize) || 1)
        if (pagination.page > maxPage) {
          pagination.page = maxPage
        }
      } catch (error) {
        console.error('加载成员称号列表失败：', error)
      } finally {
        loadingMembers.value = false
      }
    }

    // 分页后的队员数据
    const membersPage = computed(() => {
      const start = (pagination.page - 1) * pagination.pageSize
      return allMemberTitles.value.slice(start, start + pagination.pageSize)
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

    // 声部标签类型
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

    // 打开编辑对话框
    const openEditDialog = () => {
      editDialog.form = {
        name: titleInfo.value.name || '',
        description: titleInfo.value.description || '',
        appearance: JSON.stringify(titleInfo.value.appearance || {}, null, 2),
        created_date: titleInfo.value.created_date || ''
      }
      editDialog.visible = true
    }

    // 保存编辑
    const handleSaveEdit = async () => {
      if (!editDialog.form.name?.trim()) {
        notify.error('请输入称号名称')
        return
      }
      try {
        saving.value = true
        let appearance
        try {
          appearance = editDialog.form.appearance ? JSON.parse(editDialog.form.appearance) : {}
        } catch (e) {
          notify.error('外观JSON不合法')
          return
        }
        const payload = {
          name: editDialog.form.name,
          description: editDialog.form.description,
          appearance,
          created_date: editDialog.form.created_date || undefined
        }
        await updateTitle(route.params.id, payload)
        notify.success('更新成功')
        editDialog.visible = false
        await loadTitleDetail()
      } catch (error) {
        console.error('更新称号失败：', error)
        notify.error('更新失败')
      } finally {
        saving.value = false
      }
    }

    // 打开删除对话框
    const openDeleteDialog = () => {
      deleteDialog.visible = true
    }

    // 确认删除
    const handleConfirmDelete = async () => {
      try {
        await deleteTitle(route.params.id)
        notify.success('删除成功')
        deleteDialog.visible = false
        router.push('/titles')
      } catch (error) {
        console.error('删除称号失败：', error)
        notify.error('删除失败')
      }
    }

    // 打开授予对话框
    const openGrantDialog = () => {
      grantDialog.form = {
        members: [],
        awarded_at: ''
      }
      grantDialog.visible = true
    }

    // 搜索队员
    const queryMembers = async query => {
      loadingMemberOptions.value = true
      try {
        const params = { page_size: 1000 }
        const q = query && String(query).trim()
        if (q) {
          if (/^\d+$/.test(q)) {
            params.user_id = q
          } else {
            params.name__icontains = q
          }
        }
        const res = await getMemberList(params)
        memberOptions.value = res.data?.results || res.data || []
      } finally {
        loadingMemberOptions.value = false
      }
    }

    const onMembersDropdownVisibleChange = async visible => {
      if (visible && (!memberOptions.value || memberOptions.value.length === 0)) {
        await queryMembers('')
      }
    }

    // 确认授予
    const handleConfirmGrant = async () => {
      if (!grantDialog.form.members || grantDialog.form.members.length === 0) {
        notify.error('请至少选择一位队员')
        return
      }

      granting.value = true
      try {
        const payloads = grantDialog.form.members.map(memberId => ({
          member_id: memberId,
          title_id: Number(route.params.id),
          awarded_at: grantDialog.form.awarded_at || undefined
        }))

        const results = await Promise.allSettled(
          payloads.map(p => addMemberTitle(p, { skipErrorMessage: true }))
        )

        const succeeded = results.filter(r => r.status === 'fulfilled').length
        const failed = results.filter(r => r.status === 'rejected')

        if (succeeded > 0) {
          notify.success(`成功为 ${succeeded} 名队员授予称号`)
        }

        if (failed.length > 0) {
          const errors = failed.map(r => {
            const error = r.reason
            const responseData = error?.response?.data
            if (responseData?.data?.member_id) {
              return Array.isArray(responseData.data.member_id)
                ? responseData.data.member_id[0]
                : responseData.data.member_id
            } else if (responseData?.message) {
              return responseData.message
            }
            return error?.message || '未知错误'
          })
          const uniqueErrors = [...new Set(errors)]
          if (uniqueErrors.length === 1) {
            notify.warning(`部分授予失败：${uniqueErrors[0]}`)
          } else {
            notify.warning(`部分授予失败：${failed.length} 人`)
            console.warn('授予称号失败详情：', errors)
          }
        }

        grantDialog.visible = false
        await loadMemberTitles()
        await loadTitleDetail()
      } finally {
        granting.value = false
      }
    }

    // 打开移除确认对话框
    const handleRemove = row => {
      removeDialog.memberName = row.member_name || '该队员'
      removeDialog.rowId = row.id
      removeDialog.visible = true
    }

    // 确认移除成员称号
    const handleConfirmRemove = async () => {
      try {
        await removeMemberTitle(removeDialog.rowId)
        notify.success('已移除')
        removeDialog.visible = false
        await loadMemberTitles()
        await loadTitleDetail()
      } catch (error) {
        console.error('移除称号失败：', error)
        notify.error('移除失败')
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
        dialogWidth.value = '600px'
      } else {
        dialogWidth.value = '680px'
      }
    }

    onMounted(() => {
      computeDialogWidth()
      window.addEventListener('resize', computeDialogWidth, { passive: true })
      loadTitleDetail()
      loadMemberTitles()
    })

    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidth)
    })

    return {
      loading,
      loadingMembers,
      saving,
      granting,
      titleInfo,
      membersPage,
      pagination,
      totalPages,
      editDialog,
      deleteDialog,
      removeDialog,
      grantDialog,
      memberOptions,
      loadingMemberOptions,
      dialogWidth,
      handleSizeChange,
      handleCurrentChange,
      getVoicePartType,
      openEditDialog,
      handleSaveEdit,
      openDeleteDialog,
      handleConfirmDelete,
      openGrantDialog,
      queryMembers,
      onMembersDropdownVisibleChange,
      handleConfirmGrant,
      handleRemove,
      handleConfirmRemove
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

.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.card-content {
  padding: 10px 12px;
}

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.meta {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  line-height: 1.35;
  display: flex;
  align-items: center;
}

.tags {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  min-width: 120px;
}

.label {
  font-size: 12px;
  color: #6b7280;
}

.value {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    align-items: stretch;
  }

  .actions {
    margin-top: 12px;
    justify-content: flex-start;
  }
}
</style>
