// 文件下载工具

/**
 * 下载文件
 * @param {Blob} blob 文件blob
 * @param {string} filename 文件名
 */
export function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  // 释放URL对象
  window.URL.revokeObjectURL(url)
}

/**
 * 下载PDF文件
 * @param {Blob} blob PDF文件blob
 * @param {string} filename 文件名
 */
export function downloadPDF(blob, filename) {
  if (!filename.endsWith('.pdf')) {
    filename += '.pdf'
  }
  downloadFile(blob, filename)
}

/**
 * 从响应头获取文件名
 * @param {string} contentDisposition Content-Disposition响应头
 * @returns {string} 文件名
 */
export function getFilenameFromContentDisposition(contentDisposition) {
  if (!contentDisposition) {
    return 'download'
  }

  const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
  if (filenameMatch && filenameMatch[1]) {
    return filenameMatch[1].replace(/['"]/g, '')
  }

  const filenameStarMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
  if (filenameStarMatch && filenameStarMatch[1]) {
    return decodeURIComponent(filenameStarMatch[1])
  }

  return 'download'
}

/**
 * 下载乐谱文件
 * @param {number} sheetId 乐谱ID
 * @param {string} title 乐谱标题
 * @param {function} downloadAPI 下载API函数
 */
export async function downloadSheet(sheetId, title, downloadAPI) {
  try {
    const response = await downloadAPI(sheetId)

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = getFilenameFromContentDisposition(contentDisposition)

    // 如果没有从响应头获取到文件名，使用标题
    if (filename === 'download') {
      try {
        const { default: dayjs } = await import('dayjs')
        filename = `${title}_${dayjs.tz().format('YYYY-MM-DD')}.pdf`
      } catch {
        filename = `${title}_${new Date().toISOString().slice(0, 10)}.pdf`
      }
    }

    downloadPDF(response.data, filename)
    return true
  } catch (error) {
    console.error('Download failed:', error)
    throw error
  }
}

/**
 * 批量下载文件
 * @param {Array} files 文件列表
 * @param {function} downloadAPI 下载API函数
 * @param {function} onProgress 进度回调
 */
export async function batchDownload(files, downloadAPI, onProgress) {
  const total = files.length
  let completed = 0

  for (const file of files) {
    try {
      await downloadSheet(file.id, file.title, downloadAPI)
      completed++

      if (onProgress) {
        onProgress({
          completed,
          total,
          percentage: Math.round((completed / total) * 100)
        })
      }

      // 添加延迟避免请求过于频繁
      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (error) {
      console.error(`Download failed for file ${file.title}:`, error)
    }
  }
}
