<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div>
        <h1 class="dashboard-title">TaCOS 主页</h1>
        <p class="dashboard-subtitle">欢迎使用清华合唱队在线系统</p>
      </div>
    </div>

    <div class="section-grid">
      <div class="card announcements-card">
        <div class="card-content">
          <div class="card-header announcements-header">
            <h2>公告广播</h2>
          </div>
          <button
            class="btn-modern ghost sm-btn ann-manage-btn"
            v-if="isAdmin"
            @click="navigateTo('/announcements')"
          >
            <i-lucide-settings class="mr" />
            <div class="ann-manage-btn-text" style="font-weight: bold">管理公告</div>
          </button>
          <div class="divider" />
          <div class="announcements">
            <div v-if="announcements.length === 0" class="announcement-item">
              <div class="announcement-content">暂无公告</div>
            </div>
            <div v-for="item in announcements" :key="item.id" class="announcement-item">
              <div class="announcement-date">{{ formatDateTime(item.publish_time) }}</div>
              <div class="announcement-content">
                <strong v-if="item.title" class="announcement-title">{{ item.title }}</strong>
              </div>
              <div class="announcement-content">{{ item.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-grid">
      <div class="card card-clickable flat" @click="navigateTo('/personnel/members')">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-user />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.totalMembers }}</div>
            <div class="stat-label" style="font-size: 14px; font-weight: bold">总队员数</div>
          </div>
        </div>
      </div>

      <div class="card card-clickable flat" @click="navigateTo('/sheets')">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-file-text />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.totalSheets }}</div>
            <div class="stat-label" style="font-size: 14px; font-weight: bold">我的乐谱</div>
          </div>
        </div>
      </div>

      <div class="card card-clickable flat" @click="navigateTo('/events')">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-calendar />
          </div>
          <div class="stat-info">
            <div class="stat-number">
              {{ stats.totalMyEvents }}
              <span style="font-size: 0.7em">/ {{ stats.totalEvents }}</span>
            </div>
            <div class="stat-label" style="font-size: 14px; font-weight: bold">参与活动</div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-grid">
      <div class="card" v-if="isAdmin">
        <div class="card-content">
          <div class="card-header">
            <h3>管理员选项</h3>
          </div>
          <div class="divider" />
          <div class="admin-actions">
            <button
              class="btn-modern ghost big-btn"
              @click="navigateTo('/personnel/instructors')"
              style="margin-right: 12px"
            >
              <i-lucide-graduation-cap class="btn-icon" />
              <span>查看教师列表</span>
            </button>
            <button
              class="btn-modern ghost big-btn"
              @click="navigateTo('/titles')"
              style="margin-right: 12px"
            >
              <i-lucide-badge-check class="btn-icon" />
              <span>称号管理</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    <SiteFooter />
  </div>
</template>

