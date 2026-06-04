<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 20px">
          <h3 v-if="isEdit">编辑教师信息</h3>
          <h3 v-else>新增教师信息</h3>
        </div>
        <PageLoading v-if="!formReady" />

        <el-form v-else ref="formRef" :model="formData" :rules="formRules" label-width="80px">
          <el-row :gutter="24">
            <el-col :span="12" :xs="24">
              <el-form-item label="身份证号" prop="instructor_id">
                <el-input v-model="formData.instructor_id" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :span="12" :xs="24">
              <el-form-item label="姓名" prop="name">
                <el-input v-model="formData.name" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12" :xs="24">
              <el-form-item label="手机号" prop="phone_number">
                <el-input v-model="formData.phone_number" />
              </el-form-item>
            </el-col>
            <el-col :span="12" :xs="24">
              <el-form-item label="车牌号">
                <el-input v-model="formData.vehicle_number" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12" :xs="24">
              <el-form-item label="职称">
                <el-input v-model="formData.title" />
              </el-form-item>
            </el-col>
            <el-col :span="12" :xs="24">
              <el-form-item label="所属单位">
                <el-input v-model="formData.affiliation" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12" :xs="24">
              <el-form-item label="地址">
                <el-input v-model="formData.address" />
              </el-form-item>
            </el-col>
            <el-col :span="12" :xs="24">
              <el-form-item label="课时费">
                <el-input v-model="formData.fee" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12" :xs="24">
              <el-form-item label="是否外请">
                <el-switch v-model="formData.is_external" />
              </el-form-item>
            </el-col>
          </el-row>

          <div
            class="form-actions"
            style="margin-top: 12px; display: flex; gap: 8px; justify-content: right"
          >
            <button
              class="btn-modern primary"
              type="button"
              @click="handleSubmit"
              :disabled="submitting"
            >
              <i-lucide-save v-if="isEdit" class="btn-icon" />
              <i-lucide-plus v-else class="btn-icon" />
              <span>{{ isEdit ? '更新' : '创建' }}</span>
            </button>
            <button class="btn-modern ghost" type="button" @click="goBack">
              <i-lucide-x class="btn-icon" />
              <span>取消</span>
            </button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { notify } from '@/utils/notify'
import { getInstructorDetail, createInstructor, updateInstructor } from '@/api/personnel'
import PageLoading from '@/components/common/PageLoading.vue'

export default {
  name: 'InstructorForm',
  components: { PageLoading },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

    const formRef = ref()
    const loading = ref(false)
    const submitting = ref(false)

    const isEdit = computed(() => !!route.params.id)
    const formReady = ref(!isEdit.value)
    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    let detailRequestSeq = 0

    const formData = reactive({
      instructor_id: '',
      name: '',
      phone_number: '',
      vehicle_number: '',
      title: '',
      affiliation: '',
      address: '',
      fee: '',
      is_external: false
    })

    const formRules = {
      instructor_id: [
        { required: true, message: '请输入身份证号', trigger: 'blur' },
        {
          pattern: /^(\d{10}|\d{17}[\dXx])$/,
          message: '请输入10位工号或18位身份证号',
          trigger: 'blur'
        }
      ],
      name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      phone_number: [
        { required: true, message: '请输入手机号', trigger: 'blur' },
        { pattern: /^\d{11}$/, message: '请输入11位手机号', trigger: 'blur' }
      ]
    }

    const goBack = () => {
      // 优先使用 URL ref 参数
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else {
        router.push('/personnel/instructors')
      }
    }

    const loadForEdit = async () => {
      const requestSeq = ++detailRequestSeq
      const instructorId = route.params.id
      if (!isEdit.value) {
        formReady.value = true
        return
      }
      formReady.value = false
      loading.value = true
      try {
        const res = await getInstructorDetail(instructorId)
        if (requestSeq !== detailRequestSeq || String(instructorId) !== String(route.params.id)) {
          return
        }
        const data = res.data || {}
        Object.assign(formData, {
          instructor_id: data.instructor_id || '',
          name: data.name || '',
          phone_number: data.phone_number || '',
          vehicle_number: data.vehicle_number || '',
          title: data.title || '',
          affiliation: data.affiliation || '',
          address: data.address || '',
          fee: data.fee || '',
          is_external: !!data.is_external
        })
        formReady.value = true
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const handleSubmit = async () => {
      if (!isAdmin.value) {
        notify.error('无权限操作')
        router.push('/403')
        return
      }
      if (!formRef.value) {
        return
      }

      try {
        const valid = await formRef.value.validate()
        if (!valid) {
          return
        }

        submitting.value = true

        if (isEdit.value) {
          await updateInstructor(route.params.id, { ...formData })
          notify.success('教师信息更新成功')
        } else {
          await createInstructor({ ...formData })
          notify.success('教师创建成功')
        }

        // 使用 ref 参数返回来源页面
        const refParam = route.query.ref
        if (refParam) {
          router.push(decodeURIComponent(refParam))
        } else {
          router.push('/personnel/instructors')
        }
      } catch (error) {
        console.error('Submit error:', error)
        notify.error('操作失败')
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => {
      if (!isAdmin.value) {
        notify.error('无权限访问')
        router.push('/403')
        return
      }
      if (isEdit.value) {
        loadForEdit()
      }
    })

    watch(
      () => route.params.id,
      () => {
        if (isEdit.value) {
          loadForEdit()
        }
      }
    )

    return {
      formRef,
      loading,
      formReady,
      submitting,
      isEdit,
      formData,
      formRules,
      goBack,
      handleSubmit
    }
  }
}
</script>

<style lang="scss" scoped></style>
