<template>
  <aside class="sidebar" :class="{ open: isOpen, collapsed: !isOpen }" :aria-hidden="!isOpen">
    <div class="brand">
      <RouterLink class="brand-main" to="/dashboard" aria-label="TaCOS 主页">
        <img class="brand-logo" src="/icon.png" alt="" aria-hidden="true" />
        <span class="brand-copy">
          <span class="brand-name">TaCOS</span>
          <span class="brand-subtitle">清华合唱</span>
        </span>
        <span class="brand-version">v{{ appVersion }}</span>
      </RouterLink>
      <button
        v-if="isOpen"
        class="btn-modern ghost toggle-btn-in-sidebar"
        @click="$emit('toggle')"
        aria-label="收起侧边栏"
        style="border: none; padding: 5px 8px"
      >
        <i-lucide-panel-left-close class="icon" style="height: 20px; width: 20px" />
      </button>
    </div>

    <nav class="nav">
      <RouterLink class="nav-item" :class="isActive('/dashboard') && 'active'" to="/dashboard">
        <i-lucide-home class="icon" />
        <span>主页</span>
      </RouterLink>
      <RouterLink
        class="nav-item"
        :class="isActive('/personnel/members') && 'active'"
        to="/personnel/members"
      >
        <i-lucide-users class="icon" />
        <span>队员列表</span>
      </RouterLink>
      <RouterLink class="nav-item" :class="isActive('/sheets') && 'active'" to="/sheets">
        <i-lucide-file-text class="icon" />
        <span>乐谱</span>
      </RouterLink>
      <RouterLink
        v-if="isAdmin"
        class="nav-item"
        :class="isActive('/personnel/instructors') && 'active'"
        to="/personnel/instructors"
      >
        <i-lucide-graduation-cap class="icon" />
        <span>外请教师</span>
      </RouterLink>
      <RouterLink
        v-if="isAdmin"
        class="nav-item"
        :class="isActive('/titles') && 'active'"
        to="/titles"
      >
        <i-lucide-badge-check class="icon" />
        <span>称号管理</span>
      </RouterLink>
      <RouterLink class="nav-item" :class="isActive('/events') && 'active'" to="/events">
        <i-lucide-calendar class="icon" />
        <span>活动</span>
        <i-lucide-chevron-down class="icon caret" />
      </RouterLink>
      <div class="sub-nav" v-if="myOngoingEvents && myOngoingEvents.length > 0">
        <RouterLink
          v-for="ev in myOngoingEvents"
          :key="ev.id"
          class="sub-nav-item"
          :class="isActive(`/events/${ev.id}`) && 'active'"
          :to="`/events/${ev.id}`"
          :title="ev.name"
        >
          <span class="bullet" aria-hidden="true"></span>
          <span class="title">{{ ev.name }}</span>
        </RouterLink>
        <RouterLink class="sub-nav-item" to="/events">
          <span class="title">查看更多活动……</span>
        </RouterLink>
      </div>

      <div class="separator"></div>

      <button class="nav-item" @click="handleOpenPasteDialog">
        <i-lucide-clipboard-paste class="icon" />
        <span>粘贴分享链接</span>
      </button>
      <RouterLink class="nav-item" :class="isActive('/profile') && 'active'" to="/profile">
        <i-lucide-user class="icon" />
        <span>个人信息</span>
      </RouterLink>
      <button class="nav-item danger" @click="handleLogout">
        <i-lucide-log-out class="icon" />
        <span>退出账户</span>
      </button>
    </nav>
  </aside>
</template>

<script>
import { computed, ref, onMounted, watch, inject } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useStore } from 'vuex'
import { getEventList } from '@/api/events'
import {
  Home as LucideHome,
  Users as LucideUsers,
  FileText as LucideFileText,
  Calendar as LucideCalendar,
  ChevronDown as LucideChevronDown,
  GraduationCap as LucideGraduationCap,
  BadgeCheck as LucideBadgeCheck,
  User as LucideUser,
  LogOut as LucideLogOut,
  PanelLeftClose as LucidePanelLeftClose,
  ClipboardPaste as LucideClipboardPaste
} from 'lucide-vue-next'

