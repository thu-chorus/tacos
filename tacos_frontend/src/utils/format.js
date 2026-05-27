import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(relativeTime)
dayjs.tz.setDefault('Asia/Shanghai')

// 日期格式化
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) {
    return ''
  }
  return dayjs(date).tz('Asia/Shanghai').format(format)
}

// 日期时间格式化
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) {
    return ''
  }
  return dayjs(date).tz('Asia/Shanghai').format(format)
}

// 相对时间
export function formatRelativeTime(date) {
  if (!date) {
    return ''
  }
  return dayjs(date).tz('Asia/Shanghai').fromNow()
}

// 文件大小格式化
export function formatFileSize(bytes) {
  if (bytes === 0) {
    return '0 B'
  }

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

// 手机号格式化（隐藏中间4位）
export function formatPhone(phone) {
  if (!phone) {
    return ''
  }
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 身份证号格式化（隐藏中间10位）
export function formatIdCard(idCard) {
  if (!idCard) {
    return ''
  }
  return idCard.replace(/(\d{4})\d{10}(\d{4})/, '$1**********$2')
}

// 用户角色显示
export function formatUserRole(role) {
  const roleMap = {
    SuperAdmin: '超级管理员',
    Admin: '管理员',
    Member: '队员'
  }
  return roleMap[role] || role
}

// 声部显示
export function formatVoicePart(voicePart) {
  const voicePartMap = {
    S1: '女高音1',
    S2: '女高音2',
    A1: '女中音1',
    A2: '女中音2',
    T1: '男高音1',
    T2: '男高音2',
    B1: '男低音1',
    B2: '男低音2',
    Other: '其他'
  }
  return voicePartMap[voicePart] || voicePart
}

// 梯队显示
export function formatTier(tier) {
  return tier || ''
}

// 政治面貌显示
export function formatPoliticalStatus(status) {
  return status || ''
}

// 布尔值显示
export function formatBoolean(value, trueText = '是', falseText = '否') {
  return value ? trueText : falseText
}

// 数字格式化（千分位）
export function formatNumber(num) {
  if (num === null || num === undefined) {
    return ''
  }
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 百分比格式化
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined) {
    return ''
  }
  return `${(value * 100).toFixed(decimals)}%`
}

// 价格格式化
export function formatPrice(price, currency = '¥') {
  if (price === null || price === undefined) {
    return ''
  }
  return `${currency}${formatNumber(price)}`
}
