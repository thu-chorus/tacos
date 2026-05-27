<template>
  <div class="page-container">
    <div class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 5px"></div>

        <div class="profile-header">
          <div class="avatar">{{ initials }}</div>
          <div class="meta">
            <div class="name">{{ memberInfo.name || '未命名' }}</div>
            <div class="tags">
              <el-tag v-if="isAdmin" type="info">{{ memberInfo.user_id }}</el-tag>
              <el-tag :type="getVoicePartType(memberInfo.voice_part)">{{
                memberInfo.voice_part
              }}</el-tag>
              <el-tag :type="memberInfo.tier === '一队' ? 'danger' : 'primary'">{{
                memberInfo.tier
              }}</el-tag>
            </div>
            <div class="signature-box">
              <div class="signature-title">个性签名</div>
              <div class="signature-content">
                {{ memberInfo.portfolio || '这个人很低调，还没有填写签名。' }}
              </div>
            </div>
            <div
              v-if="Array.isArray(memberInfo.titles) && memberInfo.titles.length"
              class="titles-block"
            >
              <div class="titles-title">获得称号</div>
              <div class="titles">
                <TitleBadge
                  v-for="t in memberInfo.titles"
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
          <h3>队员信息</h3>
          <div class="actions">
            <button v-if="isAdmin" class="btn-modern primary sm-btn" @click="handleEdit">
              编辑
            </button>
          </div>
        </div>
        <div class="info-grid">
          <div v-if="memberInfo.wechat_id" class="info-item">
            <div class="label">微信号</div>
            <div class="value">{{ memberInfo.wechat_id }}</div>
          </div>
          <div v-if="memberInfo.gender" class="info-item">
            <div class="label">性别</div>
            <div class="value">{{ memberInfo.gender }}</div>
          </div>
          <div v-if="memberInfo.department || memberInfo.department_other" class="info-item">
            <div class="label">院系</div>
            <div class="value">
              <span v-if="memberInfo.department === '其他'">{{
                memberInfo.department_other || '其他'
              }}</span>
              <span v-else>{{ memberInfo.department }}</span>
            </div>
          </div>
          <div v-if="memberInfo.class_name" class="info-item">
            <div class="label">班级</div>
            <div class="value">{{ memberInfo.class_name }}</div>
          </div>
          <div v-if="memberInfo.join_month" class="info-item">
            <div class="label">入队年月</div>
            <div class="value">{{ memberInfo.join_month }}</div>
          </div>
          <div v-if="memberInfo.graduate_month" class="info-item">
            <div class="label">预计毕业时间</div>
            <div class="value">{{ memberInfo.graduate_month }}</div>
          </div>
          <div v-if="memberInfo.phone_number" class="info-item">
            <div class="label">手机号</div>
            <div class="value">{{ memberInfo.phone_number }}</div>
          </div>
          <div v-if="memberInfo.email" class="info-item">
            <div class="label">邮箱</div>
            <div class="value">{{ memberInfo.email }}</div>
          </div>
          <div v-if="memberInfo.dorm" class="info-item">
            <div class="label">宿舍</div>
            <div class="value">{{ memberInfo.dorm }}</div>
          </div>
          <div v-if="memberInfo.birthday" class="info-item">
            <div class="label">生日</div>
            <div class="value">{{ formatBirthday(memberInfo.birthday) }}</div>
          </div>
          <div v-if="memberInfo.hometown" class="info-item">
            <div class="label">籍贯</div>
            <div class="value">{{ memberInfo.hometown }}</div>
          </div>
          <div v-if="memberInfo.ethnicity" class="info-item">
            <div class="label">民族</div>
            <div class="value">{{ memberInfo.ethnicity }}</div>
          </div>
          <div v-if="memberInfo.political_status" class="info-item">
            <div class="label">政治面貌</div>
            <div class="value">{{ memberInfo.political_status }}</div>
          </div>
          <div v-if="memberInfo.political_affiliation" class="info-item">
            <div class="label">党团关系所在</div>
            <div class="value">{{ memberInfo.political_affiliation }}</div>
          </div>
          <div v-if="memberInfo.position" class="info-item">
            <div class="label">职务</div>
            <div class="value">{{ memberInfo.position }}</div>
          </div>
          <div
            v-if="memberInfo.is_specialty === true || memberInfo.is_specialty === false"
            class="info-item"
          >
            <div class="label">特长生</div>
            <div class="value">{{ memberInfo.is_specialty ? '是' : '否' }}</div>
          </div>
          <div
            v-if="memberInfo.is_centralized === true || memberInfo.is_centralized === false"
            class="info-item"
          >
            <div class="label">集中班</div>
            <div class="value">{{ memberInfo.is_centralized ? '是' : '否' }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="alumniProfile" class="card alumni-window-card">
      <div class="card-content" style="padding: 10px 15px">
        <div class="header alumni-window-header">
          <div class="alumni-window-title">
            <h3>校友窗口</h3>
            <el-tag v-if="alumniProfile.allow_contact === false" type="info" size="small">
              暂不开放联系
            </el-tag>
          </div>
        </div>
        <div class="alumni-window-summary">
          <div class="alumni-summary-item primary">
            <div class="summary-label">毕业时间</div>
            <div class="summary-value">{{ alumniProfile.graduation_month }}</div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">当前城市</div>
            <div class="summary-value">{{ displayAlumniValue(alumniProfile.current_city) }}</div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">行业</div>
            <div class="summary-value">{{ displayAlumniValue(alumniProfile.industry) }}</div>
          </div>
          <div class="alumni-summary-item">
            <div class="summary-label">公司 / 职位</div>
            <div class="summary-value">{{ displayAlumniValue(alumniCompanyTitle) }}</div>
          </div>
        </div>
        <div v-if="alumniProfile.bio" class="signature-box">
          <div class="signature-title">个人简介</div>
          <div class="signature-content">{{ alumniProfile.bio }}</div>
        </div>
        <div v-if="alumniProfile.contact_note" class="signature-box">
          <div class="signature-title">联系备注</div>
          <div class="signature-content">{{ alumniProfile.contact_note }}</div>
        </div>
      </div>
    </div>

    <div v-if="isAdmin && hiddenFields.length > 0" class="card">
      <div class="card-content">
        <div class="header" style="margin-bottom: 8px">
          <h3>被隐藏的个人信息</h3>
          <el-tag type="warning" size="small">该队员已隐藏以下信息</el-tag>
        </div>
        <div class="hidden-info-grid">
          <div v-for="field in hiddenFields" :key="field" class="hidden-field-item">
            <div class="field-label">{{ getFieldDisplayName(field) }}</div>
            <div class="field-value">{{ getFieldValue(field) || '未填写' }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { getMemberDetail } from '@/api/personnel'
import TitleBadge from '@/components/common/TitleBadge.vue'

export default {
  name: 'MemberDetail',
  components: {
    TitleBadge
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

    const loading = ref(false)
    const memberInfo = ref({})
    const initials = computed(() => {
      const name = memberInfo.value?.name || ''
      return name ? name.substring(0, 1) : 'T'
    })

    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const alumniProfile = computed(() => memberInfo.value?.alumni_profile || null)
    const alumniCompanyTitle = computed(() => {
      const profile = alumniProfile.value || {}
      return [profile.company, profile.job_title].filter(Boolean).join(' / ')
    })

    const displayAlumniValue = value => {
      return value || '未填写'
    }

    // 可被隐藏的字段列表
    const hiddenFields = computed(() => {
      if (!memberInfo.value.hidden_fields || !Array.isArray(memberInfo.value.hidden_fields)) {
        return []
      }
      return memberInfo.value.hidden_fields
    })

    // 字段名到中文显示名的映射
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

    const getFieldDisplayName = fieldName => {
      return fieldDisplayNames[fieldName] || fieldName
    }

    const getFieldValue = fieldName => {
      const value = memberInfo.value[fieldName]
      if (fieldName === 'is_specialty' || fieldName === 'is_centralized') {
        return value ? '是' : '否'
      }
      return value
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

    // 获取返回目标路径（不导航）
    const getBackDestination = () => {
      const ref = route.query && route.query.ref
      if (ref) {
        return typeof ref === 'string' ? ref : '/personnel/members'
      }
      return '/personnel/members'
    }

    const goBack = () => {
      router.push(getBackDestination())
    }

    const handleEdit = () => {
      // 传递详情页的返回目标给编辑页，这样编辑页保存后返回详情页时，详情页仍保留原来的 ref
      const backDest = getBackDestination()
      router.push(`/personnel/members/${route.params.id}/edit?ref=${encodeURIComponent(backDest)}`)
    }

    const loadMemberDetail = async () => {
      loading.value = true
      try {
        const response = await getMemberDetail(route.params.id)
        memberInfo.value = response.data || {}
        // 设置分享页面信息
        if (memberInfo.value.name) {
          store.dispatch('common/setSharePageInfo', `队员「${memberInfo.value.name}」的主页`)
        }
      } catch (error) {
        console.error('Failed to load member detail:', error)
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadMemberDetail()
    })

    onUnmounted(() => {})

    return {
      loading,
      memberInfo,
      initials,
      isAdmin,
      alumniProfile,
      alumniCompanyTitle,
      displayAlumniValue,
      hiddenFields,
      getVoicePartType,
      getFieldDisplayName,
      getFieldValue,
      formatBirthday,
      goBack,
      handleEdit
    }
  }
}
</script>

<style lang="scss" scoped>
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
  margin-bottom: 12px;
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

@media (max-width: 768px) {
  .info-grid,
  .hidden-info-grid,
  .alumni-window-summary {
    grid-template-columns: 1fr;
  }
  .alumni-window-header {
    flex-direction: column;
  }
}
</style>