<script>
import { computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { getMemberStats } from '@/api/personnel'
import { getAnnouncements } from '@/api/common'
import { formatDateTime } from '@/utils/format'
import { getSheetList } from '@/api/sheets'
import { getEventList } from '@/api/events'
import SiteFooter from '@/components/common/SiteFooter.vue'
import {
  User as LucideUser,
  FileText as LucideFileText,
  Calendar as LucideCalendar,
  Settings as LucideSettings,
  GraduationCap as LucideGraduationCap,
  BadgeCheck as LucideBadgeCheck
} from 'lucide-vue-next'

export default {
  name: 'Dashboard',
  components: {
    'i-lucide-user': LucideUser,
    'i-lucide-file-text': LucideFileText,
    'i-lucide-calendar': LucideCalendar,
    'i-lucide-settings': LucideSettings,
    'i-lucide-graduation-cap': LucideGraduationCap,
    'i-lucide-badge-check': LucideBadgeCheck,
    SiteFooter
  },
  setup() {
    const router = useRouter()
    const store = useStore()

    const stats = reactive({
      totalMembers: 0,
      totalSheets: 0,
      totalMyEvents: 0,
      totalEvents: 0
    })
    const announcements = reactive([])

    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const isSuperAdmin = computed(() => store.getters['auth/isSuperAdmin'])
    const userName = computed(
      () => store.getters['auth/user']?.name || store.getters['auth/user']?.user_id || '用户'
    )

    const navigateTo = path => {
      router.push(path)
    }

    const myUserId = computed(() => store.getters['auth/user']?.user_id || '')

    const fetchEventStats = async () => {
      if (!myUserId.value) {
        return { totalEvents: 0, totalMyEvents: 0 }
      }
      let page = 1
      const pageSize = 200
      let total = Infinity
      let myCount = 0
      while ((page - 1) * pageSize < total) {
        const res = await getEventList({ page, page_size: pageSize })
        const results = Array.isArray(res.data?.results) ? res.data.results : []
        total = Number(res.data?.count || 0)
        myCount += results.filter(
          ev => ev?.relation === 'member' || ev?.relation === 'event_admin'
        ).length
        if (results.length < pageSize) {
          break
        }
        page += 1
        if (page > 50) {
          break
        }
      }
      return { totalEvents: Number.isFinite(total) ? total : 0, totalMyEvents: myCount }
    }

    const loadDashboardData = async () => {
      try {
        // 成员总数（只取 count，减少数据量）
        const membersRes = await getMemberStats()
        stats.totalMembers = membersRes.data?.total_members ?? 'NaN'

        // 我的乐谱总数
        const sheetsRes = await getSheetList({ page_size: 1 })
        stats.totalSheets = sheetsRes.data?.count ?? 'NaN'

        // 活动总数和我参与/管理的活动数共用一次分页扫描
        const eventStats = await fetchEventStats()
        stats.totalMyEvents = eventStats.totalMyEvents
        stats.totalEvents = eventStats.totalEvents

        // 公告（公开读取，无需鉴权）
        const annRes = await getAnnouncements({ page_size: 5 })
        const items = annRes.data?.results || []
        announcements.splice(0, announcements.length, ...items)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      }
    }

    onMounted(() => {
      loadDashboardData()
    })

    const handleUserCommand = command => {
      if (command === 'profile') {
        router.push('/profile')
      } else if (command === 'logout') {
        handleLogout()
      }
    }

    const handleLogout = async () => {
      await store.dispatch('auth/logout')
      router.push('/login')
    }

    return {
      stats,
      announcements,
      isAdmin,
      isSuperAdmin,
      navigateTo,
      userName,
      formatDateTime,
      handleUserCommand,
      handleLogout
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;

  .dashboard-header {
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;

    .dashboard-title {
      font-size: 2rem;
      color: #303133;
      margin-bottom: 8px;
    }

    .dashboard-subtitle {
      color: #909399;
      font-size: 1.1rem;
    }
  }

  .section-grid {
    display: grid;
    grid-template-columns: repeat(12, minmax(0, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }
  .section-grid > * {
    grid-column: span 12;
  }

  .content-card {
    height: auto;

    .admin-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .btn-icon {
      width: 18px;
      height: 18px;
    }
  }

  .announcements-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .announcements {
    .announcement-item {
      padding: 10px 0;
      margin-bottom: 8px;

      &:last-child {
        border-bottom: none;
        margin-bottom: 0;
      }

      .announcement-date {
        font-size: 11px;
        color: #9ca3af;
        margin-bottom: 8px;
        font-weight: 400;
        letter-spacing: 0.3px;
        opacity: 0.85;
      }

      .announcement-title {
        color: #111827;
        font-size: 16px;
        font-weight: bold;
        line-height: 2;
      }

      .announcement-content {
        color: #7a7e84;
        font-size: 14px;
        font-weight: 400;
        line-height: 1.65;
      }
    }
  }

  .announcements-card {
    position: relative;
  }
  .ann-manage-btn {
    position: absolute;
    top: 20px;
    right: 25px;
  }

  @media (min-width: 1024px) {
    .section-grid > * {
      grid-column: span 12;
    }
  }

  .stat-content {
    display: flex;
    align-items: center;
  }
  .stat-icon {
    font-size: 18px;
    color: $primary-color;
    margin-right: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: rgba(154, 86, 181, 0.1);
  }
  .stat-info {
    display: inline-flex;
    align-items: baseline;
    gap: 8px;
  }
  .stat-number {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
    line-height: 1;
  }
  .stat-label {
    color: #6b7280;
    font-size: 0.9rem;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;

    .dashboard-header {
      display: block;

      .header-right {
        justify-content: center;
        margin-top: 12px; // 移动端标题下方留出间距
      }

      .dashboard-title {
        font-size: 1.5rem;
      }

      .dashboard-subtitle {
        font-size: 1rem;
      }
    }

    .content-card {
      height: auto;
      margin-bottom: 20px;
    }
  }
}
</style>
