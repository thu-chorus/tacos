<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 20px">
          <h3>{{ isEdit ? '编辑活动' : '创建活动' }}</h3>
        </div>

        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入活动名称" />
          </el-form-item>
          <el-form-item label="介绍" prop="introduction">
            <el-input
              v-model="form.introduction"
              type="textarea"
              :rows="4"
              placeholder="请输入活动介绍"
            />
          </el-form-item>
          <el-form-item label="公告" prop="announcement">
            <el-input
              v-model="form.announcement"
              type="textarea"
              :rows="3"
              placeholder="请输入活动公告（可选）"
            />
          </el-form-item>
          <el-form-item label="相关乐谱" prop="sheet_ids">
            <el-select
              v-model="form.sheet_ids"
              multiple
              filterable
              remote
              :reserve-keyword="false"
              :remote-method="querySheets"
              :loading="loadingSheets"
              placeholder="选择需要关联的乐谱"
              @visible-change="onSheetsDropdownVisibleChange"
            >
              <el-option
                v-for="s in sheetOptions"
                :key="s.id"
                :label="s.title + (s.composer ? '（' + s.composer + '）' : '')"
                :value="s.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="公告图片">
            <div style="display: flex; flex-direction: column; gap: 8px; width: 100%">
              <div class="announcement-images-edit" style="display: flex; flex-wrap: wrap">
                <div
                  v-for="img in annImages"
                  :key="'exist-' + img.id"
                  class="ann-image-item"
                  :class="{ 'to-delete': isAnnMarkedDelete(img.id) }"
                >
                  <el-image
                    :src="img.image"
                    :preview-src-list="annImages.map(i => i.image)"
                    fit="contain"
                  >
                    <template #error>
                      <div class="image-slot">（图片加载失败）</div>
                    </template>
                  </el-image>
                  <button
                    class="ann-delete-btn"
                    :class="isAnnMarkedDelete(img.id) ? 'warning' : 'danger'"
                    type="button"
                    @click="toggleDeleteAnnImage(img.id)"
                  >
                    <el-icon><Close /></el-icon>
                  </button>
                  <div v-if="isAnnMarkedDelete(img.id)" class="ann-badge">待删除</div>
                </div>

                <div v-for="(p, idx) in annStage.add" :key="'new-' + idx" class="ann-image-item">
                  <el-image :src="p.url" fit="contain">
                    <template #error>
                      <div class="image-slot">（预览失败）</div>
                    </template>
                  </el-image>
                  <button class="ann-delete-btn danger" type="button" @click="removeStagedAnn(idx)">
                    <el-icon><Close /></el-icon>
                  </button>
                  <div class="ann-badge new">待上传</div>
                </div>
              </div>
              <div class="ann-ops">
                <el-upload
                  :show-file-list="false"
                  :auto-upload="false"
                  accept="image/png,image/jpeg,image/gif"
                  :on-change="onAnnImageChange"
                >
                  <button type="button" class="btn-modern primary xsm-btn">上传图片</button>
                </el-upload>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="开始日期" prop="start_date">
            <el-date-picker
              v-model="form.start_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择开始日期"
            />
          </el-form-item>
          <el-form-item label="结束日期" prop="end_date">
            <el-date-picker
              v-model="form.end_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择结束日期"
            />
          </el-form-item>
          <el-form-item label="面向范围" prop="visibility">
            <el-select v-model="form.visibility" placeholder="请选择面向范围">
              <el-option label="面向全体" value="ALL" />
              <el-option label="面向一队" value="FIRST" />
              <el-option label="面向二队" value="SECOND" />
              <el-option label="面向部分" value="PARTIAL" />
            </el-select>
          </el-form-item>
          <el-form-item label="校友可见">
            <el-switch v-model="form.visible_to_alumni" active-text="开放" inactive-text="关闭" />
          </el-form-item>
          <el-form-item label="活动管理员" prop="admins">
            <el-select
              v-model="form.admins"
              multiple
              filterable
              remote
              :reserve-keyword="false"
              :remote-method="queryMembers"
              :loading="loadingMembers"
              placeholder="选择活动管理员"
              @visible-change="onMembersDropdownVisibleChange"
            >
              <el-option
                v-for="m in memberOptions"
                :key="m.id"
                :label="formatMemberOptionLabel(m)"
                :value="m.id"
                :disabled="isInvalidAdminOption(m)"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="参与人员" prop="participants">
            <el-select
              v-model="form.participants"
              multiple
              filterable
              remote
              :reserve-keyword="false"
              :remote-method="queryMembers"
              :loading="loadingMembers"
              placeholder="选择参与人员"
              @visible-change="onMembersDropdownVisibleChange"
            >
              <el-option
                v-for="m in memberOptions"
                :key="'p-' + m.id"
                :label="formatMemberOptionLabel(m)"
                :value="m.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="快捷导入">
            <div style="display: flex; gap: 8px; flex-wrap: wrap">
              <button
                class="btn-modern ghost sm-btn"
                type="button"
                :loading="importingTier === 'SECOND'"
                @click="importSecondTier"
              >
                一键导入二队成员
              </button>
              <button
                class="btn-modern ghost sm-btn"
                type="button"
                :loading="importingTier === 'FIRST'"
                @click="importFirstTier"
              >
                一键导入一队成员
              </button>
            </div>
          </el-form-item>

          <div
            class="form-actions"
            style="margin-top: 12px; display: flex; gap: 8px; justify-content: right"
          >
            <button
              class="btn-modern primary"
              type="button"
              @click="onSubmit"
              :disabled="submitting"
            >
              {{ isEdit ? '保存' : '创建' }}
            </button>
            <button v-if="isEdit" class="btn-modern danger" type="button" @click="deleteEvent">
              删除活动
            </button>
            <button class="btn-modern ghost" type="button" @click="goBack">取消</button>
          </div>
        </el-form>
      </div>
    </div>
    <ConfirmDialog
      v-model:visible="confirmDeleteVisible"
      title="确认删除活动？"
      description="删除后不可恢复。"
      confirm-text="删除"
      cancel-text="取消"
      :danger="true"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { getMemberList } from '@/api/personnel'
