import { request } from './index'

// 健康检查（后端 /api/v1/common/health/）
export function healthCheck() {
  return request.get('/common/health/')
}

export function getAnnouncements(params = {}) {
  return request.get('/common/announcements/', params)
}

export function createAnnouncement(data) {
  return request.post('/common/announcements/', data)
}

export function updateAnnouncement(id, data) {
  return request.put(`/common/announcements/${id}/`, data)
}

export function deleteAnnouncement(id) {
  return request.delete(`/common/announcements/${id}/`)
}
