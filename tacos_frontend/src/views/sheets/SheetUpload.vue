<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 20px">
          <h3>上传乐谱</h3>
        </div>
        <el-form :model="form" label-width="80px">
          <el-form-item label="曲名" required>
            <el-input v-model="form.title" placeholder="请输入曲名" />
          </el-form-item>
          <el-form-item label="作词">
            <el-input v-model="form.lyricist" placeholder="请输入作词" />
          </el-form-item>
          <el-form-item label="作曲">
            <el-input v-model="form.composer" placeholder="请输入作曲" />
          </el-form-item>
          <el-form-item label="编曲">
            <el-input v-model="form.arranger" placeholder="请输入编曲" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input
              v-model="form.introduction"
              type="textarea"
              :rows="3"
              placeholder="请输入简介"
            />
          </el-form-item>
          <el-form-item label="版权说明">
            <el-input v-model="form.copyright_notice" placeholder="请输入版权说明（可选）" />
          </el-form-item>
          <el-form-item label="版权限制">
            <el-switch v-model="form.is_restricted" active-text="受限" inactive-text="公开" />
          </el-form-item>
          <el-form-item label="可见范围">
            <el-switch
              v-model="form.visible_to_all"
              active-text="全员可见"
              inactive-text="选择范围"
            />
          </el-form-item>
          <el-form-item label="校友可见">
            <el-switch v-model="form.visible_to_alumni" active-text="开放" inactive-text="关闭" />
          </el-form-item>
          <template v-if="!form.visible_to_all">
            <el-form-item label="选择活动">
              <el-select
                v-model="form.visible_event_ids"
                multiple
                filterable
                placeholder="选择可见的活动"
              >
                <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择队员">
              <el-select
                v-model="form.visible_member_ids"
                multiple
                filterable
                placeholder="选择可见的队员"
              >
                <el-option
                  v-for="m in members"
                  :key="m.id"
                  :label="m.name + '（' + m.user_id + '）'"
                  :value="m.id"
                />
              </el-select>
            </el-form-item>
          </template>

          <el-form-item label="PDF 文件" required>
            <el-upload
              drag
              :before-upload="beforeUpload"
              :http-request="doNothing"
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
              <template #tip>
                <div class="el-upload__tip">仅支持 PDF，且不超过 20MB</div>
              </template>
            </el-upload>
            <div v-if="file" class="file-selected">已选择：{{ file.name }}</div>
          </el-form-item>

          <div
            class="form-actions"
            style="margin-top: 12px; display: flex; gap: 8px; justify-content: right"
          >
            <button class="btn-modern primary" type="button" @click="submit" :disabled="submitting">
              <i-lucide-upload class="btn-icon" />
              <span>提交</span>
            </button>
            <button class="btn-modern ghost" type="button" @click="reset">
              <i-lucide-rotate-ccw class="btn-icon" />
              <span>重置</span>
            </button>
          </div>

          <el-progress v-if="submitting" :percentage="progress" style="max-width: 420px" />
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { notify } from '@/utils/notify'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadSheet } from '@/api/sheets'
import { getEventList } from '@/api/events'
import { getMemberList } from '@/api/personnel'

export default {
  name: 'SheetUpload',
  components: { UploadFilled },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const file = ref(null)
    const form = reactive({
      title: '',
      lyricist: '',
      composer: '',
      arranger: '',
      introduction: '',
      is_restricted: false,
      visible_to_all: true,
      visible_to_alumni: false,
      visible_event_ids: [],
      visible_member_ids: []
    })
    const submitting = ref(false)
    const progress = ref(0)
    const events = ref([])
    const members = ref([])

    const goBack = () => {
      // 优先使用 URL ref 参数
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else {
        router.back()
      }
    }

    const beforeUpload = raw => {
      if (!raw) {
        return false
      }
      if (!raw.name.toLowerCase().endsWith('.pdf')) {
        notify.error('仅支持 PDF 文件')
        return false
      }
      if (raw.size > 20 * 1024 * 1024) {
        notify.error('文件大小不能超过 20MB')
        return false
      }
      file.value = raw
      return false // 阻止 el-upload 自己上传，改为手动 submit
    }

    const doNothing = () => {}

    const submit = async () => {
      if (!file.value) {
        notify.error('请先选择 PDF 文件')
        return
      }
      if (!form.title) {
        notify.error('请填写曲名')
        return
      }
      if (
        !form.visible_to_all &&
        !form.visible_to_alumni &&
        !form.visible_event_ids.length &&
        !form.visible_member_ids.length
      ) {
        notify.error('未开启全员可见时，需至少选择校友可见、活动或队员')
        return
      }
      submitting.value = true
      progress.value = 0
      try {
        await uploadSheet(file.value, form, evt => {
          if (evt && evt.total) {
            progress.value = Math.round((evt.loaded / evt.total) * 100)
          }
        })
        notify.success('上传成功')
        // 上传成功后使用 ref 参数返回，或者返回列表页
        const refParam = route.query.ref
        if (refParam) {
          router.push(decodeURIComponent(refParam))
        } else {
          router.push('/sheets')
        }
      } catch (e) {
        notify.error('上传失败')
      } finally {
        submitting.value = false
      }
    }

    const reset = () => {
      file.value = null
      form.title = ''
      form.lyricist = ''
      form.composer = ''
      form.arranger = ''
      form.introduction = ''
      form.is_restricted = false
      form.visible_to_all = true
      form.visible_to_alumni = false
      form.visible_event_ids = []
      form.visible_member_ids = []
      progress.value = 0
    }

    onMounted(async () => {
      const [eventsResult, membersResult] = await Promise.allSettled([
        getEventList({ page_size: 1000 }),
        getMemberList({ page_size: 1000 })
      ])
      if (eventsResult.status === 'fulfilled') {
        const er = eventsResult.value
        events.value = er?.data?.results || er?.data || []
      }
      if (membersResult.status === 'fulfilled') {
        const mr = membersResult.value
        members.value = mr?.data?.results || mr?.data || []
      }
    })

    return {
      goBack,
      form,
      file,
      submitting,
      progress,
      beforeUpload,
      doNothing,
      submit,
      reset,
      events,
      members
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
.file-selected {
  margin-left: 12px;
  color: #606266;
}
</style>
