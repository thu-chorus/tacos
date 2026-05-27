/**
 * 分享功能工具函数
 * 用于生成分享链接、复制到剪贴板、检测剪贴板中的分享链接
 */
import { notify } from './notify'

/**
 * 获取TaCOS的基础URL
 * @returns {string} 基础URL
 */
export function getBaseUrl() {
  return window.location.origin
}

/**
 * 生成干净的分享URL（去除ref参数）
 * @param {string} url - 原始URL
 * @returns {string} 干净的URL
 */
export function getCleanUrl(url = window.location.href) {
  try {
    const urlObj = new URL(url)
    urlObj.searchParams.delete('ref')
    return urlObj.toString()
  } catch {
    return url
  }
}

/**
 * 生成分享文本
 * @param {string} userName - 用户名称
 * @param {string} pageInfo - 页面信息描述
 * @param {string} url - 分享的URL
 * @returns {string} 分享文本
 */
export function generateShareText(userName, pageInfo, url) {
  return `${userName}分享了${pageInfo}给你:${url}，复制此内容到TaCOS或直接点击链接访问`
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>} 是否复制成功
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    // 降级方案：使用 execCommand
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.left = '-9999px'
    textArea.style.top = '-9999px'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      return true
    } finally {
      document.body.removeChild(textArea)
    }
  } catch (error) {
    console.error('复制到剪贴板失败:', error)
    return false
  }
}

/**
 * 从剪贴板读取文本
 * @returns {Promise<string|null>} 剪贴板文本或null
 */
export async function readFromClipboard() {
  try {
    if (navigator.clipboard && navigator.clipboard.readText) {
      return await navigator.clipboard.readText()
    }
    return null
  } catch (error) {
    // 用户可能拒绝了剪贴板权限，静默失败
    return null
  }
}

/**
 * 解析分享文本中的TaCOS链接
 * @param {string} text - 分享文本
 * @returns {{ url: string, sharer: string, pageInfo: string } | null} 解析结果或null
 */
export function parseShareText(text) {
  if (!text) {
    return null
  }

  const baseUrl = getBaseUrl()

  // 首先检查文本中是否包含TaCOS链接
  // 匹配格式: "{用户}分享了{页面信息}给你:{url}，复制此内容到TaCOS或直接点击链接访问"
  const sharePattern = /^(.+?)分享了(.+?)给你:(https?:\/\/[^\s,，]+)/
  const match = text.match(sharePattern)

  if (match) {
    const [, sharer, pageInfo, url] = match
    // 验证URL是否属于当前TaCOS实例
    if (url.startsWith(baseUrl)) {
      return {
        url: url.trim(),
        sharer: sharer.trim(),
        pageInfo: pageInfo.trim()
      }
    }
  }

  // 也检查纯URL的情况
  const urlPattern = new RegExp(`(${baseUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^\\s,，]*)`)
  const urlMatch = text.match(urlPattern)

  if (urlMatch) {
    return {
      url: urlMatch[1].trim(),
      sharer: '',
      pageInfo: ''
    }
  }

  return null
}

/**
 * 执行分享操作
 * @param {string} userName - 用户名称
 * @param {string} pageInfo - 页面信息
 * @returns {Promise<boolean>} 是否分享成功
 */
export async function doShare(userName, pageInfo) {
  const url = getCleanUrl()
  const shareText = generateShareText(userName, pageInfo, url)
  const success = await copyToClipboard(shareText)

  if (success) {
    notify.success('分享链接已复制到剪贴板')
  } else {
    notify.error('复制失败，请手动复制链接')
  }

  return success
}

/**
 * 根据路由判断是否为表单页面
 * @param {object} route - Vue Router route对象
 * @returns {boolean} 是否为表单页面
 */
export function isFormPage(route) {
  if (!route) {
    return false
  }

  // 检查 meta 中的 isFormPage 标记
  if (route.meta?.isFormPage === true) {
    return true
  }

  // 通过路由名称判断
  const formRoutePatterns = ['Create', 'Edit', 'Upload', 'Form', 'FirstLogin']

  const routeName = route.name || ''
  return formRoutePatterns.some(pattern => routeName.includes(pattern))
}

