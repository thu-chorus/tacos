import { request } from './index'
import {
  CACHE_TTL,
  getCached,
  invalidateCache,
  invalidateCachePrefix,
  normalizeCacheKey
} from '@/utils/requestCache'

function invalidateEventCaches(id) {
  if (id) {
    invalidateCache(`events:detail:${id}`)
  }
  invalidateCachePrefix('events:list:')
}

function invalidateEventMemberData(id) {
  invalidateEventCaches(id)
  invalidateCache('auth:profile')
}

function invalidateEventSheetRelations() {
  invalidateCachePrefix('sheets:detail:')
}

export function getEventList(params = {}, options = {}) {
  return getCached(
    `events:list:${normalizeCacheKey(params)}`,
    () => request.get('/events/', params),
    {
      ttl: CACHE_TTL.LIST,
      ...options
    }
  )
}

export function getEventDetail(id, options = {}) {
  return getCached(`events:detail:${id}`, () => request.get(`/events/${id}/`), {
    ttl: CACHE_TTL.DETAIL,
    ...options
  })
}

export function getEventAdminDetail(id) {
  return request.get(`/events/${id}/admin-detail/`)
}

export function createEvent(data) {
  return request.post('/events/', data).finally(() => {
    invalidateEventCaches()
    invalidateEventSheetRelations()
  })
}

export function updateEvent(id, data) {
  return request.put(`/events/${id}/`, data).finally(() => {
    invalidateEventCaches(id)
    invalidateEventSheetRelations()
  })
}

export function deleteEvent(id) {
  return request.delete(`/events/${id}/`).finally(() => {
    invalidateEventCaches(id)
    invalidateEventSheetRelations()
  })
}

export function joinEvent(id) {
  return request.post(`/events/${id}/join/`).finally(() => {
    invalidateEventMemberData(id)
  })
}

export function getCheckinStatus(eventId) {
  return request.get(`/events/${eventId}/checkin/status/`)
}

export function getCheckinSessions(eventId, params = {}) {
  return request.get(`/events/${eventId}/checkin/sessions/`, params)
}

export function startCheckin(eventId, data) {
  return request.post(`/events/${eventId}/checkin/start/`, data)
}

export function stopCheckin(eventId) {
  return request.post(`/events/${eventId}/checkin/stop/`)
}

export function beginCheckin(eventId, sessionId) {
  return request.post(`/events/${eventId}/checkin/begin/`, { session_id: sessionId })
}

export function submitCheckin(eventId, data) {
  // skipErrorMessage: true 避免拦截器自动显示错误，由调用方自行处理
  return request.post(`/events/${eventId}/checkin/submit/`, data, { skipErrorMessage: true })
}

export function getCheckinRecords(eventId, params = {}) {
  return request.get(`/events/${eventId}/checkin/records/`, params)
}

export function getCheckinSessionDetail(eventId, sessionId) {
  return request.get(`/events/${eventId}/checkin/sessions/${sessionId}/detail/`)
}

export function getCheckinSummary(eventId, sessionId) {
  return request.get(`/events/${eventId}/checkin/summary/`, { session_id: sessionId })
}

export function deleteCheckinSession(eventId, sessionId) {
  return request.delete(`/events/${eventId}/checkin/sessions/${sessionId}/`)
}

export function getAssignments(eventId, params = {}) {
  return request.get(`/events/${eventId}/assignments/`, params)
}

export function createAssignment(eventId, data) {
  return request.post(`/events/${eventId}/assignments/create/`, data)
}

export function getAssignmentDetail(eventId, assignmentId) {
  return request.get(`/events/${eventId}/assignments/${assignmentId}/`)
}

export function uploadAssignmentAttachment(eventId, assignmentId, file, onProgress) {
  const form = new FormData()
  form.append('file', file)
  return request.upload(
    `/events/${eventId}/assignments/${assignmentId}/attachments/`,
    form,
    onProgress
  )
}

export function uploadAssignmentAttachments(
  eventId,
  assignmentId,
  { files = [], replace = false } = {},
  onProgress
) {
  const form = new FormData()
  ;(files || []).forEach(f => form.append('files', f))
  if (replace) {
    form.append('replace', 'true')
  }
  return request.upload(
    `/events/${eventId}/assignments/${assignmentId}/attachments/`,
    form,
    onProgress
  )
}

