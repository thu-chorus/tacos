import { request } from './index'

// ========== 队员管理 ==========

// 获取队员总数（利用分页 count）
export function getMemberCount(params = {}) {
  return request.get('/members/', { ...params, page_size: 1 })
}

// 获取队员统计（轻量接口）
export function getMemberStats() {
  return request.get('/members/stats/')
}

// 获取队员列表
export function getMemberList(params) {
  return request.get('/members/', params)
}

// 获取队员详情
export function getMemberDetail(userId) {
  return request.get(`/members/${userId}/`)
}

// 创建队员档案
export function createMember(data) {
  return request.post('/members/', data)
}

// 更新队员信息
export function updateMember(userId, data) {
  return request.put(`/members/${userId}/`, data)
}

// 删除队员档案
export function deleteMember(userId) {
  return request.delete(`/members/${userId}/`)
}

// 批量导入模板下载（Excel）
export function downloadMemberImportTemplate() {
  return request.get('/members/bulk-template/', {}, { responseType: 'blob' })
}

// 批量导入队员（CSV 或 Excel）
export function bulkImportMembers(file, options = {}, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  if (options && Object.prototype.hasOwnProperty.call(options, 'override')) {
    formData.append('override', options.override ? '1' : '0')
  }
  return request.upload('/members/bulk-import/', formData, onProgress)
}

// 发起异步导出任务（返回task_id）
export function initiateExportMembers(params = {}) {
  return request.post('/members/export/', params)
}

// 轮询导出任务状态或获取结果
export function getExportMembersTask(taskId) {
  return request.get(`/members/export-task/${taskId}/`, {}, { responseType: 'blob' })
}

// 向后兼容的导出函数 - 自动处理异步轮询
export async function exportMembers(params = {}) {
  const initResp = await initiateExportMembers(params)
  const taskId = initResp.data?.task_id

  if (!taskId) {
    throw new Error('Failed to get task ID')
  }

  const poll = async () => {
    const resp = await getExportMembersTask(taskId)
    const contentType = resp.headers['content-type'] || resp.headers['Content-Type']

    if (contentType && contentType.includes('application/json')) {
      const text = await resp.data.text()
      const jsonData = JSON.parse(text)
      const taskData = jsonData.data || jsonData

      if (taskData.status === 'PENDING' || taskData.status === 'PROCESSING') {
        await new Promise(resolve => setTimeout(resolve, 1000))
        return poll()
      } else if (taskData.status === 'FAILED') {
        throw new Error(taskData.error_message || 'Export task failed')
      } else {
        throw new Error(`Unexpected task status: ${resp.data.text()}`)
      }
    } else {
      return resp
    }
  }

  return poll()
}

// ========== 外请教师管理 ==========

// 获取教师列表
export function getInstructorList(params) {
  return request.get('/instructors/', params)
}

// 获取教师详情
export function getInstructorDetail(instructorId) {
  return request.get(`/instructors/${instructorId}/`)
}

// 创建教师信息
export function createInstructor(data) {
  return request.post('/instructors/', data)
}

// 更新教师信息
export function updateInstructor(instructorId, data) {
  return request.put(`/instructors/${instructorId}/`, data)
}

// 删除教师信息
export function deleteInstructor(instructorId) {
  return request.delete(`/instructors/${instructorId}/`)
}

// ========== 称号管理 ==========

// 获取称号列表
export function getTitleList(params) {
  return request.get('/titles/', params)
}

// 获取称号详情
export function getTitleDetail(id) {
  return request.get(`/titles/${id}/`)
}

// 创建称号
export function createTitle(data) {
  return request.post('/titles/', data)
}

// 更新称号
export function updateTitle(id, data) {
  return request.put(`/titles/${id}/`, data)
}

// 删除称号
export function deleteTitle(id) {
  return request.delete(`/titles/${id}/`)
}

// 更新生日称号
export function updateBirthdayTitles(data) {
  return request.post('/titles/update-birthday-titles/', data)
}

// ========== 成员-称号 关联 ==========

// 查询成员称号关联（可按 member_id=学号 或 title_id 过滤）
export function getMemberTitles(params) {
  return request.get('/member-titles/', params)
}

// 为成员授予称号（需要 member_id 为成员主键ID，title_id 为称号ID）
export function addMemberTitle(data, config = {}) {
  return request.post('/member-titles/', data, config)
}

// 移除成员称号（需要传中间表ID）
export function removeMemberTitle(id) {
  return request.delete(`/member-titles/${id}/`)
}

// ========== 校友联系方式 ==========

export function getMyAlumniProfile() {
  return request.get('/alumni-profiles/me/')
}

export function updateMyAlumniProfile(data) {
  return request.patch('/alumni-profiles/me/', data)
}

export function getAlumniProfiles(params = {}) {
  return request.get('/alumni-profiles/', params)
}
