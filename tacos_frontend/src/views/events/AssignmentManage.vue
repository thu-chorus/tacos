<template>
  <div class="page-container">
    <div class="card" v-if="!loading && assignment.id">
      <div class="card-content" style="padding: 10px 15px">
        <div class="header" style="margin-bottom: 16px">
          <h3>{{ assignment.title || '作业管理' }}</h3>
          <div class="actions">
            <button class="btn-modern warning sm-btn" @click="openEdit">
              <i-lucide-pencil class="btn-icon" />
              <span>编辑作业</span>
            </button>
          </div>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="label">提交情况</div>
            <div class="value">
              <span style="font-weight: 600; font-size: 15px"
                >{{ submittedCount }} / {{ totalMemberCount }}</span
              >
              <span style="margin-left: 8px; color: #6b7280; font-size: 13px"
                >（不含非成员管理员）</span
              >
            </div>
          </div>
          <div class="info-item">
            <div class="label">批改情况</div>
            <div class="value">
              <span style="font-weight: 600; font-size: 15px"
                >{{ gradedCount }} / {{ submittedCount }}</span
              >
              <span style="margin-left: 8px; color: #6b7280; font-size: 13px"
                >（已提交作业中）</span
              >
            </div>
          </div>
          <div class="info-item">
            <div class="label">作业状态</div>
            <div class="value">
              <el-tag v-if="isClosed" type="warning" size="small">已截止</el-tag>
              <el-tag v-else type="success" size="small">进行中</el-tag>
            </div>
          </div>
          <div class="info-item">
            <div class="label">作业截止时间</div>
            <div class="value">{{ formatDateTime(assignment.deadline) }}</div>
          </div>
          <div
            class="info-item"
            v-if="assignment.attachments && assignment.attachments.length"
            style="grid-column: span 1"
          >
            <div class="label">作业附件</div>
            <div class="value">
              <div class="attachment-list">
                <div v-for="att in assignment.attachments" :key="att.id" class="attachment-item">
                  <el-image
                    v-if="isImage(att.file)"
                    :src="att.file"
                    :preview-src-list="[att.file]"
                    :preview-teleported="true"
                    fit="cover"
                    style="width: 140px; height: 90px; border-radius: 6px"
                    @error="onImageError"
                  />
                  <audio
                    v-else-if="isAudio(att.file)"
                    :src="att.file"
                    controls
                    style="width: 260px"
                    @error="onAudioError"
                  />
                  <el-link v-else :href="att.file" target="_blank" type="primary">{{
                    getFileName(att.file)
                  }}</el-link>
                </div>
              </div>
            </div>
          </div>

          <div class="info-item" v-if="assignment.description" style="grid-column: span 2">
            <div class="label">作业说明</div>
            <div class="value assignment-desc" v-html="formatText(assignment.description)"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="margin-bottom: -10px">
        <el-form :model="search" inline @keyup.enter="load">
          <el-form-item label="姓名">
            <el-input
              v-model="search.name"
              placeholder="请输入姓名"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item label="学号">
            <el-input
              v-model="search.user_id"
              placeholder="请输入学号"
              clearable
              style="max-width: 220px"
            />
          </el-form-item>
          <el-form-item label="声部">
            <el-select
              v-model="search.voice_part"
              placeholder="请选择声部"
              clearable
              style="width: 150px"
            >
              <el-option v-for="v in voiceParts" :key="v" :label="v" :value="v" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="search.only_submitted">只看已提交</el-checkbox>
          </el-form-item>
          <el-form-item>
            <button
              class="btn-modern primary sm-btn"
              style="margin-right: 10px"
              type="button"
              @click="load"
            >
              <i-lucide-search class="btn-icon" />
              <span>搜索</span>
            </button>
            <button class="btn-modern ghost sm-btn" type="button" @click="reset">
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
          <h3>队员作业批改</h3>
          <div class="actions">
            <button class="btn-modern success sm-btn" @click="exportXlsx" :disabled="exporting">
              <i-lucide-download class="btn-icon" />
              <span>导出成绩</span>
            </button>
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
                <th style="min-width: 90px">姓名</th>
                <th style="min-width: 130px">学号</th>
                <th style="min-width: 60px">声部</th>
                <th style="min-width: 60px">梯队</th>
                <th style="min-width: 70px">状态</th>
                <th style="min-width: 240px">附件</th>
                <th style="min-width: 200px">文字</th>
                <th style="min-width: 100px">批改分数</th>
                <th style="min-width: 240px">批改评语</th>
                <th style="min-width: 140px">提交时间</th>
                <th style="min-width: 140px">批改时间</th>
                <th class="sticky-right" style="min-width: 60px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="rows.length === 0">
                <td colspan="12" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in rows" :key="row.id || row.member_user_id" class="assignment-row">
                <td>{{ row.member_name }}</td>
                <td>{{ row.member_user_id }}</td>
                <td>
                  <el-tag :type="getVoicePartType(row.voice_part)">{{
                    row.voice_part || '-'
                  }}</el-tag>
                </td>
                <td>
                  <el-tag :type="row.tier === '一队' ? 'danger' : 'primary'">{{
                    row.tier || '-'
                  }}</el-tag>
                </td>
                <td>
                  <el-tag v-if="!row.id" type="info" size="small">未提交</el-tag>
                  <el-tag v-else-if="row.graded_at" type="success" size="small">已批改</el-tag>
                  <el-tag v-else type="warning" size="small">未批改</el-tag>
                </td>
                <td>
                  <div class="cell-scrollable">
                    <div class="attachment-list">
                      <div
                        v-for="att in row.attachments || []"
                        :key="att.id"
                        class="attachment-item"
                      >
                        <el-image
                          v-if="isImage(att.file)"
                          :src="att.file"
                          :preview-src-list="[att.file]"
                          :preview-teleported="true"
                          fit="cover"
                          style="width: 120px; height: 40px"
                          @error="onImageError"
                        />
                        <audio
                          v-else-if="isAudio(att.file)"
                          :src="att.file"
                          controls
                          style="width: 250px; margin-top: 6px"
                          @error="onAudioError"
                        />
                        <el-link v-else :href="att.file" target="_blank" type="primary">{{
                          getFileName(att.file)
                        }}</el-link>
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="cell-scrollable">
                    <span class="mono">{{ row.text || '-' }}</span>
                  </div>
                </td>
                <td>
                  <el-input
                    v-model="row._grade"
                    placeholder="可留空"
                    :disabled="!row.id"
                    size="small"
                  />
                </td>
                <td>
                  <el-input
                    v-model="row._comment"
                    placeholder="评语"
                    :disabled="!row.id"
                    size="small"
                  />
                </td>
                <td>
                  <span class="time-text">{{ formatDateTime(row.submitted_at) || '-' }}</span>
                </td>
                <td>
                  <span class="time-text">{{ formatDateTime(row.graded_at) || '-' }}</span>
                </td>
                <td class="sticky-right">
                  <button
                    class="btn-modern primary xsm-btn"
                    :disabled="!row.id || row._loading"
                    @click="gradeRow(row)"
                  >
                    <i-lucide-check class="btn-icon" />
                    <span>{{ row._loading ? '...' : '提交批改' }}</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <Pagination
          :current-page="page"
          :total-pages="totalPages"
          :page-size="pageSize"
          :total="total"
          @update:current-page="handleCurrentChange"
          @update:page-size="handleSizeChange"
        />
      </div>
    </div>
  </div>

  <el-dialog v-model="edit.visible" title="编辑作业" :width="dialogWidth">
    <el-form :model="edit.form" label-width="100px" ref="editFormRef" :rules="editRules">
      <el-form-item label="标题" prop="title" required>
        <el-input v-model="edit.form.title" placeholder="请输入作业标题" />
      </el-form-item>
      <el-form-item label="截止时间" prop="deadline" required>
        <el-date-picker
          v-model="edit.form.deadline"
          type="datetime"
          placeholder="选择截止时间"
          value-format="YYYY-MM-DDTHH:mm:ssZZ"
        />
      </el-form-item>
      <el-form-item label="说明">
        <el-input
          type="textarea"
          :rows="5"
          v-model="edit.form.description"
          placeholder="作业说明（可包含要求说明）"
        />
      </el-form-item>
      <el-form-item label="附件更新">
        <el-radio-group v-model="edit.form.replace">
          <el-radio :label="true">覆盖作业附件</el-radio>
          <el-radio :label="false">增加作业附件</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="选择文件">
        <el-upload
          :file-list="edit.files"
          :on-remove="(f, fs) => (edit.files = fs)"
          :on-change="(f, fs) => (edit.files = fs)"
          :auto-upload="false"
          multiple
        >
          <button type="button" class="btn-modern primary sm-btn">
            <i-lucide-upload class="btn-icon" />
            <span>选择附件</span>
          </button>
          <template #tip>
            <div class="el-upload__tip">支持多文件上传，单个不超过 20MB</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <button
        class="btn-modern ghost sm-btn"
        @click="edit.visible = false"
        style="margin-right: 8px"
      >
        <i-lucide-x class="btn-icon" />
        <span>取消</span>
      </button>
      <button
        class="btn-modern danger sm-btn"
        :disabled="edit.deleting || edit.loading"
        @click="confirmDelete"
        style="margin-right: 8px"
      >
        <i-lucide-trash-2 class="btn-icon" />
        <span>{{ edit.deleting ? '删除中...' : '删除' }}</span>
      </button>
      <button class="btn-modern primary sm-btn" :disabled="edit.loading" @click="saveEdit">
        <i-lucide-save class="btn-icon" />
        <span>{{ edit.loading ? '保存中...' : '保存' }}</span>
      </button>
    </template>
  </el-dialog>

  <!-- 删除作业确认对话框 -->
  <ConfirmDialog
    v-model:visible="deleteConfirmDialog.visible"
    title="删除作业"
    description="确定要删除该作业吗？该操作不可恢复。"
    confirm-text="确认删除"
    cancel-text="取消"
    :danger="true"
    @confirm="handleConfirmDelete"
  />
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notify } from '@/utils/notify'
import {
  getAssignmentDetail,
  listAssignmentSubmissions,
  gradeAssignmentSubmission,
  updateAssignment,
  deleteAssignment,
  exportAssignmentSubmissions
} from '@/api/events'
import { downloadFile } from '@/utils/download'
import { uploadAssignmentAttachments } from '@/api/events'
import Pagination from '@/components/common/Pagination.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { formatDateTime } from '@/utils/format'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
dayjs.extend(utc)
dayjs.extend(timezone)

