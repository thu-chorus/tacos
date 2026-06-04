<template>
  <div class="page-container">
    <div v-if="!pageLoaded" class="card">
      <div class="card-content">
        <PageLoading />
      </div>
    </div>

    <template v-else>
      <div class="card">
        <div class="card-content" v-loading="loading" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 20px">
            <h3>{{ sheet?.title || '乐谱详情' }}</h3>
            <div class="actions">
              <button v-if="isAdmin" class="btn-modern warning sm-btn" @click="edit">
                <i-lucide-pencil class="btn-icon" />
                <span>编辑</span>
              </button>
            </div>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <div class="label">曲名</div>
              <div class="value">{{ sheet?.title || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">作词</div>
              <div class="value">{{ sheet?.lyricist || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">作曲</div>
              <div class="value">{{ sheet?.composer || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">编曲</div>
              <div class="value">{{ sheet?.arranger || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">版权说明</div>
              <div class="value">{{ sheet?.copyright_notice || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">版权限制</div>
              <div class="value">
                <el-tag :type="sheet?.is_restricted ? 'danger' : 'success'">
                  {{ sheet?.is_restricted ? '受限' : '公开' }}
                </el-tag>
              </div>
            </div>
            <div v-if="isAdmin" class="info-item">
              <div class="label">可见范围</div>
              <div class="value">
                <span v-if="sheet?.visible_to_all">全员</span>
                <span v-else>
                  自定义（活动 {{ (sheet?.visible_events || []).length }} 个，队员
                  {{ (sheet?.visible_members || []).length }} 人）
                </span>
              </div>
            </div>
            <div v-if="isAdmin && !sheet?.visible_to_all" class="info-item">
              <div class="label">可见活动</div>
              <div class="value">
                <div class="tag-list">
                  <el-tag v-for="e in sheet?.visible_events || []" :key="e.id">
                    <el-link type="primary" @click="goEvent(e)">{{ e.name }}</el-link>
                  </el-tag>
                </div>
              </div>
            </div>
            <div v-if="isAdmin && !sheet?.visible_to_all" class="info-item">
              <div class="label">可见队员</div>
              <div class="value">
                <div class="tag-list">
                  <el-tag v-for="m in sheet?.visible_members || []" :key="m.id">
                    {{ m.name }}（{{ m.user_id }}）
                  </el-tag>
                </div>
              </div>
            </div>
            <div class="info-item">
              <div class="label">简介</div>
              <div class="value">{{ sheet?.introduction || '—' }}</div>
            </div>
            <div class="info-item">
              <div class="label">上传时间</div>
              <div class="value">{{ formatDateTime(sheet?.upload_time) }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top: 10px">
        <div class="card-content" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 10px">
            <h3>PDF 预览</h3>
            <div class="actions">
              <button class="btn-modern primary sm-btn" @click="download">
                <i-lucide-download class="btn-icon" />
                <span>下载</span>
              </button>
            </div>
          </div>
          <div class="preview-section">
            <div
              class="preview-container"
              v-loading="pdfLoading"
              element-loading-text="正在生成预览..."
            >
              <template v-if="pdfUrl">
                <iframe
                  v-if="!isIOS"
                  class="pdf-frame"
                  :src="pdfUrl"
                  title="sheet-preview"
                ></iframe>
                <div v-else class="ios-preview-warning">
                  <div class="ios-pdf-container">
                    <object :data="pdfUrl" type="application/pdf" class="pdf-object">
                      <p>无法显示PDF，请点击上方按钮下载</p>
                    </object>
                  </div>
                </div>
              </template>
              <template v-else-if="!pdfLoading">
                <el-empty description="预览不可用，请使用右上角'下载'按钮" />
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { notify } from '@/utils/notify'
import {
  getSheetDetail,
  initiateDownload,
  getDownloadTask,
  getDownloadTaskStatus
} from '@/api/sheets'
import { formatDateTime } from '@/utils/format'
import PageLoading from '@/components/common/PageLoading.vue'
export default {
  name: 'SheetDetail',
  components: { PageLoading },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()

    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const sheetId = computed(() => route.params.id)
    const loading = ref(false)
    const pageLoaded = ref(false)
    const sheet = ref(null)
    const pdfUrl = ref('')
    const pdfLoading = ref(false)
    let previewPollTimer = null
    let disposed = false
    let detailRequestSeq = 0
    let previewRequestSeq = 0
    const previewPollIntervals = [1000, 1500, 2500, 4000, 6000, 8000, 10000]
    const previewPollTimeoutMs = 5 * 60 * 1000

    // 检测是否为 iOS 设备
    const isIOS = computed(() => {
      const ua = navigator.userAgent
      return /iPad|iPhone|iPod/.test(ua) || (ua.includes('Mac') && 'ontouchend' in document)
    })

    const load = async ({ reset = false } = {}) => {
      const requestSeq = ++detailRequestSeq
      const currentSheetId = sheetId.value
      if (reset) {
        pageLoaded.value = false
        sheet.value = null
      }
      loading.value = true
      try {
        const res = await getSheetDetail(currentSheetId)
        if (requestSeq !== detailRequestSeq || String(currentSheetId) !== String(sheetId.value)) {
          return
        }
        sheet.value = res.data
        // 设置分享页面信息
        if (sheet.value?.title) {
          store.dispatch('common/setSharePageInfo', `乐谱「${sheet.value.title}」`)
        }
        pageLoaded.value = true
      } catch (e) {
        notify.error('加载失败')
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    // 获取返回目标路径（不导航）
    const getBackDestination = () => {
      const ref = route.query && route.query.ref
      if (ref && typeof ref === 'string') {
        return ref
      }
      return '/sheets'
    }

    const goBack = () => {
      router.push(getBackDestination())
    }

    const edit = () => {
      // 传递详情页的返回目标给编辑页，编辑页保存后返回详情页时保留原 ref
      const backDest = getBackDestination()
      router.push(`/sheets/${sheetId.value}/edit?ref=${encodeURIComponent(backDest)}`)
    }
    const goEvent = e => {
      if (!e || !e.id) {
        return
      }
      router.push({ path: `/events/${e.id}`, query: { ref: `/sheets/${sheetId.value}` } })
    }
    const download = async () => {
      const loadingMsg = notify.loading('正在生成PDF，请稍候...')
      const fallbackFilename = `${sheet.value?.title || 'sheet'}.pdf`

      try {
        const initResp = await initiateDownload(sheetId.value)
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
              let filename = fallbackFilename

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

    const clearPdfUrl = () => {
      if (pdfUrl.value && pdfUrl.value.startsWith('blob:')) {
        window.URL.revokeObjectURL(pdfUrl.value)
      }
      pdfUrl.value = ''
    }

    const setPdfStreamUrl = url => {
      if (disposed) {
        return
      }
      clearPdfUrl()
      pdfUrl.value = url
    }

    const loadPreview = async () => {
      const requestSeq = ++previewRequestSeq
      const currentSheetId = sheetId.value
      if (previewPollTimer) {
        window.clearTimeout(previewPollTimer)
        previewPollTimer = null
      }
      clearPdfUrl()
      pdfLoading.value = true

      try {
        const initResp = await initiateDownload(currentSheetId, { preview: true })
        const taskId = initResp.data?.task_id
        const streamUrl = initResp.data?.stream_url

        if (!taskId || !streamUrl) {
          throw new Error('无法获取预览任务')
        }

        const startedAt = Date.now()
        let pollAttempt = 0
        const nextPollDelay = () => {
          const index = Math.min(pollAttempt, previewPollIntervals.length - 1)
          pollAttempt += 1
          return previewPollIntervals[index]
        }

        const pollTask = async () => {
          if (
            disposed ||
            requestSeq !== previewRequestSeq ||
            String(currentSheetId) !== String(sheetId.value)
          ) {
            return
          }
          try {
            const resp = await getDownloadTaskStatus(taskId)
            if (
              disposed ||
              requestSeq !== previewRequestSeq ||
              String(currentSheetId) !== String(sheetId.value)
            ) {
              return
            }
            const taskStatus = resp.data?.status

            if (taskStatus === 'PENDING' || taskStatus === 'PROCESSING') {
              if (Date.now() - startedAt > previewPollTimeoutMs) {
                clearPdfUrl()
                pdfLoading.value = false
                notify.warning('预览生成时间过长，请稍后刷新或直接下载')
                return
              }
              previewPollTimer = window.setTimeout(pollTask, nextPollDelay())
            } else if (taskStatus === 'COMPLETED') {
              setPdfStreamUrl(resp.data?.stream_url || streamUrl)
              pdfLoading.value = false
            } else if (taskStatus === 'FAILED') {
              clearPdfUrl()
              pdfLoading.value = false
              console.error('Preview generation failed:', resp.data?.error_message)
            } else {
              clearPdfUrl()
              pdfLoading.value = false
              console.error('Unexpected task status')
            }
          } catch (pollError) {
            if (requestSeq !== previewRequestSeq) {
              return
            }
            clearPdfUrl()
            pdfLoading.value = false
            console.error('Preview polling error:', pollError)
          }
        }

        pollTask()
      } catch (e) {
        if (requestSeq !== previewRequestSeq) {
          return
        }
        clearPdfUrl()
        pdfLoading.value = false
        console.error('Preview error:', e)
      }
    }

    onMounted(() => {
      load({ reset: true })
      loadPreview()
    })

    watch(
      () => route.params.id,
      () => {
        load({ reset: true })
        loadPreview()
      }
    )

    onUnmounted(() => {
      disposed = true
      previewRequestSeq += 1
      if (previewPollTimer) {
        window.clearTimeout(previewPollTimer)
      }
      clearPdfUrl()
    })

    return {
      goBack,
      sheet,
      loading,
      pageLoaded,
      edit,
      isAdmin,
      download,
      pdfUrl,
      pdfLoading,
      formatDateTime,
      goEvent,
      isIOS
    }
  }
}
</script>

<style lang="scss" scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions {
  display: inline-flex;
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
}
.value {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}
.tag-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preview-section {
  margin-top: 16px;

  .preview-title {
    font-size: 1.1rem;
    color: #303133;
    margin-bottom: 8px;
  }

  .preview-container {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    overflow: hidden;
    background: #fafafa;
    min-height: 400px;
  }

  .pdf-frame {
    width: 100%;
    height: 75vh;
    border: none;
    display: block;
    background: #fff;
  }

  .ios-preview-warning {
    padding: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .ios-pdf-container {
    width: 100%;
    margin-top: 16px;
    min-height: 60vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fff;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
  }

  .pdf-object {
    width: 100%;
    height: 60vh;
    border: none;
  }
}
@media (max-width: 568px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
