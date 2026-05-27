<template>
  <div id="app">
    <AppShell v-if="useShell" :show-back-button="showBackButton" :back-to="backTo">
      <template #title />
      <router-view />
    </AppShell>
    <router-view v-else />
    <Toaster theme="light" position="top-center" rich-colors />

    <!-- 分享链接检测对话框 -->
    <div
      v-if="shareDetection.visible"
      class="share-detection-overlay"
      @click.self="dismissShareDetection"
    >
      <div class="share-detection-dialog">
        <div class="share-detection-header">
          <div class="share-detection-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="18" cy="5" r="3"></circle>
              <circle cx="6" cy="12" r="3"></circle>
              <circle cx="18" cy="19" r="3"></circle>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
          </div>
          <h3>发现分享链接</h3>
        </div>
        <div class="share-detection-body">
          <p v-if="shareDetection.sharer">
            <strong>{{ shareDetection.sharer }}</strong> 分享了
            <strong>{{ shareDetection.pageInfo || '一个页面' }}</strong> 给你
          </p>
          <p v-else>检测到剪贴板中有 TaCOS 页面链接</p>
          <p class="share-detection-question">
            {{ shareDetection.isCheckinShare ? '是否立即签到？' : '是否立即访问？' }}
          </p>
        </div>
        <div class="share-detection-footer">
          <button class="btn-modern ghost" @click="dismissShareDetection">忽略</button>
          <button class="btn-modern primary" @click="navigateToSharedUrl">
            {{ shareDetection.isCheckinShare ? '前往签到' : '立即访问' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 手动粘贴分享链接对话框（移动端友好） -->
    <div v-if="pasteDialog.visible" class="share-detection-overlay" @click.self="closePasteDialog">
      <div class="share-detection-dialog paste-dialog">
        <div class="share-detection-header">
          <div class="share-detection-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <rect width="8" height="4" x="8" y="2" rx="1" ry="1"></rect>
              <path
                d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"
              ></path>
            </svg>
          </div>
          <h3>粘贴分享链接</h3>
        </div>
        <div class="share-detection-body">
          <p class="paste-hint">请将分享内容粘贴到下方输入框中：</p>
          <textarea
            ref="pasteTextarea"
            v-model="pasteDialog.content"
            class="paste-textarea"
            placeholder="在此粘贴分享内容..."
            rows="4"
            @paste="handlePasteEvent"
          ></textarea>
          <p v-if="pasteDialog.error" class="paste-error">{{ pasteDialog.error }}</p>
          <p v-if="pasteDialog.parsed" class="paste-success">
            检测到：<strong>{{ pasteDialog.parsed.sharer || '有人' }}</strong> 分享的
            <strong>{{ pasteDialog.parsed.pageInfo || '页面' }}</strong>
          </p>
        </div>
        <div class="share-detection-footer">
          <button class="btn-modern ghost" @click="closePasteDialog">取消</button>
          <button
            class="btn-modern primary"
            @click="confirmPasteNavigation"
            :disabled="!pasteDialog.parsed"
          >
            前往
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Toaster } from 'vue-sonner'
import { computed, ref, onMounted, onUnmounted, watch, provide } from 'vue'
import AppShell from '@/components/common/AppShell.vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { readFromClipboard, parseShareText, parseCheckinShareText, getBaseUrl } from '@/utils/share'

export default {
  name: 'App',
  components: { Toaster, AppShell },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()

    const useShell = computed(() => !route.meta.noSidebar)
    const showBackButton = computed(() => route.meta.showBackButton || false)

    // 使用路由 meta 的 backTo 作为默认返回目标（URL ref 参数优先级在 AppShell 中处理）
    const backTo = computed(() => route.meta.backTo || '')

    // 分享链接检测状态
    const shareDetection = ref({
      visible: false,
      url: '',
      sharer: '',
      pageInfo: ''
    })

    // 已处理过的剪贴板内容，避免重复提示
    const processedClipboardContent = ref('')

    // 手动粘贴对话框状态
    const pasteDialog = ref({
      visible: false,
      content: '',
      error: '',
      parsed: null
    })
    const pasteTextarea = ref(null)

    // 检测剪贴板中的分享链接
    const checkClipboardForShare = async () => {
      // 只在用户已登录时检测
      const isLoggedIn = store.getters['auth/isLoggedIn']
      if (!isLoggedIn) {
        return
      }

      try {
        const clipboardText = await readFromClipboard()
        if (!clipboardText) {
          return
        }

        // 如果剪贴板内容已经处理过，跳过
        if (clipboardText === processedClipboardContent.value) {
          return
        }

        // 首先尝试解析签到分享链接
        const checkinShareInfo = parseCheckinShareText(clipboardText)
        if (checkinShareInfo) {
          // 检查是否是当前页面的URL
          const currentUrl = window.location.href
          const baseUrl = getBaseUrl()
          const currentPath = currentUrl.replace(baseUrl, '')
          const sharePath = checkinShareInfo.url.replace(baseUrl, '')

          if (currentPath === sharePath) {
            processedClipboardContent.value = clipboardText
            return
          }

          // 显示签到分享确认对话框
          shareDetection.value = {
            visible: true,
            url: checkinShareInfo.url,
            sharer: checkinShareInfo.sharer,
            pageInfo: `「${checkinShareInfo.eventName}」的签到「${checkinShareInfo.sessionName}」`,
            isCheckinShare: true
          }
          processedClipboardContent.value = clipboardText
          return
        }

        // 尝试解析普通分享链接
        const shareInfo = parseShareText(clipboardText)
        if (shareInfo) {
          // 检查是否是当前页面的URL，如果是则不提示
          const currentUrl = window.location.href
          const baseUrl = getBaseUrl()
          const currentPath = currentUrl.replace(baseUrl, '')
          const sharePath = shareInfo.url.replace(baseUrl, '')

          // 比较路径（忽略query参数）
          const currentPathname = currentPath.split('?')[0]
          const sharePathname = sharePath.split('?')[0]

          if (currentPathname === sharePathname) {
            processedClipboardContent.value = clipboardText
            return
          }

          // 显示确认对话框
          shareDetection.value = {
            visible: true,
            url: shareInfo.url,
            sharer: shareInfo.sharer,
            pageInfo: shareInfo.pageInfo,
            isCheckinShare: false
          }
          processedClipboardContent.value = clipboardText
        }
      } catch (error) {
        // 剪贴板读取失败（用户可能拒绝权限），静默处理
      }
    }

    // 忽略分享提示
    const dismissShareDetection = () => {
      shareDetection.value.visible = false
    }

    // 跳转到分享的URL
    const navigateToSharedUrl = () => {
      const url = shareDetection.value.url
      shareDetection.value.visible = false

      if (url) {
        const baseUrl = getBaseUrl()
        if (url.startsWith(baseUrl)) {
          // 内部链接，使用 router 跳转
          const path = url.replace(baseUrl, '')
          router.push(path)
        } else {
          // 外部链接（理论上不应该发生）
          window.location.href = url
        }
      }
    }

    // 定时检测剪贴板
    let clipboardCheckInterval = null

    onMounted(() => {
      // 初始检测
      setTimeout(checkClipboardForShare, 1000)

      // 每次窗口获得焦点时检测
      window.addEventListener('focus', checkClipboardForShare)

      // 定期检测（每30秒），作为备用方案
      clipboardCheckInterval = setInterval(checkClipboardForShare, 30000)
    })

    onUnmounted(() => {
      window.removeEventListener('focus', checkClipboardForShare)
      if (clipboardCheckInterval) {
        clearInterval(clipboardCheckInterval)
      }
    })

    // 路由变化时重置分享状态
    watch(
      () => route.fullPath,
      () => {
        store.dispatch('common/resetShareState')
      }
    )

    // 监听登录状态变化，用户登录时立即检测剪贴板
    watch(
      () => store.getters['auth/isLoggedIn'],
      (isLoggedIn, wasLoggedIn) => {
        if (isLoggedIn && !wasLoggedIn) {
          // 用户刚刚登录，延迟一小段时间后检测剪贴板（等待路由跳转完成）
          setTimeout(checkClipboardForShare, 500)
        }
      }
    )

    // ========== 手动粘贴功能 ==========

    // 打开手动粘贴对话框
    const openPasteDialog = () => {
      pasteDialog.value = {
        visible: true,
        content: '',
        error: '',
        parsed: null
      }
      // 自动聚焦输入框
      setTimeout(() => {
        pasteTextarea.value?.focus()
      }, 100)
    }

    // 关闭手动粘贴对话框
    const closePasteDialog = () => {
      pasteDialog.value.visible = false
      pasteDialog.value.content = ''
      pasteDialog.value.error = ''
      pasteDialog.value.parsed = null
    }

    // 处理粘贴事件
    const handlePasteEvent = () => {
      // 延迟一帧让 v-model 更新
      setTimeout(() => {
        parsePastedContent()
      }, 0)
    }

    // 解析粘贴的内容
    const parsePastedContent = () => {
      const text = pasteDialog.value.content.trim()
      if (!text) {
        pasteDialog.value.error = ''
        pasteDialog.value.parsed = null
        return
      }

      // 尝试解析签到分享
      const checkinInfo = parseCheckinShareText(text)
      if (checkinInfo) {
        pasteDialog.value.error = ''
        pasteDialog.value.parsed = {
          url: checkinInfo.url,
          sharer: checkinInfo.sharer,
          pageInfo: `「${checkinInfo.eventName}」的签到「${checkinInfo.sessionName}」`,
          isCheckinShare: true
        }
        return
      }

      // 尝试解析普通分享
      const shareInfo = parseShareText(text)
      if (shareInfo) {
        pasteDialog.value.error = ''
        pasteDialog.value.parsed = {
          url: shareInfo.url,
          sharer: shareInfo.sharer,
          pageInfo: shareInfo.pageInfo || '一个页面',
          isCheckinShare: false
        }
        return
      }

      // 检查是否包含 TaCOS URL
      const baseUrl = getBaseUrl()
      const urlMatch = text.match(
        new RegExp(`(${baseUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^\\s,，]*)`)
      )
      if (urlMatch) {
        pasteDialog.value.error = ''
        pasteDialog.value.parsed = {
          url: urlMatch[1],
          sharer: '',
          pageInfo: '一个页面',
          isCheckinShare: false
        }
        return
      }

      pasteDialog.value.error = '未检测到有效的 TaCOS 分享链接'
      pasteDialog.value.parsed = null
    }

    // 监听输入内容变化
    watch(
      () => pasteDialog.value.content,
      () => {
        parsePastedContent()
      }
    )

    // 确认跳转
    const confirmPasteNavigation = () => {
      const parsed = pasteDialog.value.parsed
      if (!parsed || !parsed.url) {
        return
      }

      closePasteDialog()

      const baseUrl = getBaseUrl()
      if (parsed.url.startsWith(baseUrl)) {
        const path = parsed.url.replace(baseUrl, '')
        router.push(path)
      } else {
        window.location.href = parsed.url
      }
    }

    // 提供给子组件调用的方法
    provide('openPasteDialog', openPasteDialog)

    return {
      useShell,
      showBackButton,
      backTo,
      shareDetection,
      dismissShareDetection,
      navigateToSharedUrl,
      pasteDialog,
      pasteTextarea,
      openPasteDialog,
      closePasteDialog,
      handlePasteEvent,
      confirmPasteNavigation
    }
  }
}
</script>