export function submitAssignment(
  eventId,
  assignmentId,
  { text = '', files = [], replace = false } = {},
  onProgress
) {
  const form = new FormData()
  if (text) {
    form.append('text', text)
  }
  ;(files || []).forEach(f => form.append('files', f))
  if (replace) {
    form.append('replace', 'true')
  }
  return request.upload(`/events/${eventId}/assignments/${assignmentId}/submit/`, form, onProgress)
}

export function listAssignmentSubmissions(eventId, assignmentId, params = {}) {
  return request.get(`/events/${eventId}/assignments/${assignmentId}/submissions/`, params)
}

export function gradeAssignmentSubmission(
  eventId,
  assignmentId,
  { submissionId, gradedScore, gradedComment }
) {
  return request.post(`/events/${eventId}/assignments/${assignmentId}/grade/`, {
    submission_id: submissionId,
    graded_score: gradedScore,
    graded_comment: gradedComment
  })
}

export function updateAssignment(eventId, assignmentId, data) {
  return request.put(`/events/${eventId}/assignments/${assignmentId}/edit/`, data)
}

export function deleteAssignment(eventId, assignmentId) {
  return request.delete(`/events/${eventId}/assignments/${assignmentId}/delete/`)
}

export function getMyAssignmentSubmission(eventId, assignmentId) {
  return request.get(`/events/${eventId}/assignments/${assignmentId}/my-submission/`)
}

// 发起异步导出任务（返回task_id）
export function initiateExport(eventId, assignmentId, params = {}) {
  return request.post(`/events/${eventId}/assignments/${assignmentId}/submissions/export/`, params)
}

// 轮询导出任务状态或获取结果
// 如果任务完成，返回blob；否则返回JSON状态
export function getExportTask(eventId, assignmentId, taskId) {
  return request.get(
    `/events/${eventId}/assignments/${assignmentId}/export-task/${taskId}/`,
    {},
    { responseType: 'blob' }
  )
}

// 向后兼容的导出函数 - 自动处理异步轮询
export async function exportAssignmentSubmissions(eventId, assignmentId, params = {}) {
  const initResp = await initiateExport(eventId, assignmentId, params)
  const taskId = initResp.data?.task_id

  if (!taskId) {
    throw new Error('Failed to get task ID')
  }

  const poll = async () => {
    const resp = await getExportTask(eventId, assignmentId, taskId)
    const contentType = resp.headers['content-type'] || resp.headers['Content-Type']

    if (contentType && contentType.includes('application/json')) {
      const text = await resp.data.text()
      const jsonData = JSON.parse(text)

      if (jsonData.data?.status === 'PENDING' || jsonData.data?.status === 'PROCESSING') {
        await new Promise(resolve => setTimeout(resolve, 1000))
        return poll()
      } else if (jsonData.data?.status === 'FAILED') {
        throw new Error(jsonData.message || 'Export task failed')
      } else {
        throw new Error('Unexpected task status')
      }
    } else {
      return resp
    }
  }

  return poll()
}

export function getEventSheets(eventId, params = {}) {
  return request.get(`/events/${eventId}/sheets/`, params)
}

export function getEventAdmins(eventId, params = {}) {
  return request.get(`/events/${eventId}/admins/`, params)
}

export function getEventMembers(eventId, params = {}) {
  return request.get(`/events/${eventId}/members/`, params)
}

export function exportEventMembers(eventId, params = {}) {
  return request.get(`/events/${eventId}/members/export/`, params, { responseType: 'blob' })
}

export function uploadEventAnnouncementImage(eventId, file, onProgress) {
  const form = new FormData()
  form.append('image', file)
  return request.upload(`/events/${eventId}/announcement/images/`, form, onProgress).finally(() => {
    invalidateEventCaches(eventId)
  })
}

export function deleteEventAnnouncementImage(eventId, imageId) {
  return request.delete(`/events/${eventId}/announcement/images/${imageId}/`).finally(() => {
    invalidateEventCaches(eventId)
  })
}
