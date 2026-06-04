<template>
  <div class="page-container">
    <div v-if="!pageLoaded" class="card">
      <div class="card-content">
        <PageLoading />
      </div>
    </div>

    <template v-else>
      <div class="card">
        <div class="card-content" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 16px">
            <h3>{{ assignment.title || '作业详情' }}</h3>
            <div class="actions">
              <button v-if="canManage" class="btn-modern primary sm-btn" @click="goManage">
                <i-lucide-settings class="btn-icon" />
                <span>管理</span>
              </button>
            </div>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <div class="label">作业状态</div>
              <div class="value">
                <el-space wrap>
                  <el-tag v-if="isClosed" type="info" size="small">已过期</el-tag>
                  <el-tag v-else type="success" size="small">进行中</el-tag>
                  <el-tag :type="assignmentStatus.type" size="small">{{
                    assignmentStatus.text
                  }}</el-tag>
                </el-space>
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

      <div class="card" v-if="submission">
        <div class="card-content" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 16px">
            <h3>作业提交记录</h3>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <div class="label">提交时间</div>
              <div class="value">{{ formatDateTime(submission.submitted_at) }}</div>
            </div>
            <div class="info-item" v-if="submission.text">
              <div class="label">提交文字</div>
              <div class="value">
                <span class="mono">{{ submission.text }}</span>
              </div>
            </div>

            <div
              class="info-item"
              v-if="submission.attachments && submission.attachments.length"
              style="grid-column: span 2"
            >
              <div class="label">已上传文件</div>
              <div class="value">
                <div class="attachment-list">
                  <div v-for="att in submission.attachments" :key="att.id" class="attachment-item">
                    <el-image
                      v-if="isImage(att.file)"
                      :src="att.file"
                      :preview-src-list="[att.file]"
                      :preview-teleported="true"
                      fit="cover"
                      style="width: 120px; height: 80px; border-radius: 6px"
                      @error="onImageError"
                    />
                    <audio
                      v-else-if="isAudio(att.file)"
                      :src="att.file"
                      controls
                      style="width: 260px; margin-top: 6px"
                      @error="onAudioError"
                    />
                    <el-link v-else :href="att.file" target="_blank" type="primary">{{
                      getFileName(att.file)
                    }}</el-link>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="section-title">批改结果</div>
          <div class="info-grid" v-if="submission.graded_at">
            <div class="info-item">
              <div class="label">批改分数</div>
              <div class="value">
                <el-tag type="success">{{ submission.graded_score ?? '-' }}</el-tag>
              </div>
            </div>
            <div class="info-item">
              <div class="label">批改时间</div>
              <div class="value">{{ formatDateTime(submission.graded_at) }}</div>
            </div>
            <div
              class="info-item"
              v-if="submission.graded_by_name || (isAdmin && submission.graded_by_user_id)"
            >
              <div class="label">批改人</div>
              <div class="value">
                <el-link type="primary" @click="goGrader(submission)">
                  <el-tag type="success">{{
                    submission.graded_by_name || (isAdmin ? submission.graded_by_user_id : '')
                  }}</el-tag>
                </el-link>
              </div>
            </div>
            <div class="info-item" v-if="submission.graded_comment" style="grid-column: span 2">
              <div class="label">批改评语</div>
              <div class="value">{{ submission.graded_comment }}</div>
            </div>
          </div>
          <p v-if="!submission.graded_at" style="color: #6b7280; margin-top: 8px">（尚未批改）</p>
        </div>
      </div>

      <div class="action-card-container">
        <div
          class="card card-clickable flat"
          :class="{ disabled: !canSubmit }"
          @click="openSubmitDialog"
        >
          <div class="card-content stat-content">
            <div class="stat-icon">
              <i-lucide-file-edit />
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ submission ? '重新提交作业' : '提交作业' }}</div>
              <div class="stat-label">
                {{ !canSubmit ? '作业已截止或不为活动成员' : '点击提交或更新作业' }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-dialog
        v-model="submitDialog.visible"
        :title="submission ? '重新提交作业' : '提交作业'"
        :width="dialogWidth"
      >
        <el-alert
          v-if="!isParticipantMember"
          title="仅活动参与成员可以提交作业"
          type="warning"
          show-icon
          :closable="false"
          style="margin-bottom: 16px"
        />
        <el-alert
          v-else-if="isClosed"
          title="作业已截止，提交入口关闭"
          type="warning"
          show-icon
          :closable="false"
          style="margin-bottom: 16px"
        />

        <el-form label-width="80px">
          <el-form-item label="文字">
            <el-input
              type="textarea"
              v-model="form.text"
              :rows="6"
              placeholder="可选，输入作业文字内容"
              :disabled="!canSubmit"
            />
          </el-form-item>
          <el-form-item label="文件">
            <el-upload
              :file-list="fileList"
              :on-remove="handleRemove"
              :before-upload="beforeUpload"
              :on-change="onFileChange"
              :auto-upload="false"
              :disabled="!canSubmit"
              multiple
            >
              <button type="button" class="btn-modern ghost sm-btn" :disabled="!canSubmit">
                <i-lucide-upload class="btn-icon" />
                <span>选择文件</span>
              </button>
              <template #tip>
                <div class="el-upload__tip">支持图片、音频等常见格式，每个不超过 5MB</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="附件选项">
            <el-radio-group v-model="form.replace" :disabled="!canSubmit">
              <el-radio :label="true">覆盖之前的附件</el-radio>
              <el-radio :label="false">追加到之前的附件</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <template #footer>
          <button
            type="button"
            class="btn-modern ghost sm-btn"
            @click="submitDialog.visible = false"
            style="margin-right: 10px"
          >
            <i-lucide-x class="btn-icon" />
            <span>取消</span>
          </button>
          <button
            type="button"
            class="btn-modern primary sm-btn"
            :disabled="!canSubmit || submitting"
            @click="doSubmit"
          >
            <i-lucide-send class="btn-icon" />
            <span>{{ submitting ? '提交中...' : '提交' }}</span>
          </button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { notify } from '@/utils/notify'
import PageLoading from '@/components/common/PageLoading.vue'
import {
  getAssignmentDetail,
  submitAssignment,
  getMyAssignmentSubmission,
  getEventDetail
} from '@/api/events'
import { formatDateTime } from '@/utils/format'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import { FileEdit as LucideFileEdit } from 'lucide-vue-next'
dayjs.extend(utc)
dayjs.extend(timezone)

export default {
  name: 'AssignmentDetail',
  components: {
    PageLoading,
    'i-lucide-file-edit': LucideFileEdit
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const eventId = computed(() => route.params.id)
    const assignmentId = computed(() => route.params.assignmentId)

    const loading = ref(false)
    const pageLoaded = ref(false)
    const submitting = ref(false)
    const assignment = ref({ attachments: [] })
    const submission = ref(null)
    const event = ref({})
    const form = ref({ text: '', replace: true })
    const fileList = ref([])
    let detailRequestSeq = 0
    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const submitDialog = ref({ visible: false })

    const canManage = computed(() => {
      return isAdmin.value || event.value?.relation === 'event_admin'
    })

    const isParticipantMember = computed(() => {
      return event.value?.is_participant === true
    })

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

    const canSubmit = computed(() => {
      return isParticipantMember.value && !isClosed.value
    })

    const assignmentStatus = computed(() => {
      if (!submission.value) {
        return { text: '未提交', type: 'danger' }
      }
      if (submission.value.graded_at) {
        return { text: '已批改', type: 'success' }
      }
      return { text: '未批改', type: 'warning' }
    })

    const load = async ({ reset = false } = {}) => {
      const requestSeq = ++detailRequestSeq
      const currentEventId = eventId.value
      const currentAssignmentId = assignmentId.value
      if (reset) {
        pageLoaded.value = false
      }
      loading.value = true
      try {
        const [assignmentResult, eventResult, mySubResult] = await Promise.allSettled([
          getAssignmentDetail(currentEventId, currentAssignmentId),
          getEventDetail(currentEventId),
          getMyAssignmentSubmission(currentEventId, currentAssignmentId)
        ])
        if (
          requestSeq !== detailRequestSeq ||
          String(currentEventId) !== String(eventId.value) ||
          String(currentAssignmentId) !== String(assignmentId.value)
        ) {
          return
        }
        if (assignmentResult.status === 'rejected') {
          throw assignmentResult.reason
        }
        if (eventResult.status === 'rejected') {
          throw eventResult.reason
        }
        const assignmentRes = assignmentResult.value
        const eventRes = eventResult.value
        const mySubRes = mySubResult.status === 'fulfilled' ? mySubResult.value : null
        assignment.value = assignmentRes.data
        event.value = eventRes.data
        // 设置分享页面信息
        if (assignment.value?.title) {
          store.dispatch('common/setSharePageInfo', `作业「${assignment.value.title}」`)
        }
        submission.value = mySubRes?.data?.submission || null
        form.value.text = submission.value?.text || ''
        pageLoaded.value = true
      } catch (error) {
        console.error('加载作业详情失败：', error)
        notify.error('加载作业详情失败')
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const doSubmit = async () => {
      submitting.value = true
      try {
        const files = fileList.value.map(f => f.raw).filter(Boolean)
        const oversize = files.filter(f => (f?.size || 0) > 5 * 1024 * 1024)
        if (oversize.length) {
          notify.error('单个文件大小不能超过 5MB')
          submitting.value = false
          return
        }
        await submitAssignment(eventId.value, assignmentId.value, {
          text: form.value.text,
          files,
          replace: !!form.value.replace
        })
        await load()
        fileList.value = []
        submitDialog.value.visible = false
        notify.success('提交成功')
      } finally {
        submitting.value = false
      }
    }

    const openSubmitDialog = () => {
      if (!canSubmit.value) {
        return
      }
      submitDialog.value.visible = true
    }

    const onFileChange = (_file, files) => {
      const filtered = (files || []).filter(f => {
        const size = f?.raw?.size ?? f?.size ?? 0
        if (size > 5 * 1024 * 1024) {
          notify.error('单个文件大小不能超过 5MB')
          return false
        }
        return true
      })
      fileList.value = filtered
    }
    const handleRemove = (_file, files) => {
      fileList.value = files
    }
    const beforeUpload = file => {
      const ok = file.size <= 5 * 1024 * 1024
      if (!ok) {
        notify.error('单个文件大小不能超过 5MB')
      }
      return ok
    }
    const goBack = () => router.push(`/events/${eventId.value}`)
    const goManage = () =>
      router.push(`/events/${eventId.value}/assignments/${assignmentId.value}/manage`)
    const formatText = s => String(s || '').replace(/\n/g, '<br/>')
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
      return /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(String(target || ''))
    }
    const isAudio = url => {
      const target = extractPathParam(url)
      return /\.(mp3|wav|ogg|m4a|aac|flac)$/i.test(String(target || ''))
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

    const goGrader = row => {
      const memberPublicId = row?.graded_by_member_public_id
      if (memberPublicId) {
        router.push({
          path: `/personnel/members/${memberPublicId}`,
          query: { ref: `/events/${eventId.value}/assignments/${assignmentId.value}` }
        })
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
      load({ reset: true })
      computeDialogWidth()
      window.addEventListener('resize', computeDialogWidth, { passive: true })
    })
    watch(
      () => [route.params.id, route.params.assignmentId],
      () => {
        load({ reset: true })
      }
    )
    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidth)
    })

    return {
      loading,
      pageLoaded,
      submitting,
      assignment,
      submission,
      event,
      isClosed,
      isParticipantMember,
      canSubmit,
      assignmentStatus,
      formatDateTime,
      form,
      fileList,
      onFileChange,
      handleRemove,
      beforeUpload,
      doSubmit,
      goBack,
      goManage,
      goGrader,
      formatText,
      isImage,
      isAudio,
      getFileName,
      onImageError,
      onAudioError,
      isAdmin,
      canManage,
      submitDialog,
      openSubmitDialog,
      dialogWidth
    }
  }
}
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
}

.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}

.card.disabled {
  opacity: 0.8;
}

.card-content {
  padding: 10px 12px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

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

.section-title {
  font-weight: 600;
  margin: 10px 0;
  color: #303133;
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

.mono {
  font-family: ui-monospace, Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  grid-column: span 12;
}

.action-card-container {
  width: 100%;
  margin-bottom: 12px;
}

.card-clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.card-clickable.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.card-clickable.disabled:hover {
  transform: none;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.card.flat {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  font-size: 18px;
  color: var(--brand-500, #9a56b5);
  margin-right: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(154, 86, 181, 0.1);
}

.stat-info {
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
}

.stat-number {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.stat-label {
  color: #6b7280;
  font-size: 0.85rem;
}

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
  padding: 12px;
}

:deep(.el-dialog__footer) {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }

  .cards-row {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
.el-image-viewer__wrapper {
  z-index: 5000 !important;
}
</style>