<style lang="scss">
#app {
  font-family:
    'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑',
    Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
  width: 100vw;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  width: 100%;
}

/* 分享链接检测对话框样式 */
.share-detection-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

.share-detection-dialog {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 90%;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

.share-detection-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 12px;
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.share-detection-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-500, #9a56b5) 0%, var(--brand-600, #7c3aed) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.share-detection-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.share-detection-body {
  padding: 16px 20px;
}

.share-detection-body p {
  margin: 0 0 8px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
}

.share-detection-body strong {
  color: #111827;
}

.share-detection-question {
  margin-top: 12px !important;
  font-weight: 500;
  color: #374151 !important;
}

.share-detection-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border, #e5e7eb);
  justify-content: flex-end;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 手动粘贴对话框样式 */
.paste-dialog {
  max-width: 440px;
}

.paste-hint {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px !important;
}

.paste-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.paste-textarea:focus {
  outline: none;
  border-color: var(--brand-500, #9a56b5);
  box-shadow: 0 0 0 3px rgba(154, 86, 181, 0.1);
}

.paste-textarea::placeholder {
  color: #9ca3af;
}

.paste-error {
  margin-top: 8px !important;
  font-size: 13px;
  color: #dc2626;
}

.paste-success {
  margin-top: 8px !important;
  font-size: 13px;
  color: #059669;
  padding: 8px 12px;
  background: #ecfdf5;
  border-radius: 6px;
}

.paste-success strong {
  color: #047857;
}
</style>
