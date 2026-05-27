import {
  getSheetList,
  getSheetDetail,
  uploadSheet,
  updateSheet,
  deleteSheet,
  downloadSheet
} from '@/api/sheets'

const state = {
  sheets: {
    list: [],
    total: 0,
    current: null
  },
  loading: false,
  uploading: false
}

const mutations = {
  SET_LOADING(state, loading) {
    state.loading = loading
  },

  SET_UPLOADING(state, uploading) {
    state.uploading = uploading
  },

  SET_SHEET_LIST(state, { list, total }) {
    state.sheets.list = list
    state.sheets.total = total
  },

  SET_CURRENT_SHEET(state, sheet) {
    state.sheets.current = sheet
  },

  ADD_SHEET(state, sheet) {
    state.sheets.list.unshift(sheet)
    state.sheets.total++
  },

  UPDATE_SHEET(state, updatedSheet) {
    const index = state.sheets.list.findIndex(s => s.sheet_id === updatedSheet.sheet_id)
    if (index !== -1) {
      state.sheets.list.splice(index, 1, updatedSheet)
    }
    if (state.sheets.current && state.sheets.current.sheet_id === updatedSheet.sheet_id) {
      state.sheets.current = updatedSheet
    }
  },

  REMOVE_SHEET(state, sheetId) {
    state.sheets.list = state.sheets.list.filter(s => s.sheet_id !== sheetId)
    state.sheets.total--
    if (state.sheets.current && state.sheets.current.sheet_id === sheetId) {
      state.sheets.current = null
    }
  }
}

const actions = {
  async fetchSheetList({ commit }, params = {}) {
    commit('SET_LOADING', true)
    try {
      const response = await getSheetList(params)
      commit('SET_SHEET_LIST', {
        list: response.data.sheets,
        total: response.data.total
      })
      return response
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async fetchSheetDetail({ commit }, sheetId) {
    const response = await getSheetDetail(sheetId)
    commit('SET_CURRENT_SHEET', response.data)
    return response
  },

  async uploadSheet({ commit }, { file, metadata, onProgress }) {
    commit('SET_UPLOADING', true)
    try {
      const response = await uploadSheet(file, metadata, onProgress)
      commit('ADD_SHEET', response.data)
      return response
    } finally {
      commit('SET_UPLOADING', false)
    }
  },

  async updateSheet({ commit }, { sheetId, sheetData }) {
    const response = await updateSheet(sheetId, sheetData)
    commit('UPDATE_SHEET', response.data)
    return response
  },

  async deleteSheet({ commit }, sheetId) {
    await deleteSheet(sheetId)
    commit('REMOVE_SHEET', sheetId)
  },

  // eslint-disable-next-line no-unused-vars
  async downloadSheet({ commit }, sheetId) {
    const response = await downloadSheet(sheetId)
    return response
  }
}

const getters = {
  sheetList: state => state.sheets.list,
  sheetTotal: state => state.sheets.total,
  currentSheet: state => state.sheets.current,
  loading: state => state.loading,
  uploading: state => state.uploading
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
