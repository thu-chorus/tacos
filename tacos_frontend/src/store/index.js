import { createStore } from 'vuex'
import auth from './modules/auth'
import personnel from './modules/personnel'
import sheets from './modules/sheets'
import common from './modules/common'

const store = createStore({
  modules: {
    auth,
    personnel,
    sheets,
    common
  },

  strict: process.env.NODE_ENV !== 'production',

  state: {
    // 全局状态
    loading: false,
    error: null
  },

  mutations: {
    SET_LOADING(state, loading) {
      state.loading = loading
    },

    SET_ERROR(state, error) {
      state.error = error
    },

    CLEAR_ERROR(state) {
      state.error = null
    }
  },

  actions: {
    setLoading({ commit }, loading) {
      commit('SET_LOADING', loading)
    },

    setError({ commit }, error) {
      commit('SET_ERROR', error)
    },

    clearError({ commit }) {
      commit('CLEAR_ERROR')
    }
  },

  getters: {
    loading: state => state.loading,
    error: state => state.error
  }
})

export default store