export default {
  name: 'AppSidebar',
  components: {
    RouterLink,
    'i-lucide-home': LucideHome,
    'i-lucide-users': LucideUsers,
    'i-lucide-file-text': LucideFileText,
    'i-lucide-calendar': LucideCalendar,
    'i-lucide-chevron-down': LucideChevronDown,
    'i-lucide-graduation-cap': LucideGraduationCap,
    'i-lucide-badge-check': LucideBadgeCheck,
    'i-lucide-user': LucideUser,
    'i-lucide-log-out': LucideLogOut,
    'i-lucide-panel-left-close': LucidePanelLeftClose,
    'i-lucide-clipboard-paste': LucideClipboardPaste
  },
  props: {
    isOpen: { type: Boolean, default: true }
  },
  emits: ['toggle'],
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

    // 从父组件注入打开粘贴对话框的方法
    const openPasteDialog = inject('openPasteDialog', null)

    const handleOpenPasteDialog = () => {
      if (openPasteDialog) {
        openPasteDialog()
      }
    }

    const isAdmin = computed(
      () => store.getters['auth/isAdmin'] || store.getters['auth/isSuperAdmin']
    )
    const user = computed(() => store.getters['auth/user'])
    const appVersion = computed(() => store.getters['common/config']?.version || '')

    const isActive = pathPrefix => {
      return route.path === pathPrefix || route.path.startsWith(`${pathPrefix}/`)
    }

    const handleLogout = async () => {
      await store.dispatch('auth/logout')
      router.push('/login')
    }

    // ---- Events submenu (我的进行中活动) ----
    const myOngoingEvents = ref([])
    const myUserId = computed(() => user.value && user.value.user_id)

    const getTodayDateString = () => {
      const d = new Date()
      const yyyy = String(d.getFullYear())
      const mm = String(d.getMonth() + 1).padStart(2, '0')
      const dd = String(d.getDate()).padStart(2, '0')
      return `${yyyy}-${mm}-${dd}`
    }
    const isOngoing = row => {
      const today = getTodayDateString()
      const start = (row?.start_date || '').slice(0, 10)
      const end = (row?.end_date || '').slice(0, 10)
      if (!start || !end) {
        return true
      }
      if (start > today) {
        return false
      }
      if (end < today) {
        return false
      }
      return true
    }
    const belongsToMe = ev => ev && ev.relation && ev.relation !== 'not_member'
    const loadMyOngoing = async () => {
      const uid = myUserId.value
      if (!uid) {
        myOngoingEvents.value = []
        return
      }
      const aggregated = []
      let page = 1
      const pageSize = 200
      let total = Infinity
      try {
        while ((page - 1) * pageSize < total) {
          const res = await getEventList({ page, page_size: pageSize })
          const results = Array.isArray(res?.data?.results) ? res.data.results : []
          total = Number(res?.data?.count || 0)
          aggregated.push(...results)
          if (results.length < pageSize) {
            break
          }
          page += 1
          if (page > 50) {
            break
          }
        }
        const mineOngoing = aggregated
          .filter(ev => belongsToMe(ev) && isOngoing(ev))
          .sort((a, b) => String(b.start_date || '').localeCompare(String(a.start_date || '')))
        myOngoingEvents.value = mineOngoing.slice(0, 10)
      } catch {
        myOngoingEvents.value = []
      }
    }
    onMounted(loadMyOngoing)
    watch(myUserId, () => {
      loadMyOngoing()
    })

    return {
      isAdmin,
      appVersion,
      isActive,
      handleLogout,
      myOngoingEvents,
      handleOpenPasteDialog
    }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
  height: 100vh;
  border-right: 1px solid var(--border);
  background: var(--background);
  padding: 0;
  overflow-y: auto;
  overflow-x: hidden;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease;
  z-index: 30;
}

@media (min-width: 769px) {
  .sidebar:not(.open) {
    transform: translateX(-240px);
    border-right-color: transparent;
  }
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 58px;
  padding: 10px 12px 8px;
  margin-bottom: 8px;
}
.brand-main {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
  color: inherit;
  text-decoration: none;
}
.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: contain;
}
.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
}
.brand-name {
  overflow: hidden;
  color: var(--brand-700);
  font-size: 18px;
  font-weight: 750;
  line-height: 21px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.brand-subtitle {
  overflow: hidden;
  color: #6b7280;
  font-size: 12px;
  line-height: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.brand-version {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 7px;
  background: #fff;
  color: #6b7280;
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
}
.toggle-btn-in-sidebar {
  padding: 6px 8px;
  border-radius: 6px;
}
.toggle-btn-in-sidebar .icon {
  width: 16px;
  height: 16px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
}
.nav-item {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #374151;
  text-decoration: none;
  border: 1px solid transparent;
  font: inherit; /* 确保 button 继承字体样式 */
  background: transparent; /* 重置 button 默认背景 */
  cursor: pointer;
}
.sub-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 4px 0 6px 17px;
}
.sub-nav-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  color: #4b5563;
  text-decoration: none;
  border: 1px solid transparent;
  font-size: 13px;
  line-height: 18px;
}
.sub-nav-item .bullet {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--brand-700);
  opacity: 0.7;
}
.sub-nav-item:hover {
  background: var(--muted);
  border-color: var(--border);
}
.sub-nav-item.active {
  background: rgba(154, 86, 181, 0.08);
  border-color: var(--border);
  color: #111827;
}
.brand-main:focus:not(:focus-visible),
.nav-item:focus:not(:focus-visible),
.sub-nav-item:focus:not(:focus-visible),
.toggle-btn-in-sidebar:focus:not(:focus-visible) {
  outline: none;
  box-shadow: none;
}
.brand-main:focus-visible,
.nav-item:focus-visible {
  outline: 2px solid var(--brand-500);
  outline-offset: 2px;
  box-shadow: none;
}
.sub-nav-item:focus-visible {
  outline: 1px solid var(--brand-500);
  outline-offset: 1px;
  box-shadow: none;
}
.toggle-btn-in-sidebar:focus-visible {
  outline: 2px solid var(--brand-500);
  outline-offset: 2px;
  box-shadow: none;
}
.nav-item span {
  white-space: nowrap;
  transition: opacity 0.12s ease;
}
.nav-item .icon {
  width: 18px;
  height: 18px;
  color: var(--brand-700);
  opacity: 0.9;
}
.nav-item .caret {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}
.nav-item:hover {
  background: var(--muted);
  border-color: var(--border);
}
.nav-item.active {
  background: rgba(154, 86, 181, 0.08);
  border-color: var(--border);
  color: #111827;
}
.nav-item.danger {
  color: #7f1d1d;
}
.nav-item.danger .icon {
  color: #7f1d1d;
}

.sidebar.collapsed .brand-copy,
.sidebar.collapsed .brand-version,
.sidebar.collapsed .nav-item span {
  opacity: 0;
}
.sidebar.collapsed .sub-nav-item .title {
  opacity: 0;
}

.separator {
  height: 1px;
  background: var(--border);
  margin: 8px 4px;
}

@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    z-index: 50;
  }
  .sidebar.open {
    transform: translateX(0);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  }
}
</style>
