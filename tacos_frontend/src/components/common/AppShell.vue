<template>
  <div class="app-shell" :class="{ 'sidebar-open': sidebarOpen }">
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="toggleSidebar" />
    <AppSidebar :isOpen="sidebarOpen" @toggle="toggleSidebar" />
    <main class="app-content">
      <header class="topbar">
        <div class="topbar-left">
          <button
            v-if="!sidebarOpen"
            class="btn-modern ghost toggle-btn"
            style="border: none; padding: 5px 8px"
            @click="toggleSidebar"
          >
            <i-lucide-panel-left class="icon" style="height: 20px; width: 20px" />
          </button>
          <button
            v-if="showBackButton"
            class="btn-modern ghost back-btn"
            style="border: none; padding: 3px 6px"
            @click="handleBack"
            :aria-label="'返回'"
          >
            <i-lucide-chevron-left class="icon" style="width: 24px; height: 24px" />
          </button>
        </div>
        <h1 class="page-title"><slot name="title" /></h1>
        <div class="spacer"></div>
        <div class="topbar-right">
          <button
            v-if="canShare"
            class="btn-modern ghost share-btn"
            style="border: none; padding: 5px 8px"
            @click="handleShare"
            :aria-label="'分享'"
            title="分享此页面"
          >
            <i-lucide-share class="icon" style="height: 18px; width: 18px" />
          </button>
        </div>
      </header>
      <section class="page-body">
        <slot />
      </section>
    </main>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import AppSidebar from './AppSidebar.vue'
import {
  PanelLeft as LucidePanelLeft,
  ChevronLeft as LucideChevronLeft,
  Share as LucideShare
} from 'lucide-vue-next'
import { shouldShowShareButton, doShare, getDefaultPageInfo } from '@/utils/share'

export default {
  name: 'AppShell',
  components: {
    AppSidebar,
    'i-lucide-panel-left': LucidePanelLeft,
    'i-lucide-chevron-left': LucideChevronLeft,
    'i-lucide-share': LucideShare
  },
  props: {
    showBackButton: {
      type: Boolean,
      default: false
    },
    backTo: {
      type: String,
      default: ''
    }
  },
  emits: ['back'],
  setup(props, { emit }) {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const sidebarOpen = ref(true)

    const toggleSidebar = () => {
      sidebarOpen.value = !sidebarOpen.value
    }

    const handleBack = () => {
      emit('back')

      // 优先从 URL query 参数 ref 获取返回目标
      const refParam = route.query.ref
      if (refParam) {
        router.push(decodeURIComponent(refParam))
      } else if (props.backTo) {
        // 其次使用 props 中的 backTo（来自路由 meta）
        router.push(props.backTo)
      } else {
        // 最后使用浏览器返回
        router.back()
      }
    }

    // 分享功能
    const canShare = computed(() => {
      // 检查路由是否允许分享
      if (!shouldShowShareButton(route)) {
        return false
      }
      // 检查 store 中是否禁用了分享
      return store.getters['common/shareEnabled']
    })

    const handleShare = async () => {
      // 获取用户名
      const user = store.getters['auth/user']
      const userName = user?.name || user?.user_id || '有人'

      // 获取页面信息：优先使用 store 中的自定义信息，其次使用路由 meta
      const customPageInfo = store.getters['common/sharePageInfo']
      const pageInfo = customPageInfo || getDefaultPageInfo(route)

      await doShare(userName, pageInfo)
    }

    return { sidebarOpen, toggleSidebar, handleBack, canShare, handleShare }
  }
}
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}
.app-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  width: 100%;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 50px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  background: var(--background);
  position: sticky;
  top: 0;
  z-index: 10;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.spacer {
  flex: 1;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.share-btn {
  padding: 6px 12px;
  border-radius: 6px;
  color: #374151;
  gap: 6px;
  border-color: var(--border);
  background: transparent;
  transition:
    color 120ms ease,
    background 150ms ease;
}
.share-btn:hover {
  background: #f3f4f6;
}
.share-btn:active {
  transform: scale(0.95);
}
.share-btn .icon {
  width: 18px;
  height: 18px;
}
.page-body {
  padding: 16px;
  flex: 1;
}
.toggle-btn {
  padding: 6px 8px;
  border-radius: 6px;
}
.toggle-btn .icon {
  width: 16px;
  height: 16px;
}
.back-btn {
  padding: 6px 12px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-color: var(--border);
  background: transparent;
  color: #374151;
  transition:
    transform 120ms ease,
    background 150ms ease;
}
.back-btn:hover {
  background: #f3f4f6;
}
.back-btn:active {
  transform: translateY(1px) scale(0.98);
}
.back-btn .icon {
  width: 16px;
  height: 16px;
}
.back-text {
  font-size: 14px;
}

@media (max-width: 768px) {
  .back-text {
    display: none;
  }
  .back-btn {
    padding: 6px 8px;
  }
}

@media (min-width: 769px) {
  .app-shell.sidebar-open .app-content {
    margin-left: 240px;
  }
}

@media (max-width: 768px) {
  .app-content {
    margin-left: 0 !important;
  }
}

.sidebar-backdrop {
  display: none;
}

@media (max-width: 768px) {
  .sidebar-backdrop {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 40;
    animation: fadeIn 0.2s ease;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
