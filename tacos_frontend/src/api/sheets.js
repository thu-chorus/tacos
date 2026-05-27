import { request } from './index'

// 获取乐谱列表
export function getSheetList(params) {
  return request.get('/sheets/', params)
}

// 获取乐谱详情
export function getSheetDetail(sheetId) {
  return request.get(`/sheets/${sheetId}/`)
}

// 上传乐谱
export function uploadSheet(file, metadata, onProgress) {
  const formData = new FormData()
  formData.append('original_file', file)

  // 添加元数据
  Object.keys(metadata).forEach(key => {
    const val = metadata[key]
    if (Array.isArray(val)) {
      val.forEach(v => formData.append(key, v))
    } else if (val !== undefined && val !== null) {
      formData.append(key, val)
    }
  })

  return request.upload('/sheets/', formData, onProgress)
}

// 更新乐谱信息
export function updateSheet(sheetId, data) {
  return request.put(`/sheets/${sheetId}/`, data)
}

// 删除乐谱
export function deleteSheet(sheetId) {
  return request.delete(`/sheets/${sheetId}/`)
}

// 发起异步下载/预览任务（返回task_id）
export function initiateDownload(sheetId, options = {}) {
  const params = options.preview ? { preview: 'true' } : {}
  return request.post(`/sheets/${sheetId}/download/`, {}, { params })
}

// 轮询下载任务状态或获取结果
// 如果任务完成，返回blob；否则返回JSON状态
export function getDownloadTask(taskId, isPreview = false) {
  const params = isPreview ? { preview: 'true' } : {}
  return request.get(`/sheets/task/${taskId}/`, params, { responseType: 'blob' })
}

// 只轮询任务状态，不下载 PDF blob
export function getDownloadTaskStatus(taskId) {
  return request.get(`/sheets/task/${taskId}/`, { status_only: 'true' })
}

// 向后兼容的下载函数 - 自动处理异步轮询
// 返回一个 Promise，resolve 时返回与旧 API 兼容的响应格式
export async function downloadSheet(sheetId) {
  // 发起下载任务
  const initResp = await initiateDownload(sheetId)
  const taskId = initResp.data?.task_id

  if (!taskId) {
    throw new Error('Failed to get task ID')
  }

  // 轮询直到完成
  const poll = async () => {
    const resp = await getDownloadTask(taskId, false)
    const contentType = resp.headers['content-type'] || resp.headers['Content-Type']

    if (contentType && contentType.includes('application/json')) {
      // 仍在处理中，解析状态
      const text = await resp.data.text()
      const jsonData = JSON.parse(text)

      if (jsonData.data?.status === 'PENDING' || jsonData.data?.status === 'PROCESSING') {
        // 等待 1 秒后重试
        await new Promise(resolve => setTimeout(resolve, 1000))
        return poll()
      } else if (jsonData.data?.status === 'FAILED') {
        throw new Error(jsonData.message || 'Task failed')
      } else {
        throw new Error('Unexpected task status')
      }
    } else {
      // 完成，返回 blob 响应
      return resp
    }
  }

  return poll()
}