/**
 * 根据路由判断是否应该显示分享按钮
 * @param {object} route - Vue Router route对象
 * @returns {boolean} 是否显示分享按钮
 */
export function shouldShowShareButton(route) {
  if (!route) {
    return false
  }

  // 不在表单页面显示
  if (isFormPage(route)) {
    return false
  }

  // 不在登录页面显示
  const noSharePages = ['Login', 'FirstLogin', 'Forbidden', 'NotFound']
  if (noSharePages.includes(route.name)) {
    return false
  }

  // 不在没有 sidebar 的页面显示（如首页登录页等）
  if (route.meta?.noSidebar) {
    return false
  }

  return true
}

/**
 * 获取默认的页面分享信息
 * @param {object} route - Vue Router route对象
 * @returns {string} 页面信息
 */
export function getDefaultPageInfo(route) {
  if (!route) {
    return '一个页面'
  }

  // 使用路由 meta 中的 title
  if (route.meta?.title) {
    return route.meta.title
  }

  return '一个页面'
}

/**
 * 生成签到分享URL
 * @param {string} eventId - 活动ID
 * @param {object} session - 签到session对象
 * @param {string} eventName - 活动名称
 * @returns {string} 签到分享URL
 */
export function generateCheckinShareUrl(eventId, session, eventName) {
  const baseUrl = getBaseUrl()
  const params = new URLSearchParams({
    session: session.id,
    type: session.type || 'NONE',
    name: session.name || '',
    event_name: eventName || ''
  })
  return `${baseUrl}/events/${eventId}/checkin-share?${params.toString()}`
}

/**
 * 生成签到分享文本
 * @param {string} userName - 用户名称
 * @param {string} eventName - 活动名称
 * @param {string} sessionName - 签到名称
 * @param {string} url - 分享的URL
 * @returns {string} 分享文本
 */
export function generateCheckinShareText(userName, eventName, sessionName, url) {
  return `${userName}分享了「${eventName}」的签到「${sessionName}」给你:${url}，复制此内容到TaCOS或直接点击链接访问`
}

/**
 * 解析签到分享文本
 * @param {string} text - 分享文本
 * @returns {{ url: string, sharer: string, eventName: string, sessionName: string, isCheckinShare: boolean } | null}
 */
export function parseCheckinShareText(text) {
  if (!text) {
    return null
  }

  const baseUrl = getBaseUrl()

  // 匹配格式: "{用户}分享了「{活动名}」的签到「{签到名}」给你:{url}"
  const checkinPattern = /^(.+?)分享了「(.+?)」的签到「(.+?)」给你:(https?:\/\/[^\s,，]+)/
  const match = text.match(checkinPattern)

  if (match) {
    const [, sharer, eventName, sessionName, url] = match
    // 验证URL是否属于当前TaCOS实例且是签到分享链接
    if (url.startsWith(baseUrl) && url.includes('/checkin-share')) {
      return {
        url: url.trim(),
        sharer: sharer.trim(),
        eventName: eventName.trim(),
        sessionName: sessionName.trim(),
        isCheckinShare: true
      }
    }
  }

  return null
}

/**
 * 执行签到分享操作
 * @param {string} userName - 用户名称
 * @param {string} eventId - 活动ID
 * @param {string} eventName - 活动名称
 * @param {object} session - 签到session对象
 * @returns {Promise<boolean>} 是否分享成功
 */
export async function doCheckinShare(userName, eventId, eventName, session) {
  const url = generateCheckinShareUrl(eventId, session, eventName)
  const sessionName = session.name || '签到'
  const shareText = generateCheckinShareText(userName, eventName, sessionName, url)
  const success = await copyToClipboard(shareText)

  if (success) {
    notify.success('签到分享链接已复制到剪贴板')
  } else {
    notify.error('复制失败，请手动复制链接')
  }

  return success
}

export default {
  getBaseUrl,
  getCleanUrl,
  generateShareText,
  copyToClipboard,
  readFromClipboard,
  parseShareText,
  doShare,
  isFormPage,
  shouldShowShareButton,
  getDefaultPageInfo,
  generateCheckinShareUrl,
  generateCheckinShareText,
  parseCheckinShareText,
  doCheckinShare
}
