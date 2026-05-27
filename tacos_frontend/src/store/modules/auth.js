import { login, logout as logoutAPI, refreshToken, getUserInfo } from '@/api/auth'
import { getToken, setToken, removeToken, setRefreshToken } from '@/utils/auth'

const state = {
  token: getToken(),
  user: null,
  roles: []
}

const mutations = {
  SET_TOKEN(state, token) {
    state.token = token
  },

  SET_USER(state, user) {
    state.user = user
  },

  SET_ROLES(state, roles) {
    state.roles = roles
  },

  CLEAR_AUTH(state) {
    state.token = null
    state.user = null
    state.roles = []
  }
}

const actions = {
  // 用户登录
  async login({ commit }, loginForm) {
    const response = await login(loginForm)
    const { token, refresh_token, user, is_first_login, needs_profile_setup } = response.data
    const currentUser = {
      ...user,
      is_first_login: !!(is_first_login ?? user?.is_first_login),
      needs_profile_setup: !!(needs_profile_setup ?? user?.needs_profile_setup)
    }

    commit('SET_TOKEN', token)
    commit('SET_USER', currentUser)
    commit('SET_ROLES', [currentUser.role])

    setToken(token)
    if (refresh_token) {
      setRefreshToken(refresh_token)
    }

    return response
  },

  // 获取用户信息
  async getUserInfo({ commit }) {
    const response = await getUserInfo()
    const user = response.data || {}
    const currentUser = {
      ...user,
      is_first_login: !!user?.is_first_login,
      needs_profile_setup: !!user?.needs_profile_setup
    }

    commit('SET_USER', currentUser)
    commit('SET_ROLES', [currentUser.role])

    return currentUser
  },

  // 用户登出
  async logout({ commit, state }) {
    try {
      const token = state.token || getToken()
      // 无 token 时跳过调用后端，直接本地清理
      if (token) {
        await logoutAPI()
      }
    } catch (error) {
      // 忽略登出错误，确保本地状态被清理
      console.error('Logout error:', error)
    } finally {
      commit('CLEAR_AUTH')
      removeToken()
    }
  },

  // 检查认证状态
  async checkAuth({ commit, dispatch }) {
    const token = getToken()
    if (token) {
      commit('SET_TOKEN', token)
      try {
        await dispatch('getUserInfo')
      } catch (error) {
        console.error('Check auth error:', error)
        // 清理本地状态，但不调用logout API，避免循环
        commit('CLEAR_AUTH')
        removeToken()
      }
    } else {
      // 没有token时清理状态
      commit('CLEAR_AUTH')
    }
  },

  // 刷新Token
  async refreshToken({ commit }) {
    const response = await refreshToken()
    const { token } = response.data

    commit('SET_TOKEN', token)
    setToken(token)

    return token
  }
}

const getters = {
  token: state => state.token,
  user: state => state.user,
  userRole: state => state.user?.role,
  isLoggedIn: state => !!state.token && !!state.user, // 修复：同时检查token和用户信息
  hasRole: state => role => state.roles.includes(role),
  isAdmin: state => ['SuperAdmin', 'Admin'].includes(state.user?.role),
  isSuperAdmin: state => state.user?.role === 'SuperAdmin'
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
