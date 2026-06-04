<template>
  <div class="checkin-share-page">
    <div class="checkin-share-container">
      <!-- 签到卡片 -->
      <div class="checkin-card">
        <div class="checkin-header">
          <div class="checkin-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <div class="checkin-title-section">
            <h2>签到分享</h2>
            <p class="checkin-subtitle">{{ eventName }}</p>
          </div>
        </div>

        <div class="checkin-body">
          <div class="checkin-info">
            <div class="info-row">
              <span class="info-label">签到名称</span>
              <span class="info-value">{{ sessionName || '签到' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">签到类型</span>
              <span class="info-value">{{ getCheckinTypeLabel(sessionType) }}</span>
            </div>
          </div>

          <!-- 签到表单 -->
          <div class="checkin-form">
            <div v-if="sessionType === 'PASSWORD'" class="form-item">
              <label class="form-label">签到口令</label>
              <input
                v-model="password"
                type="password"
                placeholder="请输入签到口令"
                class="input-modern"
              />
            </div>

            <div v-else-if="sessionType === 'LOCATION'" class="form-item">
              <p class="location-hint">需要授权定位以完成签到</p>
              <button class="btn-modern primary" @click="getLocation" :disabled="gettingLocation">
                <i-lucide-map-pin class="btn-icon" />
                <span>{{ gettingLocation ? '获取中...' : '获取当前位置' }}</span>
              </button>
              <div v-if="lat && lng" class="location-display">坐标：{{ lat }}, {{ lng }}</div>
            </div>

            <div v-else-if="sessionType === 'NONE'" class="form-item">
              <p class="none-hint">本次为无条件签到，点击下方按钮即可完成签到</p>
            </div>
          </div>
        </div>

        <div class="checkin-footer">
          <button class="btn-modern ghost" @click="goToEvent">
            <i-lucide-arrow-left class="btn-icon" />
            <span>返回活动</span>
          </button>
          <button
            class="btn-modern primary"
            @click="handleSubmit"
            :disabled="submitting || (sessionType === 'LOCATION' && !lat)"
          >
            <i-lucide-clipboard-check class="btn-icon" />
            <span>{{ submitting ? '提交中...' : '提交签到' }}</span>
          </button>
        </div>
      </div>
    </div>
    <SiteFooter dark fixed />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { submitCheckin, getCheckinStatus } from '@/api/events'
import { notify } from '@/utils/notify'
import SiteFooter from '@/components/common/SiteFooter.vue'

export default {
  name: 'CheckinShare',
  components: {
    SiteFooter
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()

    // 从URL参数获取签到信息
    const eventId = computed(() => route.params.id)
    const sessionId = computed(() => route.query.session)
    const sessionType = computed(() => route.query.type || 'NONE')
    const sessionName = computed(() => decodeURIComponent(route.query.name || '签到'))
    const eventName = computed(() => decodeURIComponent(route.query.event_name || '活动'))

    // 表单状态
    const password = ref('')
    const lat = ref(null)
    const lng = ref(null)
    const gettingLocation = ref(false)
    const submitting = ref(false)

    const getCheckinTypeLabel = type => {
      const labels = {
        NONE: '无条件签到',
        PASSWORD: '口令签到',
        LOCATION: '地点签到'
      }
      return labels[type] || '签到'
    }

    const handleGeolocationError = error => {
      const code = error && error.code
      if (code === 1) {
        notify.error('已拒绝定位权限，请在浏览器设置中允许定位')
      } else if (code === 2) {
        notify.error('无法获取位置信息，请稍后重试')
      } else if (code === 3) {
        notify.error('获取位置超时，请再次尝试')
      } else {
        notify.error('获取位置失败，请检查网络与权限设置')
      }
    }

    const getLocation = () => {
      if (!('geolocation' in navigator)) {
        notify.error('当前浏览器不支持定位')
        return
      }
      if (!window.isSecureContext) {
        notify.warning('定位需在 HTTPS 或 localhost 环境下使用')
      }

      gettingLocation.value = true
      const options = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }

      navigator.geolocation.getCurrentPosition(
        pos => {
          lat.value = Number(pos.coords.latitude.toFixed(6))
          lng.value = Number(pos.coords.longitude.toFixed(6))
          gettingLocation.value = false
          notify.success('已获取当前位置')
        },
        error => {
          gettingLocation.value = false
          handleGeolocationError(error)
        },
        options
      )
    }

    const goToEvent = () => {
      router.push(`/events/${eventId.value}`)
    }

    const handleSubmit = async () => {
      // 检查用户是否登录
      const isLoggedIn = store.getters['auth/isLoggedIn']
      if (!isLoggedIn) {
        notify.error('请先登录')
        router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
        return
      }

      submitting.value = true

      try {
        // 首先检查签到状态，验证签到是否有效
        const statusRes = await getCheckinStatus(eventId.value)
        const status = statusRes.data || {}

        // 检查签到是否正在进行
        if (!status.active) {
          notify.error('当前没有正在进行的签到')
          goToEvent()
          return
        }

        // 检查签到ID是否匹配（转为字符串比较，避免类型不一致）
        if (String(status.session?.id) !== String(sessionId.value)) {
          notify.error('签到信息不匹配，可能签到已结束或已更换')
          goToEvent()
          return
        }

        // 构建提交数据
        const payload = {}
        if (sessionType.value === 'PASSWORD') {
          if (!password.value) {
            notify.error('请输入签到口令')
            submitting.value = false
            return
          }
          payload.password = password.value
        }
        if (sessionType.value === 'LOCATION') {
          if (!lat.value || !lng.value) {
            notify.error('请先获取当前位置')
            submitting.value = false
            return
          }
          payload.lat = lat.value
          payload.lng = lng.value
        }

        // 提交签到
        const result = await submitCheckin(eventId.value, payload)

        // 检查是否是重复签到
        if (result?.data?.duplicate || result?.data?.data?.duplicate) {
          notify.warning('您已签到过，无需重复签到')
          goToEvent()
          return
        }

        notify.success('签到成功！')
        goToEvent()
      } catch (error) {
        console.error('Checkin error:', error)

        const resp = error?.response
        const data = resp?.data
        const httpStatus = resp?.status

        // 处理各种错误情况
        if (httpStatus === 401) {
          notify.error('请先登录')
          router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
          return
        }

        if (httpStatus === 403) {
          // 权限不足：可能不是活动成员，或位置不在范围内
          const message =
            data?.message || data?.detail || '您没有权限参与此签到，可能您不是该活动的成员'
          notify.error(message)
          goToEvent()
          return
        }

        if (httpStatus === 404) {
          // 活动或签到不存在
          const message = data?.message || '活动或签到不存在'
          notify.error(message)
          router.push('/events')
          return
        }

        if (httpStatus === 422) {
          // 验证错误：密码错误、坐标缺失等
          const message = data?.message || data?.detail || '签到验证失败'
          notify.error(message)
          // 不跳转，让用户可以重新输入
          return
        }

        if (httpStatus === 400) {
          // 业务错误
          let message = '签到失败'
          if (data?.message) {
            message = data.message
          } else if (data?.detail) {
            message = data.detail
          } else if (typeof data === 'string') {
            message = data
          }

          // 检查是否是重复签到
          if (message.includes('已签到') || message.includes('重复')) {
            notify.warning('您已经签到过了')
          } else {
            notify.error(message)
          }
          goToEvent()
          return
        }

        // 其他错误
        notify.error('签到失败，请重试')
        goToEvent()
      } finally {
        submitting.value = false
      }
    }

    // 检查URL参数是否完整
    onMounted(() => {
      if (!sessionId.value) {
        notify.error('签到链接无效')
        router.push('/events')
      }
    })

    return {
      eventId,
      sessionId,
      sessionType,
      sessionName,
      eventName,
      password,
      lat,
      lng,
      gettingLocation,
      submitting,
      getCheckinTypeLabel,
      getLocation,
      goToEvent,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.checkin-share-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #6a2c86 0%, #9a56b5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.checkin-share-container {
  width: 100%;
  max-width: 420px;
}

.checkin-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.checkin-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(154, 86, 181, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%);
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.checkin-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-500, #9a56b5) 0%, var(--brand-600, #7c3aed) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.checkin-title-section {
  flex: 1;
  min-width: 0;
}

.checkin-title-section h2 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 4px;
}

.checkin-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.checkin-body {
  padding: 24px;
}

.checkin-info {
  background: #f9fafb;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid #e5e7eb;
}

.info-label {
  font-size: 14px;
  color: #6b7280;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.checkin-form {
  margin-top: 16px;
}

.form-item {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.input-modern {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.input-modern:focus {
  outline: none;
  border-color: var(--brand-500, #9a56b5);
  box-shadow: 0 0 0 3px rgba(154, 86, 181, 0.1);
}

.location-hint,
.none-hint {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
  line-height: 1.5;
}

.location-display {
  margin-top: 12px;
  padding: 12px;
  background: #f0fdf4;
  border-radius: 8px;
  font-size: 13px;
  color: #166534;
}

.checkin-footer {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border, #e5e7eb);
  background: #f9fafb;
}

.checkin-footer .btn-modern {
  flex: 1;
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
}

@media (max-width: 480px) {
  .checkin-share-page {
    padding: 16px;
  }

  .checkin-header {
    padding: 20px;
  }

  .checkin-body {
    padding: 20px;
  }

  .checkin-footer {
    flex-direction: column;
  }
}
</style>
