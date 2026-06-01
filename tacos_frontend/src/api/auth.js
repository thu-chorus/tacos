import { request } from './index'
import { getRefreshToken } from '@/utils/auth'
import { CACHE_TTL, clearRequestCache, getCached, invalidateCache } from '@/utils/requestCache'

// 用户登录
export function login(data) {
  // 避免与组件内的错误提示重复，跳过全局错误提示
  clearRequestCache()
  return request.post('/auth/login', data, { skipErrorMessage: true })
}

// 用户登出
export function logout() {
  return request.post('/auth/logout').finally(() => {
    clearRequestCache()
  })
}

// 刷新Token
export function refreshToken() {
  const refresh = getRefreshToken()
  return request.post('/auth/refresh', { refresh })
}

// 获取当前用户信息
export function getUserInfo() {
  return request.get('/auth/me')
}

// 更新个人信息（目前支持 name）
export function updateProfile(data) {
  return request.put('/auth/profile', data).finally(() => {
    invalidateCache('auth:profile')
  })
}

export function getProfile(options = {}) {
  return getCached('auth:profile', () => request.get('/auth/profile'), {
    ttl: CACHE_TTL.PROFILE,
    ...options
  })
}

// 修改密码
export function changePassword(data) {
  return request.put('/auth/password', data)
}

// 首次登录信息完善
export function updateFirstLoginProfile(data) {
  return request.put('/auth/first-login', data).finally(() => {
    invalidateCache('auth:profile')
  })
}
