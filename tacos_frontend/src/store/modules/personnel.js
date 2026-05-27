import {
  getMemberList,
  getMemberDetail,
  createMember,
  updateMember,
  deleteMember,
  getInstructorList,
  getInstructorDetail,
  createInstructor,
  updateInstructor,
  deleteInstructor
} from '@/api/personnel'

const state = {
  members: {
    list: [],
    total: 0,
    current: null
  },
  instructors: {
    list: [],
    total: 0,
    current: null
  },
  loading: false
}

const mutations = {
  SET_LOADING(state, loading) {
    state.loading = loading
  },

  SET_MEMBER_LIST(state, { list, total }) {
    state.members.list = list
    state.members.total = total
  },

  SET_CURRENT_MEMBER(state, member) {
    state.members.current = member
  },

  ADD_MEMBER(state, member) {
    state.members.list.unshift(member)
    state.members.total++
  },

  UPDATE_MEMBER(state, updatedMember) {
    const index = state.members.list.findIndex(m => m.user_id === updatedMember.user_id)
    if (index !== -1) {
      state.members.list.splice(index, 1, updatedMember)
    }
    if (state.members.current && state.members.current.user_id === updatedMember.user_id) {
      state.members.current = updatedMember
    }
  },

  REMOVE_MEMBER(state, userId) {
    state.members.list = state.members.list.filter(m => m.user_id !== userId)
    state.members.total--
    if (state.members.current && state.members.current.user_id === userId) {
      state.members.current = null
    }
  },

  SET_INSTRUCTOR_LIST(state, { list, total }) {
    state.instructors.list = list
    state.instructors.total = total
  },

  SET_CURRENT_INSTRUCTOR(state, instructor) {
    state.instructors.current = instructor
  },

  ADD_INSTRUCTOR(state, instructor) {
    state.instructors.list.unshift(instructor)
    state.instructors.total++
  },

  UPDATE_INSTRUCTOR(state, updatedInstructor) {
    const index = state.instructors.list.findIndex(
      i => i.instructor_id === updatedInstructor.instructor_id
    )
    if (index !== -1) {
      state.instructors.list.splice(index, 1, updatedInstructor)
    }
    if (
      state.instructors.current &&
      state.instructors.current.instructor_id === updatedInstructor.instructor_id
    ) {
      state.instructors.current = updatedInstructor
    }
  },

  REMOVE_INSTRUCTOR(state, instructorId) {
    state.instructors.list = state.instructors.list.filter(i => i.instructor_id !== instructorId)
    state.instructors.total--
    if (state.instructors.current && state.instructors.current.instructor_id === instructorId) {
      state.instructors.current = null
    }
  }
}

const actions = {
  // 队员管理
  async fetchMemberList({ commit }, params = {}) {
    commit('SET_LOADING', true)
    try {
      const response = await getMemberList(params)
      commit('SET_MEMBER_LIST', {
        list: response.data.members,
        total: response.data.total
      })
      return response
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async fetchMemberDetail({ commit }, userId) {
    const response = await getMemberDetail(userId)
    commit('SET_CURRENT_MEMBER', response.data)
    return response
  },

  async createMember({ commit }, memberData) {
    const response = await createMember(memberData)
    commit('ADD_MEMBER', response.data)
    return response
  },

  async updateMember({ commit }, { userId, memberData }) {
    const response = await updateMember(userId, memberData)
    commit('UPDATE_MEMBER', response.data)
    return response
  },

  async deleteMember({ commit }, userId) {
    await deleteMember(userId)
    commit('REMOVE_MEMBER', userId)
  },

  // 教师管理
  async fetchInstructorList({ commit }, params = {}) {
    commit('SET_LOADING', true)
    try {
      const response = await getInstructorList(params)
      commit('SET_INSTRUCTOR_LIST', {
        list: response.data.instructors,
        total: response.data.total
      })
      return response
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async fetchInstructorDetail({ commit }, instructorId) {
    const response = await getInstructorDetail(instructorId)
    commit('SET_CURRENT_INSTRUCTOR', response.data)
    return response
  },

  async createInstructor({ commit }, instructorData) {
    const response = await createInstructor(instructorData)
    commit('ADD_INSTRUCTOR', response.data)
    return response
  },

  async updateInstructor({ commit }, { instructorId, instructorData }) {
    const response = await updateInstructor(instructorId, instructorData)
    commit('UPDATE_INSTRUCTOR', response.data)
    return response
  },

  async deleteInstructor({ commit }, instructorId) {
    await deleteInstructor(instructorId)
    commit('REMOVE_INSTRUCTOR', instructorId)
  }
}

const getters = {
  memberList: state => state.members.list,
  memberTotal: state => state.members.total,
  currentMember: state => state.members.current,
  instructorList: state => state.instructors.list,
  instructorTotal: state => state.instructors.total,
  currentInstructor: state => state.instructors.current,
  loading: state => state.loading
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