export default {
  name: 'AssignmentManage',
  components: { Pagination, ConfirmDialog },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const eventId = route.params.id
    const assignmentId = route.params.assignmentId

    const loading = ref(true)
    const exporting = ref(false)
    const assignment = ref({})
    const search = ref({ name: '', user_id: '', voice_part: '', only_submitted: false })
    const voiceParts = ['S1', 'S2', 'A1', 'A2', 'T1', 'T2', 'B1', 'B2', 'Other']
    const allRows = ref([])
    const total = ref(0)
    const page = ref(1)
    const pageSize = ref(20)
    let detailRequestSeq = 0

    const isClosed = computed(() => {
      try {
        return (
          dayjs(assignment.value.deadline).tz('Asia/Shanghai').valueOf() <=
          dayjs().tz('Asia/Shanghai').valueOf()
        )
      } catch (e) {
        return false
      }
    })

    const edit = ref({
      visible: false,
      form: { title: '', deadline: '', description: '', replace: false },
      files: [],
      loading: false,
      deleting: false
    })

    // 删除确认对话框
    const deleteConfirmDialog = ref({
      visible: false
    })
    const editFormRef = ref(null)
    const editRules = {
      title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
      deadline: [{ required: true, message: '请选择截止时间', trigger: 'change' }]
    }

    const load = async () => {
      const requestSeq = ++detailRequestSeq
      loading.value = true
      try {
        const detail = await getAssignmentDetail(eventId, assignmentId)
        if (requestSeq !== detailRequestSeq) {
          return
        }
        assignment.value = detail.data

        const aggregated = []
        let currentPage = 1
        const fetchPageSize = 200
        let totalCount = Infinity

        while ((currentPage - 1) * fetchPageSize < totalCount) {
          const list = await listAssignmentSubmissions(eventId, assignmentId, {
            ...search.value,
            include_all: true,
            page: currentPage,
            page_size: fetchPageSize
          })
          if (requestSeq !== detailRequestSeq) {
            return
          }
          const results = Array.isArray(list?.data?.results) ? list.data.results : []
          totalCount = Number(list?.data?.count || results.length || 0)
          aggregated.push(...results)

          if (results.length < fetchPageSize) {
            break
          }
          currentPage += 1
          if (currentPage > 50) {
            break // 安全上限
          }
        }

        const mappedRows = aggregated.map(r => ({
          ...r,
          _grade: r.graded_score ?? null,
          _comment: r.graded_comment || '',
          _loading: false
        }))

        allRows.value = mappedRows
        total.value = allRows.value.length

        const maxPage = Math.max(1, Math.ceil(total.value / pageSize.value) || 1)
        if (page.value > maxPage) {
          page.value = maxPage
        }
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const reset = () => {
      search.value = { name: '', user_id: '', voice_part: '', only_submitted: false }
      page.value = 1
      load()
    }

    const exportXlsx = async () => {
      exporting.value = true
      notify.info('正在导出作业成绩，请稍候...')
      try {
        const params = { ...search.value, include_all: true }
        const res = await exportAssignmentSubmissions(eventId, assignmentId, params)
        const blob = res && res.data ? res.data : res
        const filename = `作业成绩_${assignment.value.title || assignmentId}.xlsx`
        downloadFile(blob, filename)
        notify.success('导出成功')
      } catch (e) {
        notify.error('导出失败')
        console.error('Export error:', e)
      } finally {
        exporting.value = false
      }
    }

    const gradeRow = async row => {
      if (!row.id) {
        return
      }
      row._loading = true
      try {
        const gradedScore = row._grade
        const gradedComment = row._comment
        await gradeAssignmentSubmission(eventId, assignmentId, {
          submissionId: row.id,
          gradedScore,
          gradedComment
        })
        await load()
      } finally {
        row._loading = false
      }
    }

    const goBack = () => router.push(`/events/${eventId}`)

    const formatText = s => String(s || '').replace(/\n/g, '<br/>')

    const openEdit = () => {
      edit.value.form = {
        title: assignment.value.title || '',
        deadline: assignment.value.deadline || '',
        description: assignment.value.description || '',
        replace: false
      }
      edit.value.files = []
      edit.value.visible = true
    }
    const saveEdit = async () => {
      if (editFormRef.value) {
        editFormRef.value.validate(async valid => {
          if (!valid) {
            return
          }
          await actuallySaveEdit()
        })
      } else {
        await actuallySaveEdit()
      }
    }
    const actuallySaveEdit = async () => {
      edit.value.loading = true
      try {
        await updateAssignment(eventId, assignmentId, { ...edit.value.form })
        const files = (edit.value.files || []).map(f => f.raw).filter(Boolean)
        if (files.length) {
          await uploadAssignmentAttachments(eventId, assignmentId, {
            files,
            replace: !!edit.value.form.replace
          })
        }
        edit.value.visible = false
        await load()
      } finally {
        edit.value.loading = false
      }
    }

    // 打开删除确认对话框
    const confirmDelete = () => {
      deleteConfirmDialog.value.visible = true
    }

    // 确认删除作业
    const handleConfirmDelete = async () => {
      edit.value.deleting = true
      try {
        await deleteAssignment(eventId, assignmentId)
        deleteConfirmDialog.value.visible = false
        edit.value.visible = false
        notify.success('作业删除成功')
        router.push(`/events/${eventId}`)
      } catch (e) {
        console.error('删除作业失败：', e)
        notify.error('删除失败')
      } finally {
        edit.value.deleting = false
      }
    }

    const dialogWidth = ref('520px')
    const computeDialogWidth = () => {
      const vw = window.innerWidth || 1024
      if (vw <= 360) {
        dialogWidth.value = '95vw'
        return
      }
      if (vw <= 768) {
        dialogWidth.value = '92vw'
        return
      }
      if (vw <= 1024) {
        dialogWidth.value = '640px'
        return
      }
      dialogWidth.value = '720px'
    }

    onMounted(() => {
      load()
      computeDialogWidth()
      window.addEventListener('resize', computeDialogWidth, { passive: true })
    })
    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidth)
    })

    const extractPathParam = rawUrl => {
      try {
        const u = String(rawUrl || '')
        if (u.includes('?')) {
          const urlObj = new URL(u, window.location.origin)
          const p = urlObj.searchParams.get('path')
          if (p) {
            return decodeURIComponent(p)
          }
        }
        return u
      } catch (e) {
        return String(rawUrl || '')
      }
    }
    const isImage = url => {
      const target = extractPathParam(url)
      return /(\.png|\.jpe?g|\.gif|\.webp|\.bmp|\.svg)$/i.test(String(target || ''))
    }
    const isAudio = url => {
      const target = extractPathParam(url)
      return /(\.mp3|\.wav|\.ogg|\.m4a|\.aac|\.flac)$/i.test(String(target || ''))
    }
    const getFileName = url => {
      try {
        const target = extractPathParam(url)
        const slash = target.lastIndexOf('/')
        return decodeURIComponent(slash >= 0 ? target.substring(slash + 1) : target) || '附件'
      } catch (e) {
        return '附件'
      }
    }

    const onImageError = () => {
      notify.error('图片加载失败或链接已过期，请刷新页面重试')
    }
    const onAudioError = () => {
      notify.error('音频加载失败或链接已过期，请刷新页面重试')
    }

    const totalPages = computed(() => {
      const size = Number(pageSize.value) || 10
      if (!total.value || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(total.value / size))
    })

    const handleCurrentChange = val => {
      page.value = val
    }

    const handleSizeChange = val => {
      pageSize.value = val
      const maxPage = Math.max(1, Math.ceil(total.value / pageSize.value) || 1)
      if (page.value > maxPage) {
        page.value = maxPage
      }
    }

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

    const rows = computed(() => {
      const start = (page.value - 1) * pageSize.value
      return allRows.value.slice(start, start + pageSize.value)
    })

    const totalMemberCount = computed(() => {
      return allRows.value.length
    })

    const submittedCount = computed(() => {
      return allRows.value.filter(r => r.id).length
    })

    const gradedCount = computed(() => {
      return allRows.value.filter(r => r.id && r.graded_at).length
    })

    return {
      loading,
      exporting,
      assignment,
      search,
      voiceParts,
      rows,
      total,
      page,
      pageSize,
      totalMemberCount,
      submittedCount,
      gradedCount,
      load,
      reset,
      gradeRow,
      goBack,
      edit,
      editFormRef,
      editRules,
      openEdit,
      saveEdit,
      confirmDelete,
      deleteConfirmDialog,
      handleConfirmDelete,
      isImage,
      isAudio,
      getFileName,
      onImageError,
      onAudioError,
      exportXlsx,
      dialogWidth,
      totalPages,
      handleCurrentChange,
      handleSizeChange,
      formatDateTime,
      formatText,
      isClosed,
      getVoicePartType
    }
  }
}
</script>

<style lang="scss" scoped>
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

// 使用与 MemberDetail.vue 一致的信息展示样式
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.info-item {
  display: flex;
  flex-direction: column;
}
.label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}
.value {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}

.assignment-desc {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #111827;
}

.table-wrapper {
  width: 100%;
  overflow: auto;
}
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
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

.mono {
  font-family: ui-monospace, Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
}

.time-text {
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}
.attachment-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.assignment-row td {
  max-height: none;
}

.cell-scrollable {
  max-height: none;
  overflow: visible;
  padding: 4px 0;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.el-image-viewer__wrapper {
  z-index: 5000 !important;
}
</style>
