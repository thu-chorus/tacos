const state = {
  // 系统配置
  config: {
    title: 'TaCOS - 清华合唱队在线系统',
    version: import.meta.env.VITE_APP_VERSION || '0.0.0'
  },

  // 分享功能状态
  share: {
    // 当前页面的自定义分享信息，由各页面设置
    pageInfo: '',
    // 是否允许分享（默认true，某些页面可以禁用）
    enabled: true
  },

  // 常量定义
  constants: {
    // 用户角色
    USER_ROLES: {
      SUPER_ADMIN: 'SuperAdmin',
      ADMIN: 'Admin',
      MEMBER: 'Member'
    },

    MEMBER_STATUSES: [
      { value: 'ACTIVE', label: '在队' },
      { value: 'ALUMNI', label: '校友' },
      { value: 'INACTIVE', label: '停用' }
    ],

    // 声部
    VOICE_PARTS: [
      { value: 'S1', label: '女高音1' },
      { value: 'S2', label: '女高音2' },
      { value: 'A1', label: '女中音1' },
      { value: 'A2', label: '女中音2' },
      { value: 'T1', label: '男高音1' },
      { value: 'T2', label: '男高音2' },
      { value: 'B1', label: '男低音1' },
      { value: 'B2', label: '男低音2' },
      { value: 'Other', label: '其他' }
    ],

    // 梯队
    TIERS: [
      { value: '一队', label: '一队' },
      { value: '二队', label: '二队' }
    ],

    // 政治面貌
    POLITICAL_STATUS: [
      { value: '中共党员', label: '中共党员' },
      { value: '中共预备党员', label: '中共预备党员' },
      { value: '共青团员', label: '共青团员' },
      { value: '群众', label: '群众' },
      { value: '民主党派成员', label: '民主党派成员' },
      { value: '无党派人士', label: '无党派人士' },
      { value: '留学生', label: '留学生' }
    ],

    // 党团关系所在
    POLITICAL_AFFILIATION: [
      { value: '艺术团', label: '艺术团' },
      { value: '院系', label: '院系' },
      { value: '无', label: '无' }
    ],

    // 清华大学院系列表
    DEPARTMENTS: [
      { value: '建筑学院', label: '建筑学院' },
      { value: '土木工程系', label: '土木工程系' },
      { value: '水利水电工程系', label: '水利水电工程系' },
      { value: '环境学院', label: '环境学院' },
      { value: '机械工程系', label: '机械工程系' },
      { value: '精密仪器系', label: '精密仪器系' },
      { value: '热能工程系', label: '热能工程系' },
      { value: '汽车工程系', label: '汽车工程系' },
      { value: '工业工程系', label: '工业工程系' },
      { value: '电机工程与应用电子技术系', label: '电机工程与应用电子技术系' },
      { value: '电子工程系', label: '电子工程系' },
      { value: '计算机科学与技术系', label: '计算机科学与技术系' },
      { value: '自动化系', label: '自动化系' },
      { value: '软件学院', label: '软件学院' },
      { value: '航天航空学院', label: '航天航空学院' },
      { value: '工程物理系', label: '工程物理系' },
      { value: '化学工程系', label: '化学工程系' },
      { value: '材料学院', label: '材料学院' },
      { value: '数学科学系', label: '数学科学系' },
      { value: '物理系', label: '物理系' },
      { value: '化学系', label: '化学系' },
      { value: '生命科学学院', label: '生命科学学院' },
      { value: '地球系统科学系', label: '地球系统科学系' },
      { value: '心理学系', label: '心理学系' },
      { value: '经济管理学院', label: '经济管理学院' },
      { value: '公共管理学院', label: '公共管理学院' },
      { value: '人文学院', label: '人文学院' },
      { value: '社会科学学院', label: '社会科学学院' },
      { value: '马克思主义学院', label: '马克思主义学院' },
      { value: '法学院', label: '法学院' },
      { value: '新闻与传播学院', label: '新闻与传播学院' },
      { value: '美术学院', label: '美术学院' },
      { value: '医学院', label: '医学院' },
      { value: '药学院', label: '药学院' },
      { value: '万科公共卫生与健康学院', label: '万科公共卫生与健康学院' },
      { value: '五道口金融学院', label: '五道口金融学院' },
      { value: '深圳国际研究生院', label: '深圳国际研究生院' },
      { value: '其他', label: '其他' }
    ]
  },

  // UI状态
  ui: {
    sidebarCollapsed: false,
    theme: 'light'
  }
}

const mutations = {
  SET_SIDEBAR_COLLAPSED(state, collapsed) {
    state.ui.sidebarCollapsed = collapsed
  },

  SET_THEME(state, theme) {
    state.ui.theme = theme
  },

  UPDATE_CONFIG(state, config) {
    state.config = { ...state.config, ...config }
  },

  // 分享功能 mutations
  SET_SHARE_PAGE_INFO(state, pageInfo) {
    state.share.pageInfo = pageInfo
  },

  SET_SHARE_ENABLED(state, enabled) {
    state.share.enabled = enabled
  },

  RESET_SHARE_STATE(state) {
    state.share.pageInfo = ''
    state.share.enabled = true
  }
}

const actions = {
  toggleSidebar({ commit, state }) {
    commit('SET_SIDEBAR_COLLAPSED', !state.ui.sidebarCollapsed)
  },

  setSidebarCollapsed({ commit }, collapsed) {
    commit('SET_SIDEBAR_COLLAPSED', collapsed)
  },

  setTheme({ commit }, theme) {
    commit('SET_THEME', theme)
  },

  updateConfig({ commit }, config) {
    commit('UPDATE_CONFIG', config)
  },

  // 分享功能 actions
  setSharePageInfo({ commit }, pageInfo) {
    commit('SET_SHARE_PAGE_INFO', pageInfo)
  },

  setShareEnabled({ commit }, enabled) {
    commit('SET_SHARE_ENABLED', enabled)
  },

  resetShareState({ commit }) {
    commit('RESET_SHARE_STATE')
  }
}

const getters = {
  config: state => state.config,
  constants: state => state.constants,
  sidebarCollapsed: state => state.ui.sidebarCollapsed,
  theme: state => state.ui.theme,

  // 常量获取器
  voiceParts: state => state.constants.VOICE_PARTS,
  tiers: state => state.constants.TIERS,
  politicalStatus: state => state.constants.POLITICAL_STATUS,
  politicalAffiliation: state => state.constants.POLITICAL_AFFILIATION,
  departments: state => state.constants.DEPARTMENTS,
  userRoles: state => state.constants.USER_ROLES,
  memberStatuses: state => state.constants.MEMBER_STATUSES,

  // 分享功能 getters
  sharePageInfo: state => state.share.pageInfo,
  shareEnabled: state => state.share.enabled
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}
