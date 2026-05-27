import Cookies from 'js-cookie'

const TOKEN_KEY = 'tacos_token'
const REFRESH_TOKEN_KEY = 'tacos_refresh_token'

// 令牌管理
export function getToken() {
  return Cookies.get(TOKEN_KEY)
}

export function setToken(token) {
  // 置于根路径，避免在 /login 下设置导致其他路由不可读
  // 访问令牌有效期与后端保持一致（默认1天），Cookie 保留10天以便刷新
  return Cookies.set(TOKEN_KEY, token, { expires: 10, path: '/' }) // 10天过期
}

export function removeToken() {
  Cookies.remove(TOKEN_KEY)
  Cookies.remove(REFRESH_TOKEN_KEY)
  // 确保移除根路径下的Cookie
  Cookies.remove(TOKEN_KEY, { path: '/' })
  Cookies.remove(REFRESH_TOKEN_KEY, { path: '/' })
}

// 刷新令牌管理
export function getRefreshToken() {
  return Cookies.get(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(refreshToken) {
  // 刷新令牌有效期10天，启用滑动刷新后会在每次刷新时更新
  return Cookies.set(REFRESH_TOKEN_KEY, refreshToken, { expires: 10, path: '/' }) // 10天过期
}

// 权限检查
export function hasPermission(userRole, requiredRoles) {
  if (!requiredRoles || requiredRoles.length === 0) {
    return true
  }
  return requiredRoles.includes(userRole)
}

// 检查是否为管理员
export function isAdmin(userRole) {
  return ['SuperAdmin', 'Admin'].includes(userRole)
}

// 检查是否为超级管理员
export function isSuperAdmin(userRole) {
  return userRole === 'SuperAdmin'
}
