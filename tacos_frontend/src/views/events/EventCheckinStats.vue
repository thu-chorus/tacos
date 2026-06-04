<template>
  <div class="page-container">
    <div v-if="!pageLoaded" class="card">
      <div class="card-content">
        <PageLoading />
      </div>
    </div>

    <template v-else>
      <div class="card">
        <div class="card-content" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 16px">
            <h3>{{ session.name || '签到详情' }}</h3>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <div class="label">签到情况</div>
              <div class="value">
                <span style="font-weight: 600; font-size: 15px"
                  >{{ checkedInCount }} / {{ totalMemberCount }}</span
                >
                <span style="margin-left: 8px; color: #6b7280; font-size: 13px"
                  >（不含非成员管理员）</span
                >
              </div>
            </div>
            <div class="info-item">
              <div class="label">签到类型</div>
              <div class="value">
                <el-tag :type="getSessionTypeTag(session.type)">{{
                  getCheckinTypeLabel(session.type)
                }}</el-tag>
              </div>
            </div>
            <div class="info-item">
              <div class="label">状态</div>
              <div class="value">
                <el-tag :type="session.is_active ? 'success' : 'info'">{{
                  session.is_active ? '进行中' : '已结束'
                }}</el-tag>
              </div>
            </div>
            <div class="info-item">
              <div class="label">开始时间</div>
              <div class="value">{{ formatDateTime(session.started_at) }}</div>
            </div>
            <div class="info-item">
              <div class="label">结束时间</div>
              <div class="value">{{ formatDateTime(session.ended_at) || '未结束' }}</div>
            </div>
            <div
              class="info-item"
              v-if="session.type === 'LOCATION' && session.location_lat && session.location_lng"
            >
              <div class="label">位置</div>
              <div class="value">
                {{ session.location_lat }}, {{ session.location_lng }} (半径
                {{ session.radius_m || 500 }}m)
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-content" style="padding: 10px 15px">
          <div class="header" style="margin-bottom: 16px">
            <h3>签到记录</h3>
            <div class="actions">
              <button class="btn-modern success sm-btn" @click="exportCsv">
                <i-lucide-download class="btn-icon" />
                <span>导出签到记录</span>
              </button>
            </div>
          </div>

          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th style="min-width: 100px">姓名</th>
                  <th style="min-width: 100px">学号</th>
                  <th style="min-width: 60px">声部</th>
                  <th style="min-width: 60px">梯队</th>
                  <th style="min-width: 90px">签到情况</th>
                  <th style="min-width: 160px">签到时间</th>
                  <th v-if="session.type === 'LOCATION'" style="min-width: 100px">纬度</th>
                  <th v-if="session.type === 'LOCATION'" style="min-width: 100px">经度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="paginatedRecords.length === 0">
                  <td :colspan="columnCount" class="empty-cell">暂无数据</td>
                </tr>
                <tr v-for="row in paginatedRecords" :key="row.id || row.member_id">
                  <td>
                    <el-link type="primary" @click="goMember(row)">{{
                      row.member_name || '-'
                    }}</el-link>
                  </td>
                  <td>{{ row.member_user_id || '-' }}</td>
                  <td>
                    <el-tag :type="getVoicePartType(row.voice_part)">{{
                      row.voice_part || '-'
                    }}</el-tag>
                  </td>
                  <td>
                    <el-tag :type="row.tier === '一队' ? 'danger' : 'primary'">{{
                      row.tier || '-'
                    }}</el-tag>
                  </td>
                  <td>
                    <el-tag v-if="row.checked_at" type="success" size="small">已签到</el-tag>
                    <el-tag v-else type="info" size="small">未签到</el-tag>
                  </td>
                  <td>{{ formatDateTime(row.checked_at) || '-' }}</td>
                  <td v-if="session.type === 'LOCATION'">{{ row.lat || '-' }}</td>
                  <td v-if="session.type === 'LOCATION'">{{ row.lng || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <Pagination
            :current-page="pagination.page"
            :total-pages="totalPages"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            @update:current-page="val => (pagination.page = val)"
            @update:page-size="val => handlePageSizeChange(val)"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCheckinSessionDetail, getCheckinSummary, getEventDetail } from '@/api/events'
import { formatDateTime } from '@/utils/format'
import PageLoading from '@/components/common/PageLoading.vue'
import Pagination from '@/components/common/Pagination.vue'

export default {
  name: 'CheckinSessionDetail',
  components: {
    PageLoading,
    Pagination
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const eventId = computed(() => route.params.id)
    const sessionId = computed(() => route.params.sessionId)

    const loading = ref(false)
    const pageLoaded = ref(false)
    const session = ref({})
    const event = ref({})
    const records = ref([])
    const pagination = ref({ page: 1, pageSize: 20, total: 0 })
    let detailRequestSeq = 0

    const TIER_ORDER = { 一队: 0, 二队: 1 }
    const VOICE_PART_ORDER = { S1: 0, S2: 1, A1: 2, A2: 3, T1: 4, T2: 5, B1: 6, B2: 7, Other: 8 }
    const nameCollator = new Intl.Collator(['zh-Hans-u-co-pinyin', 'zh-Hans', 'zh-CN', 'en'], {
      sensitivity: 'base',
      numeric: true
    })

    const compareMembers = (a, b) => {
      const tierA = Object.prototype.hasOwnProperty.call(TIER_ORDER, a.tier)
        ? TIER_ORDER[a.tier]
        : 99
      const tierB = Object.prototype.hasOwnProperty.call(TIER_ORDER, b.tier)
        ? TIER_ORDER[b.tier]
        : 99
      if (tierA !== tierB) {
        return tierA - tierB
      }
      const vpA = Object.prototype.hasOwnProperty.call(VOICE_PART_ORDER, a.voice_part)
        ? VOICE_PART_ORDER[a.voice_part]
        : 99
      const vpB = Object.prototype.hasOwnProperty.call(VOICE_PART_ORDER, b.voice_part)
        ? VOICE_PART_ORDER[b.voice_part]
        : 99
      if (vpA !== vpB) {
        return vpA - vpB
      }
      const nameA = (a.member_name || '').toString()
      const nameB = (b.member_name || '').toString()
      const nameCmp = nameCollator.compare(nameA, nameB)
      if (nameCmp !== 0) {
        return nameCmp
      }
      const idA = (a.member_user_id || '').toString()
      const idB = (b.member_user_id || '').toString()
      return idA.localeCompare(idB)
    }

    const columnCount = computed(() => {
      let count = 6 // 姓名 + 学号 + 声部 + 梯队 + 签到情况 + 签到时间
      if (session.value.type === 'LOCATION') {
        count += 2
      } // 纬度 + 经度
      return count
    })

    const paginatedRecords = computed(() => {
      const start = (pagination.value.page - 1) * pagination.value.pageSize
      const end = start + pagination.value.pageSize
      return records.value.slice(start, end)
    })

    const totalPages = computed(() => {
      return Math.max(1, Math.ceil(pagination.value.total / pagination.value.pageSize))
    })

    const checkedInCount = computed(() => {
      return records.value.filter(r => r.checked_at).length
    })

    const totalMemberCount = computed(() => {
      return records.value.length
    })

    const handlePageSizeChange = val => {
      pagination.value.pageSize = val
      const maxPage = Math.max(1, Math.ceil(pagination.value.total / pagination.value.pageSize))
      if (pagination.value.page > maxPage) {
        pagination.value.page = maxPage
      }
    }

    const load = async ({ reset = false } = {}) => {
      const requestSeq = ++detailRequestSeq
      const currentEventId = eventId.value
      const currentSessionId = sessionId.value
      if (reset) {
        pageLoaded.value = false
      }
      loading.value = true
      try {
        const [sessionRes, eventRes, summaryRes] = await Promise.all([
          getCheckinSessionDetail(currentEventId, currentSessionId),
          getEventDetail(currentEventId),
          getCheckinSummary(currentEventId, currentSessionId)
        ])
        if (
          requestSeq !== detailRequestSeq ||
          String(currentEventId) !== String(eventId.value) ||
          String(currentSessionId) !== String(sessionId.value)
        ) {
          return
        }
        session.value = sessionRes.data
        event.value = eventRes.data
        records.value = (summaryRes.data?.results || []).sort(compareMembers)
        pagination.value.total = records.value.length

        const maxPage = Math.max(1, Math.ceil(pagination.value.total / pagination.value.pageSize))
        if (pagination.value.page > maxPage) {
          pagination.value.page = maxPage
        }
        pageLoaded.value = true
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const goMember = row => {
      if (row && row.member_id) {
        router.push({
          path: `/personnel/members/${row.member_id}`,
          query: { ref: `/events/${eventId.value}/checkin/${sessionId.value}` }
        })
      }
    }

    const exportCsv = () => {
      const header = [
        '学号',
        '姓名',
        '声部',
        '梯队',
        '签到情况',
        '签到时间',
        ...(session.value.type === 'LOCATION' ? ['纬度', '经度'] : [])
      ]

      const rows = records.value.map(r => {
        const checkinStatus = r.checked_at ? '已签到' : '未签到'
        const baseRow = [
          r.member_user_id || '',
          r.member_name || '',
          r.voice_part || '',
          r.tier || '',
          checkinStatus,
          formatDateTime(r.checked_at) || '-'
        ]

        if (session.value.type === 'LOCATION') {
          baseRow.push(r.lat || '', r.lng || '')
        }

        return baseRow
      })

      const csvLines = [header, ...rows].map(cols =>
        cols
          .map(v => {
            const s = v === null || v === undefined ? '' : String(v)
            return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
          })
          .join(',')
      )

      const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      const eventName = event.value.name || `活动${eventId.value}`
      const sessionName = session.value.name || `签到${sessionId.value}`
      a.download = `${eventName}-${sessionName}-签到记录.csv`

      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }

    const getCheckinTypeLabel = t =>
      ({ NONE: '无条件签到', PASSWORD: '口令签到', LOCATION: '地点签到' })[t] || '-'

    const getSessionTypeTag = t => {
      const map = { NONE: 'info', PASSWORD: 'warning', LOCATION: 'success' }
      return map[t] || 'info'
    }

    const getVoicePartType = voicePart => {
      const typeMap = {
        S1: 'danger',
        S2: 'danger',
        A1: 'warning',
        A2: 'warning',
        T1: 'success',
        T2: 'success',
        B1: 'primary',
        B2: 'primary',
        Other: 'info'
      }
      return typeMap[voicePart] || 'info'
    }

    onMounted(() => load({ reset: true }))
    watch(
      () => [route.params.id, route.params.sessionId],
      () => {
        load({ reset: true })
      }
    )

    return {
      loading,
      pageLoaded,
      session,
      event,
      records,
      paginatedRecords,
      pagination,
      totalPages,
      columnCount,
      checkedInCount,
      totalMemberCount,
      handlePageSizeChange,
      formatDateTime,
      exportCsv,
      goMember,
      getCheckinTypeLabel,
      getSessionTypeTag,
      getVoicePartType
    }
  }
}
</script>

<style scoped lang="scss">
.page-container {
  padding: 20px;
}

.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  margin-bottom: 12px;
}

.card-content {
  padding: 10px 12px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.value {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}

.table-wrapper {
  width: 100%;
  overflow: auto;
  margin-top: 10px;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table thead th {
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--background);
  font-size: 13px;
  white-space: nowrap;
}

.data-table tbody td {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
  color: #374151;
  overflow-wrap: anywhere;
  word-break: break-word;
  transition: background-color 0.15s ease;
}

.data-table tbody tr:hover td {
  background: #f9fafb;
}

.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
