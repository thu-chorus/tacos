<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 20px">
          <h3>{{ isEdit ? '编辑队员' : '新增队员' }}</h3>
          <div v-if="!isEdit && isAdmin" class="actions">
            <button
              class="btn-modern primary sm-btn bulk-create-button"
              type="button"
              @click="showBulkDialog = true"
            >
              批量新增
            </button>
          </div>
        </div>
        <PageLoading v-if="!formReady" />

        <el-form v-else ref="formRef" :model="formData" :rules="formRules" label-width="100px">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="学号" prop="user_id">
                <el-input v-model="formData.user_id" :disabled="isEdit" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="姓名" prop="name">
                <el-input v-model="formData.name" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="性别" prop="gender">
                <el-select v-model="formData.gender" placeholder="请选择" style="width: 100%">
                  <el-option label="男" value="男" />
                  <el-option label="女" value="女" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="微信号" prop="wechat_id">
                <el-input v-model="formData.wechat_id" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="声部" prop="voice_part">
                <el-select v-model="formData.voice_part" placeholder="请选择" style="width: 100%">
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
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="院系" prop="department">
                <div style="display: flex; gap: 8px; width: 100%">
                  <el-select
                    v-model="formData.department"
                    placeholder="请选择院系"
                    style="flex: 1"
                    filterable
                    clearable
                    :reserve-keyword="false"
                  >
                    <el-option v-for="d in DEPARTMENTS" :key="d" :label="d" :value="d" />
                  </el-select>
                </div>
              </el-form-item>
              <el-form-item
                v-if="formData.department === '其他'"
                label="院系名称"
                prop="department_other"
              >
                <el-input v-model="formData.department_other" placeholder="请填写院系名称" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="班级">
                <el-input v-model="formData.class_name" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="手机号" prop="phone_number">
                <el-input v-model="formData.phone_number" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="formData.email" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="宿舍">
                <el-input v-model="formData.dorm" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="生日">
                <el-date-picker
                  v-model="formData.birthday"
                  type="date"
                  placeholder="请选择生日或输入YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="籍贯">
                <el-row :gutter="12" style="width: 100%">
                  <el-col :xs="24" :sm="12">
                    <el-select
                      v-model="formData.hometown_province"
                      placeholder="请选择省份/地区"
                      style="width: 110px; min-width: 80px"
                      :teleported="false"
                      popper-class="wide-select-dropdown"
                    >
                      <el-option
                        v-for="province in PROVINCES"
                        :key="province"
                        :label="province"
                        :value="province"
                      />
                    </el-select>
                  </el-col>
                  <el-col :xs="24" :sm="12">
                    <el-select
                      v-model="formData.hometown_city"
                      placeholder="请选择城市/地区"
                      style="width: 110px; min-width: 80px"
                      :disabled="!formData.hometown_province"
                      :teleported="false"
                      popper-class="wide-select-dropdown"
                    >
                      <el-option
                        v-for="city in availableCities"
                        :key="city"
                        :label="city"
                        :value="city"
                      />
                    </el-select>
                  </el-col>
                </el-row>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="民族">
                <el-select
                  v-model="formData.ethnicity"
                  placeholder="请选择"
                  filterable
                  clearable
                  :reserve-keyword="false"
                >
                  <el-option v-for="e in ETHNICITY_OPTIONS" :key="e" :label="e" :value="e" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="政治面貌">
                <el-select
                  v-model="formData.political_status"
                  placeholder="请选择"
                  filterable
                  clearable
                  :reserve-keyword="false"
                >
                  <el-option v-for="p in POLITICAL_STATUS_OPTIONS" :key="p" :label="p" :value="p" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="党团关系所在">
                <el-select
                  v-model="formData.political_affiliation"
                  placeholder="请选择"
                  filterable
                  clearable
                  :reserve-keyword="false"
                >
                  <el-option
                    v-for="a in POLITICAL_AFFILIATION_OPTIONS"
                    :key="a"
                    :label="a"
                    :value="a"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="是否为特长生">
                <el-switch v-model="formData.is_specialty" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="是否为集中班">
                <el-switch v-model="formData.is_centralized" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="队内职务">
                <el-input v-model="formData.position" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="入队年月" prop="join_month">
                <el-date-picker
                  v-model="formData.join_month"
                  type="month"
                  placeholder="请选择入队年月或输入YYYY-MM"
                  value-format="YYYY-MM"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="预计毕业时间" prop="graduate_month">
                <el-date-picker
                  v-model="formData.graduate_month"
                  type="month"
                  placeholder="请选择预计毕业时间或输入YYYY-MM"
                  value-format="YYYY-MM"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="梯队">
                <el-select
                  v-model="formData.tier"
                  placeholder="请选择梯队"
                  style="width: 100%"
                  :disabled="!isAdmin"
                >
                  <el-option label="一队" value="一队" />
                  <el-option label="二队" value="二队" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col v-if="isAdmin" :xs="24" :sm="12">
              <el-form-item label="成员状态">
                <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
                  <el-option
                    v-for="s in MEMBER_STATUSES"
                    :key="s.value"
                    :label="s.label"
                    :value="s.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="签名">
                <el-input type="textarea" v-model="formData.portfolio" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 账户设置：仅在创建时显示 -->
          <el-row v-if="!isEdit" :gutter="24">
            <el-col :xs="24" :sm="12">
              <el-form-item label="是否管理员" prop="is_admin">
                <el-switch v-model="formData.is_admin" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="队员初始密码" prop="password">
                <el-input
                  v-model="formData.password"
                  show-password
                  placeholder="留空则使用系统默认初始密码"
                />
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
              {{ isEdit ? '更新' : '创建' }}
            </button>
            <button class="btn-modern ghost" type="button" @click="goBack">取消</button>
          </div>
        </el-form>
      </div>
    </div>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showBulkDialog" title="批量导入队员" width="700px">
      <div
        class="bulk-help"
        style="
          padding: 20px 28px 12px 28px;
          background: #fafbfc;
          border-radius: 8px;
          margin-bottom: 8px;
        "
      >
        <p style="margin-bottom: 6px">说明：</p>
        <p style="margin-bottom: 2px">- 支持 CSV 或 Excel (.xlsx) 文件；请使用 UTF-8 编码。</p>
        <p style="margin-bottom: 2px">
          - <strong>仅必填字段：user_id（学号）、name（姓名）</strong>。
        </p>
        <p style="margin-bottom: 2px">
          - 若 gender 为空，保持空白；若 voice_part 为空，默认 Other；若 微信号
          为空，默认"请及时填写正确微信号"。
        </p>
        <p style="margin-bottom: 2px">
          - 若 入队年月 为空，默认当月（YYYY-MM）；若 梯队 为空，默认"二队"；若 status 为空，默认
          ACTIVE。
        </p>
        <p style="margin-bottom: 2px">
          - gender 取值：男/女（可空）；voice_part 取值：S1/S2/A1/A2/T1/T2/B1/B2/Other（可空）。
        </p>
        <p style="margin-bottom: 2px">
          - join_month 使用 YYYY-MM，例如 2025-09；birthday 使用 YYYY-MM-DD。
        </p>
        <p style="margin-bottom: 2px">- 新用户默认密码：ChangeMe123!</p>
      </div>

      <div style="margin-bottom: 12px; display: flex; gap: 12px; padding: 0 28px">
        <button
          class="btn-modern primary sm-btn"
          @click="handleDownloadTemplate"
          :disabled="downloadingTemplate"
        >
          {{ downloadingTemplate ? '下载中...' : '下载模板' }}
        </button>
      </div>
      <div style="padding: 0 28px 8px 28px; display: flex; align-items: center; gap: 12px">
        <el-switch v-model="overrideExisting" />
        <span>是否覆盖已有队员信息（按学号覆盖）</span>
      </div>
      <div style="margin-bottom: 12px; display: flex; gap: 12px">
        <div style="width: 100%; display: flex; justify-content: center; align-items: center">
          <el-upload
            drag
            :auto-upload="false"
            :on-change="onFileChange"
            :before-upload="() => false"
            accept=".csv,.xlsx"
          >
            <el-icon class="el-icon--upload"><i class="el-icon-upload" /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .csv 或 .xlsx</div>
            </template>
          </el-upload>
        </div>
      </div>

      <div v-if="selectedFile" style="margin-bottom: 8px; color: #606266">
        已选择：{{ selectedFile.name }}
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 8px">
        <button class="btn-modern ghost sm-btn" @click="showBulkDialog = false">关闭</button>
        <button
          class="btn-modern primary sm-btn"
          :disabled="!selectedFile || importing"
          @click="handleBulkImport"
        >
          {{ importing ? '导入中...' : '开始导入' }}
        </button>
      </div>

      <el-divider />

      <div v-if="importResult.rows && importResult.rows.length">
        <div style="margin-bottom: 8px">
          导入完成：成功 {{ importResult.success }} 条，失败 {{ importResult.failed }} 条。
        </div>
        <el-table :data="importResult.rows" size="small" style="width: 100%">
          <el-table-column prop="index" label="原表行号" width="80" />
          <el-table-column prop="user_id" label="学号" width="140" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag
                :type="
                  scope.row.status === 'created' || scope.row.status === 'updated'
                    ? 'success'
                    : 'danger'
                "
              >
                {{
                  scope.row.status === 'created'
                    ? '创建成功'
                    : scope.row.status === 'updated'
                      ? '更新成功'
                      : '错误'
                }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="错误信息">
            <template #default="scope">
              <div v-if="scope.row.errors && scope.row.errors.length">
                <div v-for="(e, i) in scope.row.errors" :key="i">{{ e }}</div>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import {
  DEPARTMENTS,
  ETHNICITY_OPTIONS,
  POLITICAL_STATUS_OPTIONS,
  POLITICAL_AFFILIATION_OPTIONS,
  PROVINCES,
  CITIES,
  MEMBER_STATUSES
} from '@/utils/constants'
import { notify } from '@/utils/notify'
import {
  getMemberDetail,
  createMember,
  updateMember,
  downloadMemberImportTemplate,
  bulkImportMembers
} from '@/api/personnel'
import PageLoading from '@/components/common/PageLoading.vue'
import { downloadFile, getFilenameFromContentDisposition } from '@/utils/download'

export default {
  name: 'MemberForm',
  components: { PageLoading },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()

    const formRef = ref()
    const loading = ref(false)
    const submitting = ref(false)
    const showBulkDialog = ref(false)
    const selectedFile = ref(null)
    const importing = ref(false)
    const downloadingTemplate = ref(false)
    const overrideExisting = ref(false)
    const importResult = reactive({ total: 0, success: 0, failed: 0, rows: [] })

    const isEdit = computed(() => !!route.params.id)
    const formReady = ref(!isEdit.value)
    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const currentUser = computed(() => store.getters['auth/user'])
    const isSelf = ref(false)
    let detailRequestSeq = 0

    const formData = reactive({
      user_id: '',
      name: '',
      gender: '',
      wechat_id: '',
      voice_part: '',
      department: '',
      department_other: '',
      class_name: '',
      phone_number: '',
      email: '',
      dorm: '',
      birthday: '',
      // 籍贯相关：使用与 Profile 一致的省/市联动，并在提交时合成 hometown
      hometown_province: '',
      hometown_city: '',
      hometown: '',
      ethnicity: '',
      political_status: '',
      political_affiliation: '',
      is_specialty: false,
      is_centralized: false,
      position: '',
      join_month: '',
      graduate_month: '',
      tier: '二队',
      status: 'ACTIVE',
      portfolio: '',
      // 账号创建相关（仅创建时有效）
      is_admin: false,
      password: ''
    })

    const formRules = {
      user_id: [{ required: true, message: '请输入学号', trigger: 'blur' }],
      name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      department_other: [
        {
          validator: (_rule, value, callback) => {
            if (formData.department === '其他' && !value) {
              callback(new Error('当选择"其他"时，请填写院系名称'))
              return
            }
            callback()
          },
          trigger: 'blur'
        }
      ],
      phone_number: [{ pattern: /^\d{11}$/, message: '请输入11位手机号', trigger: 'blur' }],
      email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }],
      join_month: [
        { pattern: /^\d{4}-(0[1-9]|1[0-2])$/, message: '请输入YYYY-MM格式', trigger: 'blur' }
      ],
      graduate_month: [
        {
          validator: (_rule, value, callback) => {
            if (!isAdmin.value && !value) {
              callback(new Error('请选择预计毕业时间'))
              return
            }
            if (value && !/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) {
              callback(new Error('请输入YYYY-MM格式'))
              return
            }
            callback()
          },
          trigger: ['change', 'blur']
        }
      ],
      // 籍贯下拉在成员创建/编辑中非必填，不强制，但保留校验示例：
      password: [
        {
          validator: (_rule, value, callback) => {
            if (!value) {
              callback()
              return
            }
            if (value.length < 8) {
              callback(new Error('初始密码至少8位'))
              return
            }
            callback()
          },
          trigger: 'blur'
        }
      ]
    }

    // 可用城市列表
    const availableCities = computed(() => {
      if (!formData.hometown_province) {
        return []
      }
      return CITIES[formData.hometown_province] || []
    })

    // 合成 hometown
    const updateHometown = () => {
      if (formData.hometown_province && formData.hometown_city) {
        formData.hometown = `${formData.hometown_province} ${formData.hometown_city}`
      } else if (formData.hometown_province) {
        formData.hometown = formData.hometown_province
      } else {
        formData.hometown = ''
      }
    }

    const goBack = () => {
      // 优先使用 URL ref 参数，否则使用默认返回目标
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else {
        const fallback = `/personnel/members/${route.params.id}`
        router.push(fallback)
      }
    }

    const handleDownloadTemplate = async () => {
      try {
        downloadingTemplate.value = true
        const response = await downloadMemberImportTemplate()
        const filename =
          getFilenameFromContentDisposition(response.headers['content-disposition']) ||
          'members_import_template.xlsx'
        downloadFile(response.data, filename)
      } catch (e) {
        notify.error('模板下载失败')
      } finally {
        downloadingTemplate.value = false
      }
    }

    const onFileChange = file => {
      selectedFile.value = file && file.raw ? file.raw : null
    }

    const handleBulkImport = async () => {
      if (!selectedFile.value) {
        notify.warning('请先选择文件')
        return
      }
      try {
        importing.value = true
        const res = await bulkImportMembers(selectedFile.value, {
          override: overrideExisting.value
        })
        const data = res && res.data ? res.data : res
        importResult.total = data.total || 0
        importResult.success = data.success || 0
        importResult.failed = data.failed || 0
        importResult.rows = Array.isArray(data.rows) ? data.rows : []
        notify.success('导入完成')
      } catch (e) {
        notify.error(e && e.message ? e.message : '导入失败')
      } finally {
        importing.value = false
      }
    }

    const loadForEdit = async () => {
      const requestSeq = ++detailRequestSeq
      const memberId = route.params.id
      if (!isEdit.value) {
        formReady.value = true
        return
      }
      formReady.value = false
      isSelf.value = false
      loading.value = true
      try {
        const res = await getMemberDetail(memberId)
        if (requestSeq !== detailRequestSeq || String(memberId) !== String(route.params.id)) {
          return
        }
        const data = res.data || {}

        if (currentUser.value && data.user_id === currentUser.value.user_id) {
          isSelf.value = true
        }

        // 解析籍贯为省/市
        const hometown = data.hometown || ''
        let hometown_province = ''
        let hometown_city = ''
        if (hometown) {
          const parts = hometown.split(' ')
          if (parts.length >= 2) {
            hometown_province = parts[0]
            hometown_city = parts.slice(1).join(' ')
          } else {
            hometown_province = hometown
          }
        }

        Object.assign(formData, {
          user_id: data.user_id || '',
          name: data.name || '',
          gender: data.gender || '',
          wechat_id: data.wechat_id || '',
          voice_part: data.voice_part || '',
          department: data.department || '',
          department_other: data.department_other || '',
          class_name: data.class_name || data.class || '',
          phone_number: data.phone_number || '',
          email: data.email || '',
          dorm: data.dorm || '',
          birthday: data.birthday || '',
          hometown_province,
          hometown_city,
          hometown,
          ethnicity: data.ethnicity || '',
          political_status: data.political_status || '',
          political_affiliation: data.political_affiliation || '',
          is_specialty: !!data.is_specialty,
          is_centralized: !!data.is_centralized,
          position: data.position || '',
          join_month: data.join_month || '',
          graduate_month: data.graduate_month || '',
          tier: data.tier || '二队',
          status: data.status || 'ACTIVE',
          portfolio: data.portfolio || ''
        })
        updateHometown()
        formReady.value = true
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const buildCreatePayload = () => {
      // 仅在创建时包含 is_admin 与 password 字段
      const payload = { ...formData }
      if (!formData.password) {
        delete payload.password
      }
      return payload
    }

    const handleSubmit = async () => {
      if (!isAdmin.value && !isSelf.value) {
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

        // 确保 hometown 最新
        updateHometown()

        if (isEdit.value) {
          // 更新时不应传递 user_id / is_admin / password，以及中间态省/市字段
          // eslint-disable-next-line no-unused-vars
          const { user_id, is_admin, password, hometown_province, hometown_city, ...rest } =
            formData
          const updatePayload = { ...rest, hometown: formData.hometown }
          if (!isAdmin.value) {
            delete updatePayload.status
            delete updatePayload.tier
          }
          const lookupId = route.params.id
          await updateMember(lookupId, updatePayload, { skipErrorMessage: true })
          notify.success('队员信息更新成功')
          // 编辑保存后导航
          const refParam = route.query.ref
          // 如果从 Profile 页面来，直接返回 Profile
          if (refParam === '/profile') {
            router.push('/profile')
          } else if (refParam) {
            // 否则进入详情页，并将原 ref 传递给详情页
            router.push(`/personnel/members/${lookupId}?ref=${encodeURIComponent(refParam)}`)
          } else {
            router.push(`/personnel/members/${lookupId}`)
          }
        } else {
          const payload = buildCreatePayload()
          // 确保创建时 hometown 同步
          payload.hometown = formData.hometown
          // 删除省/市中间字段
          delete payload.hometown_province
          delete payload.hometown_city
          const created = await createMember(payload)
          const newId = created && created.data && created.data.id
          notify.success('队员创建成功')
          // 创建成功后跳转到详情页，将原 ref（来源列表页）传递给详情页
          const refParam = route.query.ref
          if (newId) {
            if (refParam) {
              router.push(`/personnel/members/${newId}?ref=${encodeURIComponent(refParam)}`)
            } else {
              router.push(
                `/personnel/members/${newId}?ref=${encodeURIComponent('/personnel/members')}`
              )
            }
          } else {
            router.push('/personnel/members')
          }
        }
      } catch (error) {
        console.error('Submit error:', error)
        const resp = error && error.response
        const data = resp && resp.data
        const details = data && data.data ? data.data : data
        let message = '操作失败'
        if (details && typeof details === 'object' && !Array.isArray(details)) {
          const detailText = Object.entries(details)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join('; ') : String(v)}`)
            .join(' | ')
          if (detailText) {
            message = detailText
          }
        } else if (data && data.message) {
          message = data.message
        }
        notify.error(message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => {
      if (isEdit.value) {
        loadForEdit()
      } else if (!isAdmin.value) {
        notify.error('无权限访问')
        router.push('/403')
        return
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
      isSelf,
      DEPARTMENTS,
      ETHNICITY_OPTIONS,
      POLITICAL_STATUS_OPTIONS,
      POLITICAL_AFFILIATION_OPTIONS,
      PROVINCES,
      CITIES,
      MEMBER_STATUSES,
      availableCities,
      formData,
      formRules,
      goBack,
      handleSubmit,
      isAdmin,
      showBulkDialog,
      selectedFile,
      importing,
      downloadingTemplate,
      importResult,
      overrideExisting,
      handleDownloadTemplate,
      onFileChange,
      handleBulkImport
    }
  }
}
</script>

<style lang="scss" scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.header h3 {
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.bulk-create-button {
  min-width: 72px;
  white-space: nowrap;
}

/* 下拉框宽度优化，保持与 Profile 一致 */
::deep(.wide-select-dropdown) {
  .el-select-dropdown__item {
    min-width: 200px;
    white-space: nowrap;
    overflow: visible;
    text-overflow: ellipsis;
  }
  .el-select-dropdown {
    min-width: 200px;
  }
}
</style>
