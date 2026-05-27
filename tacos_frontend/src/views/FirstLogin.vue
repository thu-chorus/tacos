<template>
  <div class="first-login-page">
    <div class="first-login-container">
      <div class="header">
        <h1 class="title">完善个人信息</h1>
        <p class="subtitle">欢迎使用TaCOS！请完善您的个人信息并设置新密码</p>
        <p class="subtitle">（进入系统后可以随时修改个人信息，并更改他人可见范围）</p>
      </div>

      <el-card>
        <el-form
          ref="formRef"
          :model="formData"
          :rules="formRules"
          label-width="120px"
          v-loading="loading"
        >
          <!-- 基础信息 -->
          <div class="form-section">
            <h3 class="section-title">基础信息</h3>
            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="学号 / 工号" prop="user_id">
                  <el-input v-model="formData.user_id" disabled />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="formData.name" placeholder="请输入姓名" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="性别" prop="gender">
                  <el-select v-model="formData.gender" style="width: 100%" placeholder="请选择性别">
                    <el-option label="男" value="男" />
                    <el-option label="女" value="女" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="微信号" prop="wechat_id">
                  <el-input v-model="formData.wechat_id" placeholder="请输入微信号" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="声部" prop="voice_part">
                  <el-select
                    v-model="formData.voice_part"
                    style="width: 100%"
                    placeholder="请选择声部"
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
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="梯队" prop="tier">
                  <el-select
                    v-model="formData.tier"
                    style="width: 100%"
                    placeholder="请选择梯队"
                    :disabled="true"
                  >
                    <el-option label="一队" value="一队" />
                    <el-option label="二队" value="二队" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="院系" prop="department">
                  <el-select
                    v-model="formData.department"
                    placeholder="请选择院系"
                    style="width: 100%"
                    filterable
                    clearable
                    :reserve-keyword="false"
                  >
                    <el-option v-for="d in DEPARTMENTS" :key="d" :label="d" :value="d" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="班级" prop="class_name">
                  <el-input v-model="formData.class_name" placeholder="请输入班级" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row v-if="formData.department === '其他'" :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="院系名称" prop="department_other">
                  <el-input v-model="formData.department_other" placeholder="请填写院系名称" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 联系信息 -->
          <div class="form-section">
            <h3 class="section-title">联系信息</h3>
            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="手机号" prop="phone_number">
                  <el-input
                    v-model="formData.phone_number"
                    placeholder="请输入手机号（中国大陆）"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="formData.email" placeholder="请输入邮箱" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="宿舍" prop="dorm">
                  <el-input
                    v-model="formData.dorm"
                    placeholder="请输入宿舍号，例：紫荆6#513、26#621，10北#601，红杉1201，双清2523，协和，校外"
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="生日" prop="birthday">
                  <el-date-picker
                    v-model="formData.birthday"
                    type="date"
                    placeholder="请选择生日或输入YYYY-MM-DD"
                    style="width: 100%"
                    value-format="YYYY-MM-DD"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 个人详细信息 -->
          <div class="form-section">
            <h3 class="section-title">详细信息</h3>
            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="籍贯" prop="hometown_province">
                  <el-row :gutter="12">
                    <el-col :xs="24" :sm="12">
                      <el-select
                        v-model="formData.hometown_province"
                        placeholder="请选择省份/地区"
                        style="width: 100px; min-width: 80px"
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
                        style="width: 100px; min-width: 80px"
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
                <el-form-item label="民族" prop="ethnicity">
                  <el-select
                    v-model="formData.ethnicity"
                    style="width: 100%"
                    placeholder="请选择民族"
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
                <el-form-item label="政治面貌" prop="political_status">
                  <el-select
                    v-model="formData.political_status"
                    style="width: 100%"
                    placeholder="请选择政治面貌"
                    filterable
                    clearable
                    :reserve-keyword="false"
                  >
                    <el-option
                      v-for="p in POLITICAL_STATUS_OPTIONS"
                      :key="p"
                      :label="p"
                      :value="p"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="党团关系所在" prop="political_affiliation">
                  <el-select
                    v-model="formData.political_affiliation"
                    style="width: 100%"
                    placeholder="请选择党团关系所在"
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
                <el-form-item label="是否为特长生" prop="is_specialty">
                  <el-switch v-model="formData.is_specialty" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="是否为集中班" prop="is_centralized">
                  <el-switch v-model="formData.is_centralized" />
                  <div
                    class="form-item-tip"
                    style="color: #909399; font-size: 12px; margin-left: 8px"
                  >
                    若不清楚则选择“否”
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="队内职务">
                  <el-input v-model="formData.position" placeholder="请输入队内职务（如有）" />
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
              <el-col :span="24">
                <el-form-item label="个人签名">
                  <el-input
                    type="textarea"
                    v-model="formData.portfolio"
                    placeholder="请输入个人签名或简介（整活区）"
                    :rows="3"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 密码设置 -->
          <div class="form-section">
            <h3 class="section-title">
              <el-icon><Lock /></el-icon>
              设置新密码
            </h3>
            <el-row :gutter="24">
              <el-col :xs="24" :sm="12">
                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="formData.new_password"
                    type="password"
                    placeholder="请输入新密码（至少8位）"
                    show-password
                  />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="确认新密码" prop="new_password_confirm">
                  <el-input
                    v-model="formData.new_password_confirm"
                    type="password"
                    placeholder="请再次输入新密码"
                    show-password
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <div class="form-actions">
            <button
              class="btn-modern primary"
              style="font-size: 15px; padding: 12px 28px"
              @click="handleSubmit"
              :disabled="submitting"
            >
              {{ submitting ? '提交中...' : '完成设置并进入系统' }}
            </button>
          </div>
        </el-form>
      </el-card>
    </div>
    <SiteFooter dark fixed />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Lock } from '@element-plus/icons-vue'