import { notify } from '@/utils/notify'
import { MEMBER_STATUSES } from '@/utils/constants'
import {
  createEvent,
  getEventAdminDetail,
  updateEvent,
  uploadEventAnnouncementImage,
  deleteEventAnnouncementImage,
  deleteEvent as deleteEventApi
} from '@/api/events'
import { getSheetList } from '@/api/sheets'
import { Close } from '@element-plus/icons-vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'EventForm',
  components: { ConfirmDialog },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const isEdit = computed(() => !!route.params.id)
    const eventIdForApi = computed(() => route.params.id)
    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const formRef = ref(null)
    const submitting = ref(false)
    const annImages = ref([])
    const annStage = ref({ add: [], removeIds: new Set() })
    const form = reactive({
      name: '',
      introduction: '',
      start_date: '',
      end_date: '',
      visibility: 'PARTIAL',
      visible_to_alumni: false,
      admins: [],
      participants: [],
      announcement: '',
      sheet_ids: []
    })

    const isDateOrderValid = () => {
      try {
        if (!form.start_date || !form.end_date) {
          return true
        }
        return new Date(form.start_date).getTime() <= new Date(form.end_date).getTime()
      } catch (e) {
        return true
      }
    }
    const validateStartDate = (_rule, value, callback) => {
      if (!value) {
        return callback(new Error('请选择开始日期'))
      }
      if (!isDateOrderValid()) {
        return callback(new Error('开始时间必须早于结束时间'))
      }
      callback()
    }
    const validateEndDate = (_rule, value, callback) => {
      if (!value) {
        return callback(new Error('请选择结束日期'))
      }
      if (!isDateOrderValid()) {
        return callback(new Error('开始时间必须早于结束时间'))
      }
      callback()
    }
    function getInvalidAdminNames() {
      if (form.visible_to_alumni) {
        return []
      }
      return (form.admins || [])
        .map(id => selectedMemberMap.value.get(id))
        .filter(member => member?.status === 'ALUMNI')
        .map(member => member.name || member.user_id || member.id)
    }

    function validateAdmins(_rule, value, callback) {
      if (!Array.isArray(value) || value.length === 0) {
        return callback(new Error('请至少选择一位活动管理员'))
      }
      const invalidNames = getInvalidAdminNames()
      if (invalidNames.length > 0) {
        return callback(new Error(`校友不能担任校友不可见活动的管理员：${invalidNames.join('、')}`))
      }
      callback()
    }

    const rules = {
      name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
      introduction: [{ required: true, message: '请输入介绍', trigger: 'blur' }],
      start_date: [
        { required: true, message: '请选择开始日期', trigger: 'change' },
        { validator: validateStartDate, trigger: 'change' }
      ],
      end_date: [
        { required: true, message: '请选择结束日期', trigger: 'change' },
        { validator: validateEndDate, trigger: 'change' }
      ],
      admins: [{ validator: validateAdmins, trigger: 'change' }],
      visibility: [{ required: true, message: '请选择面向范围', trigger: 'change' }]
    }

    const memberOptions = ref([])
    const loadingMembers = ref(false)
    const importingTier = ref('') // '', 'FIRST', 'SECOND'
    const selectedSeed = ref([])
    const sheetOptions = ref([])
    const selectedSheetSeed = ref([])
    const loadingSheets = ref(false)
    const selectedMemberMap = computed(() => {
      const map = new Map()
      ;(selectedSeed.value || []).forEach(member => {
        if (member?.id) {
          map.set(member.id, member)
        }
      })
      ;(memberOptions.value || []).forEach(member => {
        if (member?.id) {
          map.set(member.id, member)
        }
      })
      return map
    })

    const getMemberStatusLabel = status =>
      (MEMBER_STATUSES.find(item => item.value === status) || {}).label || ''

    const formatMemberOptionLabel = member => {
      const base = isAdmin.value
        ? `${member.name || '-'}（${member.user_id || '-'}）`
        : member.name || '-'
      const statusLabel = getMemberStatusLabel(member.status)
      return statusLabel && member.status !== 'ACTIVE' ? `${base}（${statusLabel}）` : base
    }

    const isInvalidAdminOption = member => {
      return !form.visible_to_alumni && member?.status === 'ALUMNI'
    }

    const queryMembers = async query => {
      loadingMembers.value = true
      try {
        const params = { page_size: 1000 }
        const q = query && String(query).trim()
        if (q) {
          // 用 user_id 模糊匹配；或用姓名模糊匹配
          if (/^\d+$/.test(q)) {
            params.user_id = q
          } else {
            params.name__icontains = q
          }
        }
        const res = await getMemberList(params)
        const fetched = res.data?.results || res.data || []
        const mergedMap = new Map()
        fetched.forEach(m => mergedMap.set(m.id, m))
        if (!q) {
          ;(selectedSeed.value || []).forEach(m => {
            if (!mergedMap.has(m.id)) {
              mergedMap.set(m.id, m)
            }
          })
        }
        memberOptions.value = Array.from(mergedMap.values())
      } finally {
        loadingMembers.value = false
      }
    }

    const onMembersDropdownVisibleChange = async visible => {
      if (visible && (!memberOptions.value || memberOptions.value.length === 0)) {
        await queryMembers('')
      }
    }

    const fetchAllMembersByTier = async tier => {
      const pageSize = 1000
      let page = 1
      let results = []
      let total = 0
      const first = await getMemberList({ tier, page, page_size: pageSize })
      const firstData = first && first.data ? first.data : first
      const firstResults = firstData?.results || firstData || []
      results = results.concat(firstResults)
      total =
        firstData?.count !== null && firstData?.count !== undefined
          ? firstData.count
          : results.length
      const totalPages = Math.max(1, Math.ceil(total / pageSize))
      while (page < totalPages) {
        page += 1
        const res = await getMemberList({ tier, page, page_size: pageSize })
        const data = res && res.data ? res.data : res
        const items = data?.results || data || []
        results = results.concat(items)
      }
      return results
    }

    const importTierMembers = async tierLabel => {
      try {
        importingTier.value = tierLabel === '一队' ? 'FIRST' : 'SECOND'
        const members = await fetchAllMembersByTier(tierLabel)
        if (!Array.isArray(members) || members.length === 0) {
          notify.info(`未找到${tierLabel}成员`)
          return
        }
        const current = new Set(form.participants || [])
        members.forEach(m => {
          if (m && m.id !== null && m.id !== undefined) {
            current.add(m.id)
          }
        })
        form.participants = Array.from(current)
        const map = new Map((memberOptions.value || []).map(m => [m.id, m]))
        members.forEach(m => {
          if (m && m.id !== null && m.id !== undefined) {
            map.set(m.id, m)
          }
        })
        memberOptions.value = Array.from(map.values())
        const seedMap = new Map((selectedSeed.value || []).map(m => [m.id, m]))
        members.forEach(m => {
          if (m && m.id !== null && m.id !== undefined) {
            seedMap.set(m.id, m)
          }
        })
        selectedSeed.value = Array.from(seedMap.values())
        notify.success(`已导入${tierLabel}成员 ${members.length} 人`)
      } catch (e) {
        notify.error('导入失败')
      } finally {
        importingTier.value = ''
      }
    }

    const importFirstTier = () => importTierMembers('一队')
    const importSecondTier = () => importTierMembers('二队')

    const loadDetailIfEdit = async () => {
      if (!isEdit.value) {
        return
      }
      const res = await getEventAdminDetail(eventIdForApi.value)
      const d = res.data
      form.name = d.name
      form.introduction = d.introduction
      form.announcement = d.announcement || ''
      form.start_date = d.start_date
      form.end_date = d.end_date
      form.visibility = d.visibility || 'PARTIAL'
      form.visible_to_alumni = !!d.visible_to_alumni
      form.admins = (d.admins_detail || []).map(x => x.id)
      form.participants = (d.participants_detail || []).map(x => x.id)
      form.sheet_ids = (d.sheets || []).map(x => x.id)
      annImages.value = d.announcement_images || []
      selectedSheetSeed.value = d.sheets || []
      selectedSeed.value = [...(d.admins_detail || []), ...(d.participants_detail || [])]
      // 立即将已选成员注入下拉选项
      const seedMap = new Map()
      ;(selectedSeed.value || []).forEach(m => seedMap.set(m.id, m))
      memberOptions.value = Array.from(seedMap.values())
    }

    const onSubmit = () => {
      formRef.value.validate(async valid => {
        if (!valid) {
          return
        }
        submitting.value = true
        try {
          if (isEdit.value) {
            await updateEvent(eventIdForApi.value, form)
            const toDelete = Array.from(annStage.value.removeIds)
            for (const imageId of toDelete) {
              try {
                await deleteEventAnnouncementImage(eventIdForApi.value, imageId)
              } catch {
                // 忽略删除图片时的错误，继续处理其他图片
              }
            }
            for (const p of annStage.value.add) {
              try {
                await uploadEventAnnouncementImage(eventIdForApi.value, p.file)
              } catch {
                // 忽略上传图片时的错误，继续处理其他图片
              }
            }
            annStage.value.add.forEach(p => {
              try {
                if (p.url) {
                  URL.revokeObjectURL(p.url)
                }
              } catch {
                // 忽略URL释放错误
              }
            })
            annStage.value = { add: [], removeIds: new Set() }
            // 编辑保存后导航到详情页，并将原 ref 传递给详情页
            const refParam = route.query.ref
            if (refParam) {
              router.push(`/events/${route.params.id}?ref=${encodeURIComponent(refParam)}`)
            } else {
              router.push(`/events/${route.params.id}`)
            }
          } else {
            const created = await createEvent(form)
            const newId = created && created.data && created.data.id
            // 创建成功后跳转到详情页，将原 ref（来源列表页）传递给详情页
            const refParam = route.query.ref
            if (newId) {
              if (refParam) {
                router.push(`/events/${newId}?ref=${encodeURIComponent(refParam)}`)
              } else {
                router.push(`/events/${newId}?ref=${encodeURIComponent('/events')}`)
              }
            } else {
              router.push('/events')
            }
          }
        } finally {
          submitting.value = false
        }
      })
    }

    const goBack = () => {
      // 优先使用 URL ref 参数，否则使用默认返回目标
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else {
        const fallback = isEdit.value ? `/events/${route.params.id}` : '/events'
        router.push(fallback)
      }
    }

    const onAnnImageChange = async file => {
      const raw = file && file.raw
      if (!raw) {
        return
      }
      const allowed = ['image/jpeg', 'image/png', 'image/gif']
      const contentType = raw.type || ''
      if (!allowed.includes(contentType)) {
        notify.error('仅支持 JPG/PNG/GIF 图片')
        return
      }
      const maxBytes = 5 * 1024 * 1024
      if (raw.size > maxBytes) {
        notify.error('图片大小不能超过 5MB')
        return
      }
      const url = URL.createObjectURL(raw)
      annStage.value.add.push({ file: raw, url })
    }
    const removeStagedAnn = idx => {
      const item = annStage.value.add[idx]
      if (item && item.url) {
        try {
          URL.revokeObjectURL(item.url)
        } catch {
          // 忽略URL释放错误
        }
      }
      annStage.value.add.splice(idx, 1)
    }
    const toggleDeleteAnnImage = imageId => {
      const set = annStage.value.removeIds
      if (set.has(imageId)) {
        set.delete(imageId)
      } else {
        set.add(imageId)
      }
    }
    const isAnnMarkedDelete = imageId => annStage.value.removeIds.has(imageId)

    const querySheets = async query => {
      loadingSheets.value = true
      try {
        const params = { page_size: 1000 }
        const q = query && String(query).trim()
        if (q) {
          params.search = q
        }
        const res = await getSheetList(params)
        const fetched = res.data?.results || res.data || []
        const optionMap = new Map()
        ;(selectedSheetSeed.value || []).forEach(s => optionMap.set(s.id, s))
        ;(sheetOptions.value || []).forEach(s => optionMap.set(s.id, s))
        fetched.forEach(s => optionMap.set(s.id, s))

        const selectedIds = Array.isArray(form.sheet_ids) ? form.sheet_ids : []
        const selectedIdSet = new Set(selectedIds)
        const selectedOptions = selectedIds.map(id => optionMap.get(id)).filter(Boolean)
        const unselectedOptions = fetched.filter(s => !selectedIdSet.has(s.id))
        sheetOptions.value = [...selectedOptions, ...unselectedOptions]
      } finally {
        loadingSheets.value = false
      }
    }

    const onSheetsDropdownVisibleChange = async visible => {
      if (visible && (!sheetOptions.value || sheetOptions.value.length === 0)) {
        await querySheets('')
      }
    }

    const confirmDeleteVisible = ref(false)
    const deletingEvent = ref(false)
    const deleteEvent = () => {
      if (!isEdit.value) {
        return
      }
      confirmDeleteVisible.value = true
    }
    const handleConfirmDelete = async () => {
      if (!isEdit.value) {
        confirmDeleteVisible.value = false
        return
      }
      if (deletingEvent.value) {
        return
      }
      deletingEvent.value = true
      try {
        await deleteEventApi(eventIdForApi.value)
        notify.success('活动已删除')
        // 删除后跳转到列表页
        router.push('/events')
      } catch (e) {
        notify.error('删除失败')
      } finally {
        deletingEvent.value = false
        confirmDeleteVisible.value = false
      }
    }

    onMounted(async () => {
      await loadDetailIfEdit()
      await queryMembers('')
      await querySheets('')
    })

    watch(
      () => form.visible_to_alumni,
      () => {
        if (!formRef.value) {
          return
        }
        const result = formRef.value.validateField('admins', () => {})
        if (result && typeof result.catch === 'function') {
          result.catch(() => {})
        }
      }
    )

    return {
      formRef,
      form,
      rules,
      memberOptions,
      isEdit,
      submitting,
      onSubmit,
      goBack,
      annImages,
      onAnnImageChange,
      sheetOptions,
      loadingSheets,
      querySheets,
      queryMembers,
      deleteEvent,
      loadingMembers,
      onMembersDropdownVisibleChange,
      onSheetsDropdownVisibleChange,
      formatMemberOptionLabel,
      isInvalidAdminOption,
      isAdmin,
      importFirstTier,
      importSecondTier,
      importingTier,
      Close,
      annStage,
      removeStagedAnn,
      toggleDeleteAnnImage,
      isAnnMarkedDelete,
      confirmDeleteVisible,
      handleConfirmDelete,
      deletingEvent
    }
  }
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ann-image-item {
  position: relative;
  margin-right: 8px;
  margin-bottom: 8px;
  width: 120px;
  height: 90px;
}
.ann-image-item .ann-delete-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  transform: translate(0, 0);
  z-index: 2;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  padding: 0;
  color: #fff;
  &.danger {
    background: #f56c6c;
    &:hover {
      background: #e04848;
    }
  }
  &.warning {
    background: #e6a23c;
    &:hover {
      background: #d48d1d;
    }
  }
}
.ann-image-item :deep(.el-image) {
  width: 120px;
  height: 90px;
  display: block;
}
.ann-image-item .ann-badge {
  position: absolute;
  left: 4px;
  bottom: 4px;
  background: rgba(255, 165, 0, 0.9);
  color: #fff;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 2px;
}
.ann-image-item .ann-badge.new {
  background: rgba(64, 158, 255, 0.9);
}
</style>
