<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="profile-header">
          <div class="avatar">{{ initials }}</div>
          <div class="meta">
            <div class="name">{{ profileForm.name || '未命名' }}</div>
            <div class="tags">
              <el-tag type="info">{{ profileForm.user_id }}</el-tag>
              <el-tag v-if="profileForm.role" type="success">{{ roleDisplayName }}</el-tag>
              <el-tag
                v-if="profileForm.voice_part"
                :type="getVoicePartType(profileForm.voice_part)"
                >{{ profileForm.voice_part || 'Other' }}</el-tag
              >
              <el-tag
                v-if="profileForm.tier"
                :type="profileForm.tier === '一队' ? 'danger' : 'primary'"
                >{{ profileForm.tier || '二队' }}</el-tag
              >
              <el-tag v-if="profileForm.status === 'ALUMNI'" type="warning">校友</el-tag>
            </div>
            <div class="signature-box">
              <div class="signature-title">个性签名</div>
              <div class="signature-content">
                {{ profileForm.portfolio || '这个人很低调，还没有填写签名。' }}
              </div>
            </div>
            <div
              v-if="Array.isArray(profileForm.titles) && profileForm.titles.length"
              class="titles-block"
            >
              <div class="titles-title">获得称号</div>
              <div class="titles">
                <TitleBadge
                  v-for="t in profileForm.titles"
                  :key="t.id + '-' + t.awarded_at"
                  :title="t"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-content" style="padding: 10px 15px">
        <div class="header" style="margin-bottom: 20px">
          <h3>个人信息</h3>
          <div class="actions">
            <button class="btn-modern primary sm-btn" @click="goEdit">
              {{ profileActionText }}
            </button>
          </div>
        </div>
        <div class="info-grid">
          <div v-if="profileForm.role" class="info-item">
            <div class="label">账号角色</div>
            <div class="value">{{ roleDisplayName }}</div>
          </div>
          <div v-if="!hasMemberProfile" class="info-item">
            <div class="label">成员档案</div>
            <div class="value">待完善</div>
          </div>
          <div v-if="profileForm.wechat_id" class="info-item">
            <div class="label">微信号</div>
            <div class="value">{{ profileForm.wechat_id }}</div>
          </div>
          <div v-if="profileForm.gender" class="info-item">
            <div class="label">性别</div>
            <div class="value">{{ profileForm.gender }}</div>
          </div>
          <div v-if="profileForm.department || profileForm.department_other" class="info-item">
            <div class="label">院系</div>
            <div class="value">
              <span v-if="profileForm.department === '其他'">{{
                profileForm.department_other || '其他'
              }}</span>
              <span v-else>{{ profileForm.department }}</span>
            </div>
          </div>
          <div v-if="profileForm.class_name" class="info-item">
            <div class="label">班级</div>
            <div class="value">{{ profileForm.class_name }}</div>
          </div>
          <div v-if="profileForm.join_month" class="info-item">
            <div class="label">入队年月</div>
            <div class="value">{{ profileForm.join_month }}</div>
          </div>
          <div v-if="profileForm.graduate_month" class="info-item">
            <div class="label">预计毕业时间</div>
            <div class="value">{{ profileForm.graduate_month }}</div>
          </div>
          <div v-if="profileForm.phone_number" class="info-item">
            <div class="label">手机号</div>
            <div class="value">{{ profileForm.phone_number }}</div>
          </div>
          <div v-if="profileForm.email" class="info-item">
            <div class="label">邮箱</div>
            <div class="value">{{ profileForm.email }}</div>
          </div>
          <div v-if="profileForm.dorm" class="info-item">
            <div class="label">宿舍</div>
            <div class="value">{{ profileForm.dorm }}</div>
          </div>
          <div v-if="profileForm.birthday" class="info-item">
            <div class="label">生日</div>
            <div class="value">{{ formatBirthday(profileForm.birthday) }}</div>
          </div>
          <div v-if="profileForm.hometown" class="info-item">
            <div class="label">籍贯</div>
            <div class="value">{{ profileForm.hometown }}</div>
          </div>
          <div v-if="profileForm.ethnicity" class="info-item">
            <div class="label">民族</div>
            <div class="value">{{ profileForm.ethnicity }}</div>
          </div>
          <div v-if="profileForm.political_status" class="info-item">
            <div class="label">政治面貌</div>
            <div class="value">{{ profileForm.political_status }}</div>
          </div>
          <div v-if="profileForm.political_affiliation" class="info-item">
            <div class="label">党团关系所在</div>
            <div class="value">{{ profileForm.political_affiliation }}</div>
          </div>
          <div v-if="profileForm.position" class="info-item">
            <div class="label">职务</div>
            <div class="value">{{ profileForm.position }}</div>
          </div>
          <div v-if="profileForm.is_specialty !== undefined" class="info-item">
            <div class="label">特长生</div>
            <div class="value">{{ profileForm.is_specialty ? '是' : '否' }}</div>
          </div>
          <div v-if="profileForm.is_centralized !== undefined" class="info-item">
            <div class="label">集中班</div>
            <div class="value">{{ profileForm.is_centralized ? '是' : '否' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isAlumni" class="card alumni-window-card">
      <div class="card-content" style="padding: 10px 15px">
        <div class="header alumni-window-header">
          <div class="alumni-window-title">
            <h3>校友窗口</h3>
            <el-tag :type="alumniContactStatusType" size="small">
              {{ alumniContactStatusText }}
            </el-tag>
          </div>
          <div class="actions">
            <button
              class="btn-modern primary sm-btn"
              type="button"
              :disabled="savingAlumniContact"
              @click="openAlumniDialog"
            >
              编辑校友信息
            </button>
          </div>
        </div>

        <div class="alumni-window-summary">
          <div class="alumni-summary-item primary">
            <div class="summary-label">毕业时间</div>
            <div class="summary-value">
              {{ displayAlumniValue(alumniContact.graduation_month) }}
            </div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">当前城市</div>
            <div class="summary-value">{{ displayAlumniValue(alumniContact.current_city) }}</div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">行业</div>
            <div class="summary-value">{{ displayAlumniValue(alumniContact.industry) }}</div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">公司 / 职位</div>
            <div class="summary-value">{{ displayAlumniValue(alumniCompanyTitle) }}</div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="alumniDialog.visible" title="编辑校友信息" :width="dialogWidth">
      <el-form
        ref="alumniFormRef"
        :model="alumniDraft"
        :rules="alumniRules"
        label-width="88px"
        class="alumni-contact-form"
      >
        <div class="alumni-form-grid">
          <div class="alumni-form-field">
            <el-form-item label="毕业时间" prop="graduation_month">
              <el-date-picker
                v-model="alumniDraft.graduation_month"
                type="month"
                placeholder="请选择"
                format="YYYY-MM"
                value-format="YYYY-MM"
                class="field-control"
              />
            </el-form-item>
          </div>
          <div class="alumni-form-field">
            <el-form-item label="允许联系">
              <el-switch
                v-model="alumniDraft.allow_contact"
                active-text="开放"
                inactive-text="关闭"
              />
            </el-form-item>
          </div>
          <div class="alumni-form-field">
            <el-form-item label="当前城市">
              <el-input v-model="alumniDraft.current_city" placeholder="可选" />
            </el-form-item>
          </div>
          <div class="alumni-form-field">
            <el-form-item label="行业">
              <el-input v-model="alumniDraft.industry" placeholder="可选" />
            </el-form-item>
          </div>
          <div class="alumni-form-field">
            <el-form-item label="公司">
              <el-input v-model="alumniDraft.company" placeholder="可选" />
            </el-form-item>
          </div>
          <div class="alumni-form-field">
            <el-form-item label="职位">
              <el-input v-model="alumniDraft.job_title" placeholder="可选" />
            </el-form-item>
          </div>
        </div>
        <el-form-item label="个人简介">
          <el-input
            v-model="alumniDraft.bio"
            type="textarea"
            :rows="3"
            placeholder="可填写当前方向、背景或希望公开的信息"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="alumniDraft.contact_note"
            type="textarea"
            :rows="3"
            placeholder="可填写偏好的联系渠道、时间段或说明"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          type="button"
          style="margin-right: 10px"
          @click="alumniDialog.visible = false"
        >
          取消
        </button>
        <button
          class="btn-modern primary sm-btn"
          type="button"
          :disabled="savingAlumniContact"
          @click="handleSaveAlumniContact"
        >
          保存
        </button>
      </template>
    </el-dialog>

    <div v-if="hasMemberProfile && hiddenFields.length > 0" class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 8px">
          <h3>已隐藏的信息</h3>
          <div class="actions">
            <button class="btn-modern primary sm-btn" @click="openPrivacyDialog">隐私设置</button>
          </div>
        </div>
        <div class="hidden-info-grid">
          <div v-for="field in hiddenFields" :key="field" class="hidden-field-item">
            <div class="field-label">{{ getFieldDisplayName(field) }}</div>
            <div class="field-value">{{ getFieldValue(field) || '未填写' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-grid cards-row">
      <div class="card card-clickable flat" @click="openPasswordDialog">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-lock />
          </div>
          <div class="stat-info">
            <div class="stat-number">修改个人密码</div>
            <div class="stat-label">点击修改密码</div>
          </div>
        </div>
      </div>
      <div
        v-if="hasMemberProfile && hiddenFields.length === 0"
        class="card card-clickable flat"
        @click="openPrivacyDialog"
      >
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-eye-off />
          </div>
          <div class="stat-info">
            <div class="stat-number">隐私设置</div>
            <div class="stat-label">管理隐藏信息</div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="privacyDialog.visible" title="隐私设置" :width="dialogWidth">
      <div class="privacy-content">
        <div class="privacy-description">
          <p>
            选择你想要隐藏的个人信息字段。普通队员无法看到你主动隐藏的信息，被隐藏的信息只有在需要时才能由管理员读取。
          </p>
        </div>
        <div class="privacy-fields">
          <div
            v-for="field in privacyFieldOptions"
            :key="field.value"
            class="privacy-field-item"
            :class="{ active: tempHiddenFields.includes(field.value) }"
            @click="togglePrivacyField(field.value)"
          >
            <div class="privacy-checkbox">
              <svg
                v-if="tempHiddenFields.includes(field.value)"
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <span class="privacy-label">{{ field.label }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="privacyDialog.visible = false"
          style="margin-right: 10px"
        >
          取消
        </button>
        <button
          class="btn-modern primary sm-btn"
          :loading="savingPrivacy"
          @click="handleSavePrivacy"
        >
          保存
        </button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialog.visible" title="修改密码" :width="dialogWidth">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordRef" label-width="100px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="new_password_confirm">
          <el-input v-model="passwordForm.new_password_confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="passwordDialog.visible = false"
          style="margin-right: 10px"
        >
          取消
        </button>
        <button
          class="btn-modern primary sm-btn"
          :loading="savingPassword"
          @click="handleChangePassword"
        >
          提交
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { notify } from '@/utils/notify'
import { getProfile, changePassword, updateProfile } from '@/api/auth'
import { getMyAlumniProfile, updateMyAlumniProfile } from '@/api/personnel'
import { Lock as LucideLock, EyeOff as LucideEyeOff } from 'lucide-vue-next'
import TitleBadge from '@/components/common/TitleBadge.vue'

export default {
  name: 'Profile',
  components: {
    'i-lucide-lock': LucideLock,
    'i-lucide-eye-off': LucideEyeOff,
    TitleBadge
  },
  setup() {
    const router = useRouter()
    const passwordRef = ref()

    const profileForm = reactive({
      user_id: '',
      role: '',
      name: '',
      wechat_id: '',
      gender: '',
      voice_part: '',
      department: '',
      department_other: '',
      class_name: '',
      phone_number: '',
      email: '',
      dorm: '',
      birthday: '',
      hometown: '',
      ethnicity: '',
      political_status: '',
      political_affiliation: '',
      is_specialty: false,
      is_centralized: false,
      position: '',
      tier: '',
      status: 'ACTIVE',
      join_month: '',
      graduate_month: '',
      portfolio: '',
      hidden_fields: [],
      titles: []
    })

    const memberId = ref(null)
    const hasMemberProfile = computed(() => !!memberId.value)
    const roleDisplayName = computed(() => {
      const roleMap = {
        SuperAdmin: '超级管理员',
        Admin: '管理员',
        Member: '队员'
      }
      return roleMap[profileForm.role] || profileForm.role || '未知'
    })
    const profileActionText = computed(() =>
      hasMemberProfile.value ? '编辑个人信息' : '完善个人信息'
    )
    const alumniContact = reactive({
      current_city: '',
      industry: '',
      company: '',
      job_title: '',
      graduation_month: '',
      bio: '',
      contact_note: '',
      allow_contact: true
    })
    const alumniDraft = reactive({
      current_city: '',
      industry: '',
      company: '',
      job_title: '',
      graduation_month: '',
      bio: '',
      contact_note: '',
      allow_contact: true
    })
    const alumniFormRef = ref()
    const alumniDialog = ref({ visible: false })
    const alumniRules = {
      graduation_month: [{ required: true, message: '请选择毕业时间', trigger: 'change' }]
    }
    const savingAlumniContact = ref(false)
    const isAlumni = computed(() => profileForm.status === 'ALUMNI')
    const alumniContactStatusType = computed(() =>
      alumniContact.allow_contact ? 'success' : 'info'
    )
    const alumniContactStatusText = computed(() =>
      alumniContact.allow_contact ? '开放联系' : '暂不开放联系'
    )
    const alumniCompanyTitle = computed(() => {
      const parts = [alumniContact.company, alumniContact.job_title].filter(Boolean)
      return parts.join(' / ')
    })

    const displayAlumniValue = value => {
      return value || '未填写'
    }

    const copyAlumniFields = (target, source = {}) => {
      Object.assign(target, {
        current_city: source.current_city || '',
        industry: source.industry || '',
        company: source.company || '',
        job_title: source.job_title || '',
        graduation_month: source.graduation_month || '',
        bio: source.bio || '',
        contact_note: source.contact_note || '',
        allow_contact: source.allow_contact !== false
      })
    }

    const initials = computed(() => {
      const name = profileForm.name || ''
      return name ? name.substring(0, 1) : 'T'
    })

    const hiddenFields = computed(() => {
      if (!profileForm.hidden_fields || !Array.isArray(profileForm.hidden_fields)) {
        return []
      }
      return profileForm.hidden_fields
    })

    const fieldDisplayNames = {
      gender: '性别',
      phone_number: '手机号',
      email: '邮箱',
      dorm: '宿舍',
      hometown: '籍贯',
      ethnicity: '民族',
      political_status: '政治面貌',
      political_affiliation: '党团关系所在',
      is_specialty: '特长生',
      is_centralized: '集中班',
      graduate_month: '预计毕业时间',
      birthday: '生日'
    }

    const getFieldDisplayName = fieldName => {
      return fieldDisplayNames[fieldName] || fieldName
    }

    const getFieldValue = fieldName => {
      const value = profileForm[fieldName]
      if (fieldName === 'is_specialty' || fieldName === 'is_centralized') {
        return value ? '是' : '否'
      }
      if (fieldName === 'birthday' && value) {
        return formatBirthday(value)
      }
      return value
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

    const formatBirthday = birthday => {
      if (!birthday) {
        return ''
      }
      try {
        const { formatDate } = require('@/utils/format')
        return formatDate(birthday, 'YYYY年M月D日')
      } catch {
        return birthday
      }
    }

    const passwordForm = reactive({
      old_password: '',
      new_password: '',
      new_password_confirm: ''
    })

    const passwordRules = {
      old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
      ],
      new_password_confirm: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== passwordForm.new_password) {
              callback(new Error('两次输入的密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }

    const savingPassword = ref(false)
    const savingPrivacy = ref(false)
    const privacyDialog = ref({ visible: false })
    const passwordDialog = ref({ visible: false })

    // 临时存储隐私设置的副本，只有保存时才应用到 profileForm
    const tempHiddenFields = ref([])

    const privacyFieldOptions = [
      { label: '性别', value: 'gender' },
      { label: '手机号', value: 'phone_number' },
      { label: '邮箱', value: 'email' },
      { label: '宿舍', value: 'dorm' },
      { label: '生日', value: 'birthday' },
      { label: '籍贯', value: 'hometown' },
      { label: '民族', value: 'ethnicity' },
      { label: '政治面貌', value: 'political_status' },
      { label: '党团关系所在', value: 'political_affiliation' },
      { label: '是否为特长生', value: 'is_specialty' },
      { label: '是否为集中班', value: 'is_centralized' },
      { label: '预计毕业时间', value: 'graduate_month' }
    ]

    const togglePrivacyField = fieldValue => {
      const index = tempHiddenFields.value.indexOf(fieldValue)
      if (index > -1) {
        tempHiddenFields.value.splice(index, 1)
      } else {
        tempHiddenFields.value.push(fieldValue)
      }
    }

    const loadProfile = async () => {
      const res = await getProfile()
      const user = res.data?.user || {}
      const member = res.data?.member || {}

      profileForm.user_id = user.user_id || ''
      profileForm.role = user.role || ''
      // 使用 member.name，因为队员信息中的姓名是可编辑的
      profileForm.name = member.name || user.name || ''

      memberId.value = member.id || null

      Object.assign(profileForm, {
        wechat_id: member.wechat_id || '',
        gender: member.gender || '',
        voice_part: member.voice_part || '',
        department: member.department || '',
        department_other: member.department_other || '',
        class_name: member.class_name || '',
        phone_number: member.phone_number || '',
        email: member.email || '',
        dorm: member.dorm || '',
        birthday: member.birthday || '',
        hometown: member.hometown || '',
        ethnicity: member.ethnicity || '',
        political_status: member.political_status || '',
        political_affiliation: member.political_affiliation || '',
        is_specialty: !!member.is_specialty,
        is_centralized: !!member.is_centralized,
        position: member.position || '',
        join_month: member.join_month || '',
        graduate_month: member.graduate_month || '',
        tier: member.tier || '',
        status: member.status || '',
        portfolio: member.portfolio || '',
        hidden_fields: Array.isArray(member.hidden_fields) ? member.hidden_fields : [],
        titles: Array.isArray(member.titles) ? member.titles : []
      })
      if (member.status === 'ALUMNI') {
        await loadAlumniContact()
      }
    }

    const loadAlumniContact = async () => {
      try {
        const res = await getMyAlumniProfile()
        const data = res.data || {}
        copyAlumniFields(alumniContact, data)
        copyAlumniFields(alumniDraft, data)
      } catch (e) {
        notify.error('加载校友信息失败')
      }
    }

    const goEdit = () => {
      if (hasMemberProfile.value) {
        // 从 Profile 进入编辑页，编辑保存后应该返回 Profile
        router.push(
          `/personnel/members/${memberId.value}/edit?ref=${encodeURIComponent('/profile')}`
        )
      } else {
        notify.warning('当前账号还没有成员档案，请先完善个人信息')
        router.push('/first-login')
      }
    }

    const openPrivacyDialog = () => {
      if (!hasMemberProfile.value) {
        notify.warning('当前账号还没有成员档案，请先完善个人信息')
        router.push('/first-login')
        return
      }
      // 打开对话框时，将当前的隐私设置复制到临时变量
      tempHiddenFields.value = [...profileForm.hidden_fields]
      privacyDialog.value.visible = true
    }

    const openPasswordDialog = () => {
      passwordForm.old_password = ''
      passwordForm.new_password = ''
      passwordForm.new_password_confirm = ''
      passwordDialog.value.visible = true
    }

    const openAlumniDialog = () => {
      copyAlumniFields(alumniDraft, alumniContact)
      alumniDialog.value.visible = true
      nextTick(() => {
        alumniFormRef.value?.clearValidate()
      })
    }

    const handleSavePrivacy = async () => {
      try {
        savingPrivacy.value = true
        // 保存时才将临时变量的值应用到 profileForm
        profileForm.hidden_fields = [...tempHiddenFields.value]
        await updateProfile({ hidden_fields: profileForm.hidden_fields })
        notify.success('隐私设置已保存')
        privacyDialog.value.visible = false
        await loadProfile()
      } catch (e) {
        notify.error('保存隐私设置失败')
      } finally {
        savingPrivacy.value = false
      }
    }

    const handleSaveAlumniContact = async () => {
      try {
        if (alumniFormRef.value) {
          const valid = await alumniFormRef.value.validate().catch(() => false)
          if (!valid) {
            return
          }
        }
        const graduationMonth = String(alumniDraft.graduation_month || '').trim()
        if (!graduationMonth) {
          notify.warning('请填写毕业时间')
          return
        }
        savingAlumniContact.value = true
        await updateMyAlumniProfile({
          current_city: alumniDraft.current_city,
          industry: alumniDraft.industry,
          company: alumniDraft.company,
          job_title: alumniDraft.job_title,
          graduation_month: graduationMonth,
          bio: alumniDraft.bio,
          contact_note: alumniDraft.contact_note,
          allow_contact: alumniDraft.allow_contact
        })
        alumniDraft.graduation_month = graduationMonth
        copyAlumniFields(alumniContact, alumniDraft)
        alumniDialog.value.visible = false
        notify.success('校友信息已保存')
      } catch (e) {
        notify.error(e?.response?.data?.message || e?.message || '保存校友信息失败')
      } finally {
        savingAlumniContact.value = false
      }
    }

    const handleChangePassword = async () => {
      if (!passwordRef.value) {
        return
      }
      const valid = await passwordRef.value.validate()
      if (!valid) {
        return
      }
      try {
        savingPassword.value = true
        await changePassword({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
          new_password_confirm: passwordForm.new_password_confirm
        })
        notify.success('密码修改成功')
        passwordDialog.value.visible = false
        passwordForm.old_password = ''
        passwordForm.new_password = ''
        passwordForm.new_password_confirm = ''
      } catch (e) {
        notify.error('密码修改失败')
      } finally {
        savingPassword.value = false
      }
    }

    const dialogWidth = ref('520px')
    const computeDialogWidths = () => {
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
      loadProfile()
      computeDialogWidths()
      window.addEventListener('resize', computeDialogWidths, { passive: true })
    })

    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidths)
    })

    return {
      profileForm,
      alumniContact,
      alumniDraft,
      alumniFormRef,
      alumniDialog,
      alumniRules,
      isAlumni,
      alumniContactStatusType,
      alumniContactStatusText,
      alumniCompanyTitle,
      displayAlumniValue,
      hasMemberProfile,
      profileActionText,
      roleDisplayName,
      initials,
      hiddenFields,
      getFieldDisplayName,
      getFieldValue,
      getVoicePartType,
      formatBirthday,
      goEdit,
      passwordForm,
      passwordRules,
      passwordRef,
      savingPassword,
      savingPrivacy,
      savingAlumniContact,
      privacyDialog,
      passwordDialog,
      privacyFieldOptions,
      tempHiddenFields,
      togglePrivacyField,
      openPrivacyDialog,
      openPasswordDialog,
      openAlumniDialog,
      handleSavePrivacy,
      handleSaveAlumniContact,
      handleChangePassword,
      dialogWidth
    }
  }
}
</script>

<style lang="scss" scoped>
.page-container {
  padding: 20px;
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

.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 6px 0 4px;
}
.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
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
  margin: 0 0 2px 0;
}
.tags {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.signature-box {
  margin-top: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-left: 3px solid var(--el-color-primary);
  border-radius: 8px;
  background: var(--background);
}
.signature-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}
.signature-content {
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
}

.titles-block {
  margin-top: 12px;
}
.titles-title {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.titles {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.alumni-window-header {
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.alumni-window-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.alumni-window-title h3 {
  margin: 0;
}
.alumni-window-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}
.alumni-summary-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  min-height: 62px;
  background: #fafafa;
}
.alumni-summary-item.primary {
  border-color: rgba(154, 86, 181, 0.35);
  background: rgba(154, 86, 181, 0.06);
}
.summary-label {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  white-space: nowrap;
}
.summary-value {
  margin-top: 4px;
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.alumni-contact-form {
  max-width: 900px;
  padding: 0 20px;
}
.alumni-contact-form :deep(.el-form-item__label) {
  white-space: nowrap;
}
.alumni-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 16px;
}
.field-control {
  width: 100%;
}

.hidden-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.hidden-field-item {
  display: flex;
  flex-direction: column;
}
.hidden-field-item .field-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
  font-weight: 500;
}
.hidden-field-item .field-value {
  font-size: 14px;
  color: #595959;
  padding: 8px 12px;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  min-height: 20px;
  display: flex;
  align-items: center;
}

.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}
.card-content {
  padding: 10px 12px;
}

.cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.card.flat {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}
.card-clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}
.card-clickable:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.stat-content {
  display: flex;
  align-items: center;
}
.stat-info {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}
.stat-number {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}
.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
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
  padding: 4px 0px;
}
:deep(.el-dialog__footer) {
  padding: 10px 0px 0px 0px;
  border-top: 1px solid var(--border);
}

.privacy-content {
  padding: 0 20px;
}
.privacy-description {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--background);
  border-radius: 8px;
  border: 1px solid var(--border);
}
.privacy-description p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.6;
}
.privacy-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.privacy-field-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}
.privacy-field-item:hover {
  background: var(--background);
  border-color: var(--brand-500, #9a56b5);
}
.privacy-field-item.active {
  background: rgba(154, 86, 181, 0.05);
  border-color: var(--brand-500, #9a56b5);
}
.privacy-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
}
.privacy-field-item.active .privacy-checkbox {
  background: var(--brand-500, #9a56b5);
  border-color: var(--brand-500, #9a56b5);
  color: #fff;
}
.privacy-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}
.privacy-field-item.active .privacy-label {
  color: var(--brand-600, #8a46a5);
}

@media (max-width: 768px) {
  .info-grid,
  .hidden-info-grid,
  .alumni-window-summary,
  .alumni-form-grid {
    grid-template-columns: 1fr;
  }
  .alumni-window-header {
    align-items: stretch;
    flex-direction: column;
  }
  .cards-row {
    grid-template-columns: 1fr;
  }
  .privacy-fields {
    grid-template-columns: 1fr;
  }
}
</style>