import { notify } from '@/utils/notify'
import {
  DEPARTMENTS,
  ETHNICITY_OPTIONS,
  POLITICAL_STATUS_OPTIONS,
  POLITICAL_AFFILIATION_OPTIONS,
  PROVINCES,
  CITIES
} from '@/utils/constants'
import { updateFirstLoginProfile, getProfile } from '@/api/auth'
import SiteFooter from '@/components/common/SiteFooter.vue'

export default {
  name: 'FirstLogin',
  components: {
    Lock,
    SiteFooter
  },
  setup() {
    const router = useRouter()
    const store = useStore()

    const formRef = ref()
    const loading = ref(false)
    const submitting = ref(false)

    // 计算可用的城市列表
    const availableCities = computed(() => {
      if (!formData.hometown_province) {
        return []
      }
      return CITIES[formData.hometown_province] || []
    })

    // // 监听省份变化，重置城市选择
    // })

    // // 监听城市变化，更新籍贯信息
    // })

    // 更新籍贯信息
    const updateHometown = () => {
      if (formData.hometown_province && formData.hometown_city) {
        formData.hometown = `${formData.hometown_province} ${formData.hometown_city}`
      } else if (formData.hometown_province) {
        formData.hometown = formData.hometown_province
      } else {
        formData.hometown = ''
      }
    }

    const formData = reactive({
      user_id: '',
      name: '',
      gender: '',
      wechat_id: '',
      voice_part: '',
      tier: '二队', // 默认二队
      department: '',
      department_other: '',
      class_name: '',
      phone_number: '',
      email: '',
      dorm: '',
      birthday: '',
      hometown_province: '',
      hometown_city: '',
      hometown: '', // 最终组合的籍贯信息
      ethnicity: '',
      political_status: '',
      political_affiliation: '',
      is_specialty: false,
      is_centralized: false,
      position: '',
      join_month: '',
      graduate_month: '',
      portfolio: '',
      new_password: '',
      new_password_confirm: ''
    })

    const formRules = {
      name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
      wechat_id: [{ required: true, message: '请输入微信号', trigger: 'blur' }],
      voice_part: [{ required: true, message: '请选择声部', trigger: 'change' }],
      tier: [{ required: true, message: '请选择梯队', trigger: 'change' }],
      department: [{ required: true, message: '请选择院系', trigger: 'change' }],
      class_name: [{ required: true, message: '请输入班级', trigger: 'blur' }],
      phone_number: [
        { required: true, message: '请输入手机号（中国大陆）', trigger: 'blur' },
        { pattern: /^\d{11}$/, message: '请输入中国大陆11位手机号', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }
      ],
      dorm: [{ required: true, message: '请输入宿舍号', trigger: 'blur' }],
      birthday: [{ required: true, message: '请选择生日', trigger: 'change' }],
      hometown_province: [{ required: true, message: '请选择省份/地区', trigger: 'change' }],
      hometown_city: [{ required: true, message: '请选择城市/地区', trigger: 'change' }],
      ethnicity: [{ required: true, message: '请选择民族', trigger: 'change' }],
      political_status: [{ required: true, message: '请选择政治面貌', trigger: 'change' }],
      political_affiliation: [{ required: true, message: '请选择党团关系所在', trigger: 'change' }],
      position: [],
      join_month: [{ required: true, message: '请选择入队年月', trigger: 'change' }],
      graduate_month: [
        { required: true, message: '请选择预计毕业时间', trigger: 'change' },
        { pattern: /^\d{4}-(0[1-9]|1[0-2])$/, message: '请输入YYYY-MM格式', trigger: 'blur' }
      ],
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
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
      ],
      new_password_confirm: [
        { required: true, message: '请确认新密码', trigger: 'blur' },
        {
          validator: (_rule, value, callback) => {
            if (value !== formData.new_password) {
              callback(new Error('两次输入的密码不一致'))
              return
            }
            callback()
          },
          trigger: 'blur'
        }
      ]
    }

    const initUserInfo = async () => {
      const user = store.getters['auth/user']
      if (user) {
        formData.user_id = user.user_id || ''
        formData.name = user.name || ''
      }
      // 设置默认入队年月为当前年月（后续若后端有数据将被覆盖）
      const now = new Date()
      formData.join_month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

      try {
        loading.value = true
        const resp = await getProfile()
        const profile = (resp && resp.data) || {}
        const member = profile.member || {}

        // 解析籍贯信息并填充
        const hometown = member.hometown || ''
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
          // 基本与联系信息
          wechat_id: member.wechat_id || formData.wechat_id,
          gender: member.gender || formData.gender,
          voice_part: member.voice_part || formData.voice_part,
          department: member.department || formData.department,
          department_other: member.department_other || '',
          class_name: member.class_name || '',
          phone_number: member.phone_number || '',
          email: member.email || '',
          dorm: member.dorm || '',
          birthday: member.birthday || '',
          // 籍贯联动字段
          hometown_province,
          hometown_city,
          hometown,
          // 其他信息
          ethnicity: member.ethnicity || '',
          political_status: member.political_status || '',
          political_affiliation: member.political_affiliation || '',
          is_specialty: !!member.is_specialty,
          is_centralized: !!member.is_centralized,
          position: member.position || '',
          join_month: member.join_month || formData.join_month,
          graduate_month: member.graduate_month || '',
          portfolio: member.portfolio || ''
        })

        // 更新合成后的籍贯，确保一致
        updateHometown()

        // 设置梯队，若后端为空则使用已有默认值
        const memberTier = member.tier
        formData.tier = memberTier ? memberTier : formData.tier || '二队'
      } catch (_e) {
        formData.tier = formData.tier || '二队'
      } finally {
        loading.value = false
      }
    }

    const handleSubmit = async () => {
      if (!formRef.value) {
        return
      }

      // 表单验证 - Element Plus validate() 失败时会抛出异常
      try {
        await formRef.value.validate()
      } catch (_validationError) {
        // 表单验证失败，Element Plus 会自动在字段旁显示错误提示
        notify.error('请检查表单填写是否完整')
        return
      }

      // 表单验证通过，开始提交
      try {
        submitting.value = true

        // 确保籍贯信息是最新的
        updateHometown()

        // 提交数据
        const submitData = {
          // 个人信息
          name: formData.name,
          gender: formData.gender,
          wechat_id: formData.wechat_id,
          voice_part: formData.voice_part,
          tier: formData.tier,
          department: formData.department,
          class_name: formData.class_name,
          phone_number: formData.phone_number,
          email: formData.email,
          dorm: formData.dorm,
          birthday: formData.birthday,
          hometown: formData.hometown,
          ethnicity: formData.ethnicity,
          political_status: formData.political_status,
          political_affiliation: formData.political_affiliation,
          is_specialty: formData.is_specialty,
          is_centralized: formData.is_centralized,
          position: formData.position,
          join_month: formData.join_month,
          graduate_month: formData.graduate_month,
          portfolio: formData.portfolio,
          // 密码修改
          new_password: formData.new_password,
          new_password_confirm: formData.new_password_confirm
        }

        // 只在选择"其他"院系时才包含department_other
        if (formData.department === '其他') {
          submitData.department_other = formData.department_other
        }

        await updateFirstLoginProfile(submitData)

        notify.success('信息设置完成，欢迎使用TaCOS！')

        // 更新用户信息
        await store.dispatch('auth/getUserInfo')

        // 跳转到主页
        router.push('/dashboard')
      } catch (error) {
        console.error('First login setup error:', error)
        const resp = error && error.response
        const data = resp && resp.data
        let message = '设置失败，请重试'
        if (data && typeof data === 'object' && !data.message) {
          // DRF校验错误
          const details = Object.entries(data)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join('; ') : String(v)}`)
            .join(' | ')
          if (details) {
            message = details
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
      // 检查是否已登录
      if (!store.getters['auth/isLoggedIn']) {
        router.push('/login')
        return
      }
      initUserInfo()
    })

    return {
      formRef,
      loading,
      submitting,
      formData,
      formRules,
      DEPARTMENTS,
      ETHNICITY_OPTIONS,
      POLITICAL_STATUS_OPTIONS,
      POLITICAL_AFFILIATION_OPTIONS,
      PROVINCES,
      CITIES,
      availableCities,
      handleSubmit
    }
  }
}
</script>

<style lang="scss" scoped>
.first-login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #6a2c86 0%, #9a56b5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.first-login-container {
  width: 100%;
  max-width: 1000px;

  .header {
    text-align: center;
    margin-bottom: 30px;
    color: white;

    .title {
      font-size: 2.5rem;
      font-weight: bold;
      margin-bottom: 10px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }

    .subtitle {
      font-size: 1.1rem;
      opacity: 0.9;
    }
  }
}

.el-card {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);

  :deep(.el-card__body) {
    padding: 40px;
  }
}

.form-section {
  margin-bottom: 40px;

  &:last-child {
    margin-bottom: 0;
  }

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: #303133;
    border-bottom: 2px solid #6a2c86;
    padding-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;

    .el-icon {
      color: #6a2c86;
    }
  }
}

.form-actions {
  text-align: center;
  margin-top: 40px;

  .el-button {
    padding: 12px 40px;
    font-size: 1.1rem;
    border-radius: 8px;
    background: linear-gradient(135deg, #6a2c86 0%, #9a56b5 100%);
    border: none;

    &:hover {
      background: linear-gradient(135deg, #5a1f73 0%, #8a469f 100%);
    }
  }
}

.el-form-item {
  margin-bottom: 20px;
}

.el-input,
.el-select,
.el-date-picker {
  :deep(.el-input__wrapper) {
    border-radius: 8px;
  }
}

@media (max-width: 768px) {
  .first-login-container {
    max-width: 600px;

    .header .title {
      font-size: 2rem;
    }
  }

  .el-card :deep(.el-card__body) {
    padding: 20px;
  }

  .el-col {
    width: 100% !important;
  }
}

// 全局样式，用于下拉框宽度
:deep(.wide-select-dropdown) {
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
