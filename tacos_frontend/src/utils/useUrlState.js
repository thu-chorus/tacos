/**
 * useUrlState Composable
 * 将组件状态与 URL query 参数同步
 * 支持页面刷新、返回时保留筛选/分页状态
 */

import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * 将状态与 URL query 参数同步
 *
 * @param {Object} config - 配置对象
 * @param {Object} config.defaults - 默认值对象，key 为参数名，value 为默认值
 * @param {Object} config.types - 类型映射对象，key 为参数名，value 为类型 ('string' | 'number' | 'boolean' | 'array')
 * @param {boolean} config.immediate - 是否立即同步到 URL（默认 false，只在值变化时同步）
 * @param {Function} config.onRestore - 状态恢复后的回调函数
 *
 * @returns {Object} 包含状态对象和辅助方法
 *
 * @example
 * const { state, resetState, updateUrl } = useUrlState({
 *   defaults: {
 *     name: '',
 *     voicePart: '',
 *     page: 1,
 *     pageSize: 20
 *   },
 *   types: {
 *     page: 'number',
 *     pageSize: 'number'
 *   },
 *   onRestore: () => {
 *     // 状态恢复后重新加载数据
 *     loadData()
 *   }
 * })
 */
export function useUrlState(config = {}) {
  const { defaults = {}, types = {}, immediate = false, onRestore = null } = config

  const route = useRoute()
  const router = useRouter()

  // 是否正在从 URL 恢复状态（防止循环更新）
  let isRestoring = false
  // 是否已完成初始化
  let isInitialized = false

  /**
   * 解析 URL query 参数值
   */
  const parseValue = (value, type) => {
    if (value === null || value === undefined || value === '') {
      return type === 'array' ? [] : type === 'number' ? undefined : ''
    }

    switch (type) {
      case 'number': {
        const num = Number(value)
        return isNaN(num) ? undefined : num
      }
      case 'boolean':
        return value === 'true' || value === '1'
      case 'array':
        if (Array.isArray(value)) {
          return value
        }
        if (typeof value === 'string') {
          try {
            const parsed = JSON.parse(value)
            return Array.isArray(parsed) ? parsed : [value]
          } catch {
            return value ? [value] : []
          }
        }
        return []
      default:
        return String(value)
    }
  }

  // 同步初始化：在 setup 阶段就从 URL 恢复状态
  const getInitialState = () => {
    const query = route.query
    const initialState = { ...defaults }

    for (const key of Object.keys(defaults)) {
      const type = types[key] || 'string'
      const urlValue = query[key]

      if (urlValue !== undefined && urlValue !== null && urlValue !== '') {
        const parsedValue = parseValue(urlValue, type)
        if (parsedValue !== undefined) {
          initialState[key] = parsedValue
        }
      }
    }

    return initialState
  }

  // 创建响应式状态对象（使用从 URL 恢复的初始值）
  const state = ref(getInitialState())

  /**
   * 序列化值用于 URL query
   */
  const serializeValue = (value, type) => {
    if (value === null || value === undefined) {
      return undefined
    }
    if (type === 'array') {
      if (!Array.isArray(value) || value.length === 0) {
        return undefined
      }
      return JSON.stringify(value)
    }
    if (type === 'boolean') {
      return value ? 'true' : 'false'
    }
    if (type === 'number') {
      return value !== undefined && value !== null ? String(value) : undefined
    }
    return value || undefined
  }

  /**
   * 从 URL query 恢复状态
   */
  const restoreFromUrl = () => {
    isRestoring = true
    const query = route.query
    const newState = { ...defaults }

    for (const key of Object.keys(defaults)) {
      const type = types[key] || 'string'
      const urlValue = query[key]

      if (urlValue !== undefined && urlValue !== null && urlValue !== '') {
        const parsedValue = parseValue(urlValue, type)
        if (parsedValue !== undefined) {
          newState[key] = parsedValue
        }
      }
    }

    state.value = newState
    isRestoring = false

    if (onRestore && isInitialized) {
      onRestore(state.value)
    }
  }

  /**
   * 将状态同步到 URL query
   */
  const updateUrl = (replace = true) => {
    if (isRestoring) {
      return
    }

    const query = {}
    for (const key of Object.keys(defaults)) {
      const type = types[key] || 'string'
      const value = state.value[key]
      const defaultValue = defaults[key]

      // 只有非默认值才写入 URL
      const serialized = serializeValue(value, type)
      const defaultSerialized = serializeValue(defaultValue, type)

      if (serialized !== undefined && serialized !== defaultSerialized) {
        query[key] = serialized
      }
    }

    // 保留其他不在 defaults 中的 query 参数
    for (const key of Object.keys(route.query)) {
      if (!(key in defaults)) {
        query[key] = route.query[key]
      }
    }

    const newQuery = { ...query }
    const currentQuery = { ...route.query }

    // 检查 query 是否有变化
    const hasChange =
      Object.keys(newQuery).length !== Object.keys(currentQuery).length ||
      Object.keys(newQuery).some(k => newQuery[k] !== currentQuery[k])

    if (hasChange) {
      if (replace) {
        router.replace({ query: newQuery })
      } else {
        router.push({ query: newQuery })
      }
    }
  }

  /**
   * 重置状态为默认值
   */
  const resetState = () => {
    state.value = { ...defaults }
    updateUrl()
  }

  /**
   * 更新单个状态值
   */
  const setState = (key, value) => {
    if (key in defaults) {
      state.value = { ...state.value, [key]: value }
    }
  }

  /**
   * 批量更新状态值
   */
  const setStates = updates => {
    const newState = { ...state.value }
    for (const [key, value] of Object.entries(updates)) {
      if (key in defaults) {
        newState[key] = value
      }
    }
    state.value = newState
  }

  // 监听状态变化，同步到 URL
  watch(
    () => state.value,
    () => {
      if (!isRestoring && isInitialized) {
        updateUrl()
      }
    },
    { deep: true }
  )

  // 监听路由变化，从 URL 恢复状态（处理浏览器前进/后退）
  watch(
    () => route.query,
    () => {
      if (isInitialized && !isRestoring) {
        restoreFromUrl()
      }
    },
    { deep: true }
  )

  // 组件挂载后标记为已初始化
  onMounted(() => {
    isInitialized = true

    if (immediate) {
      updateUrl()
    }

    // 初始化完成后触发回调
    if (onRestore) {
      onRestore(state.value)
    }
  })

  return {
    state,
    resetState,
    setState,
    setStates,
    updateUrl,
    restoreFromUrl
  }
}

export default useUrlState
