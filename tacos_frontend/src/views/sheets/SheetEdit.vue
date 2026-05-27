<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content" v-loading="loading">
        <div class="header" style="margin-bottom: 20px">
          <h3>编辑乐谱</h3>
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
              inactive-text="部分可见"
            />
          </el-form-item>
          <el-form-item label="校友可见">
            <el-switch v-model="form.visible_to_alumni" active-text="开放" inactive-text="关闭" />
          </el-form-item>
          <template v-if="!form.visible_to_all">
            <el-form-item label="选择关联活动">
              <el-select
                v-model="form.visible_event_ids"
                multiple
                filterable
                placeholder="选择相关联的活动（活动内的队员皆获得访问权限）"
              >
                <el-option v-for="e in events" :key="e.id" :label="e.name" :value="e.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择可见队员">
              <el-select
                v-model="form.visible_member_ids"
                multiple
                filterable
                placeholder="选择可见的队员（管理员始终可见）"
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
          <el-form-item label="简介">
            <el-input
              v-model="form.introduction"
              type="textarea"
              :rows="3"
              placeholder="请输入简介"
            />
          </el-form-item>

          <div
            class="form-actions"
            style="margin-top: 12px; display: flex; gap: 8px; justify-content: right"
          >
            <button class="btn-modern primary" type="button" @click="submit" :disabled="submitting">
              保存
            </button>
            <button
              v-if="isAdmin"
              class="btn-modern danger"
              type="button"
              :disabled="deleting || submitting"
              @click="handleDelete"
            >
              删除
            </button>
            <button class="btn-modern ghost" type="button" @click="goBack">取消</button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 删除乐谱确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteConfirmDialog.visible"
      title="删除乐谱"
      description="确定要删除该乐谱吗？此操作不可恢复。"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { notify } from '@/utils/notify'
import { getSheetDetail, updateSheet, deleteSheet } from '@/api/sheets'
import { getEventList } from '@/api/events'
import { getMemberList } from '@/api/personnel'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

export default {
  name: 'SheetEdit',
  components: { ConfirmDialog },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()

    const isAdmin = computed(() => store.getters['auth/isAdmin'])

    const sheetId = route.params.id
    const loading = ref(false)
    const submitting = ref(false)
    const deleting = ref(false)

    // 删除确认对话框
    const deleteConfirmDialog = ref({
      visible: false
    })
    const form = reactive({
      title: '',
      lyricist: '',
      composer: '',
      arranger: '',
      introduction: '',
      copyright_notice: '',
      is_restricted: false,
      visible_to_all: true,
      visible_to_alumni: false,
      visible_event_ids: [],
      visible_member_ids: []
    })
    const events = ref([])
    const members = ref([])

    const load = async () => {
      loading.value = true
      try {
        const res = await getSheetDetail(sheetId)
        const data = res.data || {}
        Object.assign(form, {
          title: data.title || '',
          lyricist: data.lyricist || '',
          composer: data.composer || '',
          arranger: data.arranger || '',
          introduction: data.introduction || '',
          copyright_notice: data.copyright_notice || '',
          is_restricted: !!data.is_restricted,
          visible_to_all: data.visible_to_all !== false,
          visible_to_alumni: !!data.visible_to_alumni,
          visible_event_ids: (data.visible_events || []).map(e => e.id),
          visible_member_ids: (data.visible_members || []).map(m => m.id)
        })
      } catch (e) {
        if (e?.response?.status === 404) {
          notify.warning('乐谱不存在或已删除')
          router.replace('/sheets')
          return
        }
        notify.error('加载失败')
      } finally {
        loading.value = false
      }
    }

    const goBack = () => {
      // 优先使用 URL ref 参数，否则使用浏览器返回
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else {
        router.back()
      }
    }

    const submit = async () => {
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
      try {
        await updateSheet(sheetId, {
          title: form.title,
          lyricist: form.lyricist,
          composer: form.composer,
          arranger: form.arranger,
          introduction: form.introduction,
          copyright_notice: form.copyright_notice,
          is_restricted: form.is_restricted,
          visible_to_all: form.visible_to_all,
          visible_to_alumni: form.visible_to_alumni,
          visible_event_ids: form.visible_event_ids,
          visible_member_ids: form.visible_member_ids
        })
        notify.success('保存成功')
        // 编辑保存后导航到详情页，并将原 ref 传递给详情页
        const refParam = route.query.ref
        if (refParam) {
          router.push(`/sheets/${sheetId}?ref=${encodeURIComponent(refParam)}`)
        } else {
          router.push(`/sheets/${sheetId}`)
        }
      } catch (e) {
        notify.error('保存失败')
      } finally {
        submitting.value = false
      }
    }

    // 打开删除确认对话框
    const handleDelete = () => {
      if (deleting.value) {
        return
      }
      deleteConfirmDialog.value.visible = true
    }

    // 确认删除乐谱
    const confirmDelete = async () => {
      deleting.value = true
      try {
        await deleteSheet(sheetId)
        notify.success('删除成功')
        deleteConfirmDialog.value.visible = false
        // 使用 replace，避免返回历史时回到已删除的详情页
        router.replace('/sheets')
      } catch (e) {
        notify.error('删除失败')
      } finally {
        deleting.value = false
      }
    }

    onMounted(async () => {
      await load()
      try {
        const [er, mr] = await Promise.all([
          getEventList({ page_size: 1000 }),
          getMemberList({ page_size: 1000 })
        ])
        events.value = er?.data?.results || er?.data || []
        members.value = mr?.data?.results || mr?.data || []
      } catch (e) {
        // 下拉数据加载失败时保留空列表
      }
    })

    return {
      goBack,
      form,
      loading,
      submitting,
      deleting,
      submit,
      handleDelete,
      deleteConfirmDialog,
      confirmDelete,
      isAdmin,
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
</style>
