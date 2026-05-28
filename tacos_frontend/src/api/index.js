import axios from 'axios'
import { notify } from '@/utils/notify'
import { getToken, removeToken, getRefreshToken, setToken, setRefreshToken } from '@/utils/auth'
import router from '@/router'
import store from '@/store'
import { API_BASE_URL } from '@/utils/constants'

// 创建axios实例
const BASE_URL =
  (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL) || API_BASE_URL
const service = axios.create({
  baseURL: BASE_URL, // 接口基础路径（支持通过 VITE_API_BASE_URL 覆盖，如 http://localhost:8000/api/v1）
  timeout: 60000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 401 处理防抖，避免重复弹窗/重定向
let isHandling401 = false

// 令牌刷新状态管理
let isRefreshing = false
let refreshSubscribers = []

// 添加等待刷新的请求
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 刷新完成后执行所有等待的请求
function onTokenRefreshed(newToken) {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// 刷新失败，拒绝所有等待的请求
function onRefreshFailed(error) {
  refreshSubscribers.forEach(callback => callback(null, error))
  refreshSubscribers = []
}

// 刷新Token
async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  // 直接使用 axios 而不是 service，避免拦截器循环
  const response = await axios.post(`${BASE_URL}/auth/refresh`, { refresh: refreshToken })
  const data = response.data

  if (data && data.code === 200 && data.data) {
    const { token, refresh: newRefresh } = data.data
    if (token) {
      setToken(token)
      store.commit('auth/SET_TOKEN', token)
    }
    // 如果后端返回了新的 refresh token（滑动刷新），也更新它
    if (newRefresh) {
      setRefreshToken(newRefresh)
    }
    return token
  }
  throw new Error('Token refresh failed')
}

// 处理登出（清理状态并跳转登录页）
function handleLogout(cfg, message) {
  // 防抖：只在第一次检测到需要登出时执行
  if (!isHandling401) {
    isHandling401 = true
    try {
      removeToken()
      store.commit('auth/CLEAR_AUTH', null, { root: true })
      router.push('/login')
      if (!cfg.skipErrorMessage) {
        notify.error(message)
      }
    } finally {
      setTimeout(() => {
        isHandling401 = false
      }, 1000)
    }
  }
}

function formatErrorDetail(detail) {
  if (!detail || typeof detail !== 'object' || Array.isArray(detail)) {
    return ''
  }
  return Object.entries(detail)
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}: ${value.join('; ')}`
      }
      if (value && typeof value === 'object') {
        return `${key}: ${formatErrorDetail(value) || JSON.stringify(value)}`
      }
      return `${key}: ${String(value)}`
    })
    .filter(Boolean)
    .join(' | ')
}

function resolveErrorMessage(data, fallback) {
  const detailMessage = formatErrorDetail(data && data.data)
  if (detailMessage) {
    return detailMessage
  }
  return (data && data.message) || fallback
}

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 显示加载状态
    store.dispatch('setLoading', true)

    // 添加认证token
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  error => {
    store.dispatch('setLoading', false)
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    store.dispatch('setLoading', false)

    const cfg = (response && response.config) || {}

    // 文件下载等二进制响应直接返回
    const contentType = response.headers && response.headers['content-type']
    const isBlob =
      (response.config && response.config.responseType === 'blob') ||
      (response.request && response.request.responseType === 'blob')
    const isBinaryContent =
      contentType &&
      (contentType.includes('application/pdf') ||
        contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') ||
        contentType.includes('application/octet-stream'))
    if (isBlob || isBinaryContent) {
      return response
    }

    const res = response.data

    // 根据code判断请求结果
    // 针对DELETE请求，204也视为成功
    const method = response.config && response.config.method
    if (
      (res && (res.code === 200 || res.code === 201 || res.code === 202)) ||
      (method === 'delete' && response.status === 204)
    ) {
      return res || { code: 204, message: 'No Content', data: null }
    } else {
      // 业务错误处理
      const message = (res && res.message) || '请求失败'
      if (!cfg.skipErrorMessage) {
        notify.error(message)
      }
      return Promise.reject(new Error(message))
    }
  },
  async error => {
    store.dispatch('setLoading', false)

    const { response, config } = error
    const cfg = config || (response && response.config) || {}
    let message = '网络错误，请稍后重试'

    if (response) {
      const { status, data } = response

      switch (status) {
      case 400:
        message = resolveErrorMessage(data, '请求参数错误')
        break
      case 401:
        // 如果是刷新token的请求失败，直接跳转登录
        if (config && config.url && config.url.includes('/auth/refresh')) {
          handleLogout(cfg, '登录已过期，请重新登录')
          return Promise.reject(error)
        }

        // 尝试刷新Token
        if (!isRefreshing) {
          isRefreshing = true

          try {
            const newToken = await refreshAccessToken()
            isRefreshing = false
            onTokenRefreshed(newToken)

            // 重试原请求
            if (config) {
              config.headers.Authorization = `Bearer ${newToken}`
              return service(config)
            }
          } catch (refreshError) {
            isRefreshing = false
            onRefreshFailed(refreshError)
            handleLogout(cfg, '登录已过期，请重新登录')
            return Promise.reject(error)
          }
        } else {
          // 其他请求等待刷新完成
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((newToken, err) => {
              if (err || !newToken) {
                reject(error)
              } else if (config) {
                config.headers.Authorization = `Bearer ${newToken}`
                resolve(service(config))
              } else {
                reject(error)
              }
            })
          })
        }
        return Promise.reject(error)
      case 403:
        // 保留后端消息（如“不在签到范围内”），有详细信息时追加
        if (data && data.message) {
          const detail = (data && data.data) || {}
          if (detail && typeof detail.distance === 'number') {
            message = `${data.message}（距目标约${Math.round(detail.distance)}米）`
          } else {
            message = data.message
          }
        } else {
          message = '权限不足，无法访问'
        }
        break
      case 404:
        message = '请求的资源不存在'
        break
      case 409:
        message = data.message || '资源冲突'
        break
      case 422:
        message = resolveErrorMessage(data, '数据验证失败')
        break
      case 500:
        message = '服务器内部错误'
        break
      default:
        message = (data && data.message) || `请求失败 (${status})`
      }
    }

    if (!cfg.skipErrorMessage) {
      notify.error(message)
    }
    return Promise.reject(error)
  }
)

// 通用请求方法
export const request = {
  get(url, params = {}, config = {}) {
    return service.get(url, { params, ...config })
  },

  post(url, data = {}, config = {}) {
    return service.post(url, data, { ...config })
  },

  put(url, data = {}, config = {}) {
    return service.put(url, data, { ...config })
  },

  patch(url, data = {}, config = {}) {
    return service.patch(url, data, { ...config })
  },

  delete(url, config = {}) {
    return service.delete(url, { ...config })
  },

  upload(url, formData, onProgress, config = {}) {
    return service.post(url, formData, {
      ...config,
      headers: {
        ...(config.headers || {}),
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress || config.onUploadProgress
    })
  }
}

export default service
