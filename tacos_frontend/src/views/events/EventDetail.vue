<template>
  <div class="page-container">
    <div v-if="!pageLoaded" class="card">
      <div class="card-content">
        <PageLoading />
      </div>
    </div>

    <div v-if="pageLoaded" class="card">
      <div class="card-content">
        <div class="profile-header">
          <div class="meta">
            <div class="name">{{ event.name || '活动详情' }}</div>
            <div class="tags">
              <!-- <el-tag v-if="event.visibility" type="info">{{ getVisibilityLabel(event.visibility) + '的活动'}}</el-tag> -->
              <el-tag v-if="event.is_participant" type="success">角色：活动成员</el-tag>
              <el-tag v-if="event.relation === 'event_admin'" type="warning"
                >角色：活动管理员</el-tag
              >
              <el-tag v-if="!event.is_participant && event.relation !== 'event_admin'" type="info"
                >未参加</el-tag
              >
            </div>
          </div>
          <div class="actions">
            <button v-if="canEdit" class="btn-modern warning sm-btn" @click="goEdit">
              <i-lucide-pencil class="btn-icon" />
              <span>编辑</span>
            </button>
            <button v-if="canJoin" class="btn-modern success sm-btn" @click="doJoin">
              <i-lucide-check class="btn-icon" />
              <span>报名参加</span>
            </button>
          </div>
        </div>
      </div>
      <div class="info-grid" style="padding: 10px 12px">
        <div class="info-item">
          <div class="label">活动介绍</div>
          <div class="value">{{ event.introduction }}</div>
        </div>
        <div class="info-item">
          <div class="label">活动范围</div>
          <div class="value">{{ getVisibilityLabel(event.visibility) }}</div>
        </div>
        <div class="info-item">
          <div class="label">开始日期</div>
          <div class="value">{{ formatDate(event.start_date) }}</div>
        </div>
        <div class="info-item">
          <div class="label">结束日期</div>
          <div class="value">{{ formatDate(event.end_date) }}</div>
        </div>
      </div>
    </div>

    <div v-if="pageLoaded && isParticipantMember && !canJoin" class="alerts-grid">
      <div
        v-if="checkin.active && !hasCheckedIn"
        class="alert-card"
        style="border-left-color: var(--el-color-warning)"
      >
        <div class="alert-title">有签到进行中</div>
        <div class="alert-desc">您还未完成当前签到，请尽快签到。</div>
        <div class="alert-actions">
          <button class="btn-modern warning sm-btn" @click="openCheckinDialog">
            <i-lucide-clipboard-check class="btn-icon" />
            <span>立即签到</span>
          </button>
        </div>
      </div>
      <div
        v-if="pendingAssignmentsCount > 0"
        class="alert-card"
        style="border-left-color: var(--brand-500)"
      >
        <div class="alert-title">有未提交的作业</div>
        <div class="alert-desc">当前共有 {{ pendingAssignmentsCount }} 个进行中的作业未提交。</div>
        <div class="alert-actions">
          <button class="btn-modern primary sm-btn" @click="openAssignmentList">
            <i-lucide-list-checks class="btn-icon" />
            <span>查看作业</span>
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="
        pageLoaded &&
        canViewEventContent &&
        (event.announcement || (event.announcement_images && event.announcement_images.length))
      "
      class="alerts-grid"
    >
      <div class="alert-card" style="border-left-color: var(--el-color-danger)">
        <div class="alert-title">活动公告</div>
        <div
          class="alert-desc"
          v-if="event.announcement"
          style="white-space: pre-wrap; line-height: 1.6"
        >
          {{ event.announcement }}
        </div>
        <div
          class="announcement-images"
          v-if="event.announcement_images && event.announcement_images.length"
        >
          <el-image
            v-for="img in event.announcement_images"
            :key="img.id"
            :src="img.image"
            :preview-src-list="event.announcement_images.map(i => i.image)"
            fit="contain"
            style="width: 160px; height: 120px; margin-right: 8px; margin-top: 8px"
          >
            <template #error>
              <div class="image-slot">（图片加载失败）</div>
            </template>
          </el-image>
        </div>
      </div>
    </div>

    <div class="section-grid cards-row" v-if="pageLoaded && canViewEventContent">
      <div class="card card-clickable flat" @click="openCheckinList">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-list-checks />
          </div>
          <div class="stat-info">
            <div class="stat-number">签到列表</div>
            <div class="stat-label">点击查看与签到</div>
          </div>
        </div>
      </div>
      <div class="card card-clickable flat" @click="openAssignmentList">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-file-text />
          </div>
          <div class="stat-info">
            <div class="stat-number">作业</div>
            <div class="stat-label">点击查看与提交</div>
          </div>
        </div>
      </div>
      <div class="card card-clickable flat" @click="openSheetList">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-music />
          </div>
          <div class="stat-info">
            <div class="stat-number">乐谱</div>
            <div class="stat-label">活动相关乐谱</div>
          </div>
        </div>
      </div>
      <div class="card card-clickable flat" @click="openMemberList">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-user />
          </div>
          <div class="stat-info">
            <div class="stat-number">参与队员</div>
            <div class="stat-label">点击查看</div>
          </div>
        </div>
      </div>
      <div class="card card-clickable flat" @click="openAdminList">
        <div class="card-content stat-content">
          <div class="stat-icon">
            <i-lucide-user />
          </div>
          <div class="stat-info">
            <div class="stat-number">活动管理员</div>
            <div class="stat-label">点击查看</div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="startDialog.visible" title="创建签到" :width="dialogWidth">
      <el-form :model="startDialog.form" :rules="startRules" ref="startFormRef" label-width="80px">
        <el-form-item label="名称" prop="name" required>
          <el-input
            v-model="startDialog.form.name"
            placeholder="必填，请输入签到名称（例如 第一次排练签到）"
          />
        </el-form-item>
        <el-form-item label="签到类型">
          <el-select v-model="startDialog.form.type" :teleported="true">
            <el-option label="无条件签到" value="NONE" />
            <el-option label="口令签到" value="PASSWORD" />
            <el-option label="地点签到" value="LOCATION" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="startDialog.form.type === 'PASSWORD'" label="签到口令" prop="password">
          <el-input
            v-model="startDialog.form.password"
            type="password"
            placeholder="必填，请输入签到口令"
          />
        </el-form-item>
        <template v-if="startDialog.form.type === 'LOCATION'">
          <el-form-item label="定位纬度" prop="location_lat">
            <el-input
              v-model.number="startDialog.form.location_lat"
              placeholder="必填，纬度，例如 39.9042"
            />
          </el-form-item>
          <el-form-item label="定位经度" prop="location_lng">
            <el-input
              v-model.number="startDialog.form.location_lng"
              placeholder="必填，经度，例如 116.4074"
            />
          </el-form-item>
          <el-form-item label="半径(米)" prop="radius_m">
            <el-input-number v-model="startDialog.form.radius_m" :min="100" :max="5000" />
          </el-form-item>
          <el-form-item>
            <button class="btn-modern ghost sm-btn" @click="fillCurrentLocation">
              <i-lucide-map-pin class="btn-icon" />
              <span>使用当前定位填充</span>
            </button>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="startDialog.visible = false"
          style="margin-right: 10px"
        >
          <i-lucide-x class="btn-icon" />
          <span>取消</span>
        </button>
        <button class="btn-modern primary sm-btn" @click="doStartCheckin">
          <i-lucide-plus class="btn-icon" />
          <span>创建</span>
        </button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="submitDialog.visible"
      :title="'立即签到 - ' + (checkin.session?.name || getCheckinTypeLabel(checkin.session?.type))"
      :width="dialogWidth"
    >
      <div v-if="checkin.session?.type === 'PASSWORD'" style="margin-bottom: 10px">
        <el-input v-model="submitDialog.password" type="password" placeholder="输入签到口令" />
      </div>
      <div v-else-if="checkin.session?.type === 'LOCATION'" style="margin-bottom: 10px">
        <p>需要授权定位以完成签到</p>
        <button class="btn-modern primary sm-btn" @click="getLocation">
          <i-lucide-map-pin class="btn-icon" />
          <span>获取当前位置</span>
        </button>
        <div v-if="submitDialog.lat && submitDialog.lng" style="margin-top: 8px">
          坐标：{{ submitDialog.lat }}, {{ submitDialog.lng }}
        </div>
      </div>
      <div v-else-if="checkin.session?.type === 'NONE'" style="margin-bottom: 10px">
        <p style="margin-left: 10px">本次为无条件签到，点击提交即可完成签到</p>
      </div>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="submitDialog.visible = false"
          style="margin-right: 10px"
        >
          <i-lucide-x class="btn-icon" />
          <span>取消</span>
        </button>
        <button class="btn-modern primary sm-btn" @click="doSubmitCheckin">
          <i-lucide-check class="btn-icon" />
          <span>提交</span>
        </button>
      </template>
    </el-dialog>

    <!-- 对话框：签到列表 -->
    <el-dialog v-model="dialogs.checkins.visible" title="签到列表" :width="dialogWidth">
      <div v-loading="dialogs.checkins.loading">
        <div class="row-actions" v-if="canEdit" style="gap: 6px; align-items: center">
          <h4 style="margin-left: 10px">管理员选项：</h4>
          <button class="btn-modern primary sm-btn" @click="openStartCheckin">
            <i-lucide-plus class="btn-icon" />
            <span>创建签到</span>
          </button>
        </div>
        <div class="table-wrapper" style="margin-top: 10px">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width: 100px">签到</th>
                <th style="min-width: 80px">状态</th>
                <th style="min-width: 130px">类型</th>
                <th style="min-width: 160px">开始时间</th>
                <th style="min-width: 160px">结束时间</th>
                <th class="sticky-right" style="max-width: 175px; min-width: 150px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="(dialogs.checkins.items || []).length === 0">
                <td colspan="6" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in checkinsPage" :key="row.id">
                <td>{{ row.name || '-' }}</td>
                <td>
                  <template v-if="isSessionChecked(row.id)">
                    <el-tag type="success">已签到</el-tag>
                  </template>
                  <template v-else>
                    <el-tag :type="row.is_active ? 'warning' : 'info'">{{
                      row.is_active ? '进行中' : '未签到'
                    }}</el-tag>
                  </template>
                </td>
                <td>{{ getCheckinTypeLabel(row.type) }}</td>
                <td>{{ formatDateTime(row.started_at) }}</td>
                <td>{{ formatDateTime(row.ended_at) }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button
                      class="btn-modern primary xsm-btn"
                      v-if="canEdit && !row.is_active"
                      @click="doBeginCheckin(row.id)"
                    >
                      <i-lucide-check class="btn-icon" />
                      <span>开始</span>
                    </button>
                    <button
                      class="btn-modern danger xsm-btn"
                      v-if="canEdit && row.is_active"
                      @click="doStopCheckin"
                    >
                      <i-lucide-x class="btn-icon" />
                      <span>结束</span>
                    </button>
                    <button
                      class="btn-modern primary xsm-btn"
                      v-if="
                        checkin.active &&
                        row.id === checkin.session?.id &&
                        canSubmitCheckin &&
                        !isSessionChecked(row.id)
                      "
                      @click="openCheckinDialog"
                    >
                      <i-lucide-clipboard-check class="btn-icon" />
                      <span>立即签到</span>
                    </button>
                    <button
                      class="btn-modern warning xsm-btn"
                      v-if="canEdit"
                      @click="goSessionManage(row.id)"
                    >
                      <i-lucide-settings class="btn-icon" />
                      <span>管理</span>
                    </button>
                    <button
                      class="btn-modern ghost xsm-btn share-checkin-btn"
                      @click="handleShareCheckin(row)"
                      title="分享此签到"
                    >
                      <i-lucide-share class="btn-icon" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :current-page="paginations.checkins.page"
          :total-pages="checkinsTotalPages"
          :page-size="paginations.checkins.pageSize"
          :total="paginations.checkins.total"
          @update:current-page="val => handleCurrentPage('checkins', val)"
          @update:page-size="val => handlePageSize('checkins', val)"
        />
      </div>
    </el-dialog>

    <!-- 对话框：管理员列表 -->
    <el-dialog v-model="dialogs.admins.visible" title="活动管理员" :width="dialogWidth">
      <div v-loading="dialogs.admins.loading">
        <div class="row-actions" v-if="canEdit" style="gap: 6px; align-items: center">
          <h4 style="margin-left: 10px">管理员选项：</h4>
          <button class="btn-modern warning sm-btn" @click="goEdit">
            <i-lucide-pencil class="btn-icon" />
            <span>编辑相关信息</span>
          </button>
        </div>
        <div class="table-wrapper" style="margin-top: 10px">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width: 80px">姓名</th>
                <th v-if="isAdmin" style="min-width: 80px">学号</th>
                <th style="min-width: 40px">声部</th>
                <th style="min-width: 40px">梯队</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="(dialogs.admins.items || []).length === 0">
                <td colspan="4" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in adminsPage" :key="row.id || row.member_id">
                <td>
                  <el-link type="primary" @click="goMember(row)">{{ row.name || '-' }}</el-link>
                </td>
                <td v-if="isAdmin">{{ row.user_id || '-' }}</td>
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
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :current-page="paginations.admins.page"
          :total-pages="adminsTotalPages"
          :page-size="paginations.admins.pageSize"
          :total="paginations.admins.total"
          @update:current-page="val => handleCurrentPage('admins', val)"
          @update:page-size="val => handlePageSize('admins', val)"
        />
      </div>
    </el-dialog>

    <!-- 对话框：参与队员列表 -->
    <el-dialog v-model="dialogs.members.visible" title="参与队员" :width="createDialogWidth">
      <div v-loading="dialogs.members.loading">
        <div class="row-actions" v-if="canEdit" style="gap: 6px; align-items: center">
          <h4 style="margin-left: 10px">管理员选项：</h4>
          <button class="btn-modern warning sm-btn" @click="goEdit">
            <i-lucide-pencil class="btn-icon" />
            <span>编辑相关信息</span>
          </button>
        </div>
        <div class="table-wrapper" style="margin-top: 10px">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width: 80px">姓名</th>
                <th v-if="isAdmin" style="min-width: 80px">学号</th>
                <th style="min-width: 40px">声部</th>
                <th style="min-width: 40px">梯队</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="(dialogs.members.items || []).length === 0">
                <td colspan="4" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in membersPage" :key="row.id || row.member_id">
                <td>
                  <el-link type="primary" @click="goMember(row)">{{ row.name || '-' }}</el-link>
                </td>
                <td v-if="isAdmin">{{ row.user_id || '-' }}</td>
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
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :current-page="paginations.members.page"
          :total-pages="membersTotalPages"
          :page-size="paginations.members.pageSize"
          :total="paginations.members.total"
          @update:current-page="val => handleCurrentPage('members', val)"
          @update:page-size="val => handlePageSize('members', val)"
        />
      </div>
    </el-dialog>

    <!-- 对话框：作业列表 -->
    <el-dialog v-model="dialogs.assignments.visible" title="作业列表" :width="createDialogWidth">
      <div v-loading="dialogs.assignments.loading">
        <div class="row-actions" v-if="canEdit" style="gap: 6px; align-items: center">
          <h4 style="margin-left: 10px">管理员选项：</h4>
          <button class="btn-modern primary sm-btn" @click="openCreateAssignment">
            <i-lucide-plus class="btn-icon" />
            <span>发布作业</span>
          </button>
        </div>
        <div class="table-wrapper" style="margin-top: 10px">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width: 120px">标题</th>
                <th style="min-width: 80px">状态</th>
                <th style="min-width: 120px">批改评语</th>
                <th style="min-width: 160px">截止时间</th>
                <th class="sticky-right" style="min-width: 110px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="(dialogs.assignments.items || []).length === 0">
                <td colspan="5" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in assignmentsPage" :key="row.id">
                <td>
                  <router-link
                    :to="{
                      name: 'AssignmentDetail',
                      params: { id, assignmentId: row.id },
                      query: { ref: `/events/${id}` }
                    }"
                  >
                    {{ row.title }}
                  </router-link>
                </td>
                <td>
                  <el-space wrap>
                    <el-tag :type="isAssignmentClosed(row) ? 'info' : 'warning'">{{
                      isAssignmentClosed(row) ? '已截止' : '进行中'
                    }}</el-tag>
                    <el-tag :type="row.my_submitted ? 'success' : 'danger'">{{
                      row.my_submitted ? '已提交' : '未提交'
                    }}</el-tag>
                  </el-space>
                </td>
                <td>
                  <span
                    v-if="row.my_graded && row.my_graded_comment && row.my_graded_comment.trim()"
                    >{{ row.my_graded_comment }}</span
                  >
                  <span v-else>未批改</span>
                </td>
                <td>{{ formatDateTime(row.deadline) }}</td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button
                      v-if="!canEdit"
                      class="btn-modern primary xsm-btn"
                      @click="goAssignment(row)"
                    >
                      <i-lucide-eye class="btn-icon" />
                      <span>查看内容</span>
                    </button>
                    <button
                      v-if="canEdit"
                      class="btn-modern primary xsm-btn"
                      @click="goAssignment(row)"
                    >
                      <i-lucide-eye class="btn-icon" />
                      <span>查看</span>
                    </button>
                    <button
                      v-if="canEdit"
                      class="btn-modern warning xsm-btn"
                      @click="goAssignmentManage(row)"
                    >
                      <i-lucide-settings class="btn-icon" />
                      <span>管理</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :current-page="paginations.assignments.page"
          :total-pages="assignmentsTotalPages"
          :page-size="paginations.assignments.pageSize"
          :total="paginations.assignments.total"
          @update:current-page="val => handleCurrentPage('assignments', val)"
          @update:page-size="val => handlePageSize('assignments', val)"
        />
      </div>
    </el-dialog>

    <!-- 对话框：乐谱列表 -->
    <el-dialog v-model="dialogs.sheets.visible" title="相关乐谱" :width="createDialogWidth">
      <div v-loading="dialogs.sheets.loading">
        <div class="row-actions" v-if="canEdit" style="gap: 6px; align-items: center">
          <h4 style="margin-left: 10px">管理员选项：</h4>
          <button class="btn-modern warning sm-btn" @click="goEdit">
            <i-lucide-pencil class="btn-icon" />
            <span>编辑相关信息</span>
          </button>
        </div>
        <div class="table-wrapper" style="margin-top: 10px">
          <table class="data-table">
            <thead>
              <tr>
                <th style="min-width: 140px">曲名</th>
                <th style="min-width: 80px">作曲</th>
                <th style="min-width: 80px">编曲</th>
                <th style="min-width: 90px">版权限制</th>
                <th class="sticky-right" style="min-width: 110px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="(dialogs.sheets.items || []).length === 0">
                <td colspan="5" class="empty-cell">暂无数据</td>
              </tr>
              <tr v-for="row in sheetsPage" :key="row.id">
                <td>
                  <el-link type="primary" @click="goSheet(row)">{{ row.title }}</el-link>
                </td>
                <td>{{ row.composer || '-' }}</td>
                <td>{{ row.arranger || '-' }}</td>
                <td>
                  <el-tag :type="row.is_restricted ? 'danger' : 'success'">{{
                    row.is_restricted ? '受限' : '公开'
                  }}</el-tag>
                </td>
                <td class="sticky-right">
                  <div class="row-actions">
                    <button class="btn-modern ghost xsm-btn" @click="goSheet(row)">
                      <i-lucide-eye class="btn-icon" />
                      <span>详情</span>
                    </button>
                    <button class="btn-modern primary xsm-btn" @click="download(row)">
                      <i-lucide-download class="btn-icon" />
                      <span>下载</span>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pagination
          :current-page="paginations.sheets.page"
          :total-pages="sheetsTotalPages"
          :page-size="paginations.sheets.pageSize"
          :total="paginations.sheets.total"
          @update:current-page="val => handleCurrentPage('sheets', val)"
          @update:page-size="val => handlePageSize('sheets', val)"
        />
      </div>
    </el-dialog>

    <el-dialog v-model="createDialog.visible" title="发布作业" :width="createDialogWidth">
      <el-form
        :model="createDialog.form"
        label-width="80px"
        ref="createFormRef"
        :rules="createRules"
      >
        <el-form-item label="标题" prop="title" required>
          <el-input v-model="createDialog.form.title" placeholder="请输入作业标题" />
        </el-form-item>
        <el-form-item label="截止时间" prop="deadline" required>
          <el-date-picker
            v-model="createDialog.form.deadline"
            type="datetime"
            placeholder="选择截止时间"
            value-format="YYYY-MM-DDTHH:mm:ssZZ"
            :teleported="true"
          />
        </el-form-item>
        <el-form-item label="说明">
          <el-input
            type="textarea"
            :rows="5"
            v-model="createDialog.form.description"
            placeholder="作业说明（可包含要求说明）"
          />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            :file-list="createDialog.files"
            :on-change="onCreateFileChange"
            :on-remove="onCreateFileRemove"
            :auto-upload="false"
            multiple
          >
            <button class="btn-modern ghost sm-btn" type="button">
              <i-lucide-upload class="btn-icon" />
              <span>选择文件</span>
            </button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <button
          class="btn-modern ghost sm-btn"
          @click="createDialog.visible = false"
          style="margin-right: 10px"
        >
          <i-lucide-x class="btn-icon" />
          <span>取消</span>
        </button>
        <button class="btn-modern primary sm-btn" :loading="creating" @click="doCreateAssignment">
          <i-lucide-send class="btn-icon" />
          <span>发布</span>
        </button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import PageLoading from '@/components/common/PageLoading.vue'
import Pagination from '@/components/common/Pagination.vue'
import {
  getEventDetail,
  deleteEvent,
  joinEvent,
  getCheckinStatus,
  getCheckinSessions,
  startCheckin,
  stopCheckin as stopCheckinApi,
  submitCheckin,
  beginCheckin,
  getCheckinRecords,
  getAssignments,
  createAssignment,
  uploadAssignmentAttachment,
  getEventSheets,
  getEventAdmins,
  getEventMembers
} from '@/api/events'
import { getProfile } from '@/api/auth'
import { initiateDownload, getDownloadTask } from '@/api/sheets'
import { formatDate, formatDateTime } from '@/utils/format'
import { notify } from '@/utils/notify'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
dayjs.extend(utc)
dayjs.extend(timezone)
import {
  User as LucideUser,
  ListChecks as LucideListChecks,
  FileText as LucideFileText,
  Music as LucideMusic,
  Share as LucideShare
} from 'lucide-vue-next'
import { doCheckinShare } from '@/utils/share'

export default {
  name: 'EventDetail',
  components: {
    PageLoading,
    Pagination,
    'i-lucide-user': LucideUser,
    'i-lucide-list-checks': LucideListChecks,
    'i-lucide-file-text': LucideFileText,
    'i-lucide-music': LucideMusic,
    'i-lucide-share': LucideShare
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const isAdmin = computed(() => store.getters['auth/isAdmin'])
    const user = computed(() => store.getters['auth/user'])

    const currentId = computed(() => route.params.id)
    const loading = ref(false)
    const pageLoaded = ref(false)
    const event = ref({})
    const checkin = ref({ active: false, session: null })
    const pendingAssignmentsCount = ref(0)
    let detailRequestSeq = 0
    const dialogs = ref({
      checkins: { visible: false, loading: false, items: [] },
      assignments: { visible: false, loading: false, items: [] },
      sheets: { visible: false, loading: false, items: [] },
      admins: { visible: false, loading: false, items: [] },
      members: { visible: false, loading: false, items: [] }
    })
    const paginations = ref({
      admins: { page: 1, pageSize: 10, total: 0 },
      members: { page: 1, pageSize: 10, total: 0 },
      checkins: { page: 1, pageSize: 10, total: 0 },
      assignments: { page: 1, pageSize: 10, total: 0 },
      sheets: { page: 1, pageSize: 10, total: 0 }
    })
    const myTier = ref('')
    const myStatus = ref('ACTIVE')
    const memberContextLoaded = ref(false)
    const startDialog = ref({
      visible: false,
      form: {
        name: '',
        type: 'NONE',
        password: '',
        location_lat: null,
        location_lng: null,
        radius_m: 500
      }
    })
    const startFormRef = ref(null)
    const startRules = {
      name: [
        { required: true, message: '请输入签到名称', trigger: 'blur' },
        {
          validator: (_r, v, cb) =>
            v && String(v).trim() ? cb() : cb(new Error('请输入签到名称')),
          trigger: 'blur'
        }
      ],
      password: [
        {
          validator: (_r, v, cb) => {
            if (startDialog.value.form.type === 'PASSWORD' && (!v || !String(v).trim())) {
              return cb(new Error('请输入签到口令'))
            }
            cb()
          },
          trigger: 'blur'
        }
      ]
    }
    const submitDialog = ref({ visible: false, password: '', lat: null, lng: null })
    const hasCheckedIn = ref(false)
    const checkedSessionIds = ref([])

    const loadMyMemberContext = async () => {
      if (memberContextLoaded.value) {
        return
      }
      try {
        const res = await getProfile()
        myTier.value = res?.data?.member?.tier || ''
        myStatus.value = res?.data?.member?.status || 'ACTIVE'
      } catch (e) {
        // 个人信息缺失时继续加载活动详情
      } finally {
        memberContextLoaded.value = true
      }
    }

    const canViewEventMemberData = () => {
      return isAdmin.value || event.value?.relation === 'event_admin' || event.value?.is_participant
    }

    const fetchDetail = async ({ reset = false } = {}) => {
      const requestSeq = ++detailRequestSeq
      if (reset) {
        pageLoaded.value = false
      }
      loading.value = true
      try {
        const curId = route.params.id
        const isLatestRequest = () =>
          requestSeq === detailRequestSeq && String(curId) === String(route.params.id)
        const [res] = await Promise.all([getEventDetail(curId), loadMyMemberContext()])
        if (!isLatestRequest()) {
          return
        }
        event.value = res.data
        // 设置分享页面信息
        if (event.value.name) {
          store.dispatch('common/setSharePageInfo', `活动「${event.value.name}」`)
        }
        const [checkinResult, pendingAssignmentsResult] = await Promise.allSettled([
          getCheckinStatus(curId),
          computePendingAssignmentsCount(curId)
        ])
        if (!isLatestRequest()) {
          return
        }
        const s2 =
          checkinResult.status === 'fulfilled'
            ? checkinResult.value
            : { data: { active: false, session: null } }
        const nextPendingAssignmentsCount =
          pendingAssignmentsResult.status === 'fulfilled' ? pendingAssignmentsResult.value : 0
        checkin.value = s2.data || { active: false, session: null }
        const activeSessionId = Number(checkin.value?.session?.id)
        hasCheckedIn.value = !!s2.data?.has_checked_in
        checkedSessionIds.value =
          hasCheckedIn.value && Number.isFinite(activeSessionId) ? [activeSessionId] : []
        pendingAssignmentsCount.value = nextPendingAssignmentsCount
        pageLoaded.value = true
      } finally {
        if (requestSeq === detailRequestSeq) {
          loading.value = false
        }
      }
    }

    const refreshMyCheckinFlag = async eventId => {
      try {
        if (!user.value) {
          return
        }
        if (!canViewEventMemberData()) {
          return
        }
        // 非管理员接口虽然只返回“我自己的签到记录”，但仍然有分页；
        // 这里只取第一页会导致部分较早记录漏掉，进而误判成“未签到”。
        const pageSize = 200
        const rows = []
        let page = 1
        let total = Infinity

        while ((page - 1) * pageSize < total) {
          const res = await getCheckinRecords(eventId, { page, page_size: pageSize, mine: true })
          const pageRows = res?.data?.results || []
          total = Number(res?.data?.count || pageRows.length || 0)
          rows.push(...pageRows)

          if (pageRows.length < pageSize) {
            break
          }
          page += 1
          if (page > 50) {
            break
          }
        }

        const myId = user.value.user_id
        const mine = rows.filter(r => r.member_user_id === myId)
        const nextCheckedSessionIds = mine
          .map(r => Number(r.session))
          .filter(sessionId => Number.isFinite(sessionId))

        if (String(eventId) !== String(currentId.value)) {
          return
        }

        checkedSessionIds.value = nextCheckedSessionIds
        if (checkin.value.active && checkin.value.session) {
          hasCheckedIn.value = nextCheckedSessionIds.includes(Number(checkin.value.session.id))
        } else {
          hasCheckedIn.value = false
        }
      } catch (e) {
        // 签到记录加载失败时保持默认状态
      }
    }

    const isSessionChecked = sid => checkedSessionIds.value.includes(Number(sid))

    const computePendingAssignmentsCount = async eventId => {
      try {
        if (!event.value?.is_participant) {
          return 0
        }
        const ares = await getAssignments(eventId, { page_size: 200 })
        const rows = ares?.data?.results || []
        const now = dayjs().tz('Asia/Shanghai')
        return rows.filter(r => {
          const deadline = dayjs(r.deadline).tz('Asia/Shanghai')
          const ongoing = !r.is_closed && deadline.valueOf() > now.valueOf()
          return ongoing && !r.my_submitted
        }).length
      } catch {
        return 0
      }
    }

    const openCheckinList = async () => {
      dialogs.value.checkins.visible = true
      dialogs.value.checkins.loading = true
      try {
        const [listRes] = await Promise.all([
          getCheckinSessions(currentId.value),
          refreshMyCheckinFlag(currentId.value)
        ])
        const payload = listRes && listRes.data ? listRes.data : listRes
        const sessions = (payload && (payload.results ?? payload)) || []
        dialogs.value.checkins.items = Array.isArray(sessions) ? sessions : sessions.results || []
        paginations.value.checkins.total = Array.isArray(dialogs.value.checkins.items)
          ? dialogs.value.checkins.items.length
          : 0
        paginations.value.checkins.page = 1
      } finally {
        dialogs.value.checkins.loading = false
      }
    }
    const openAssignmentList = async () => {
      dialogs.value.assignments.visible = true
      dialogs.value.assignments.loading = true
      try {
        const ares = await getAssignments(currentId.value, { page_size: 200 })
        dialogs.value.assignments.items = ares?.data?.results || []
        paginations.value.assignments.total = Array.isArray(dialogs.value.assignments.items)
          ? dialogs.value.assignments.items.length
          : 0
        paginations.value.assignments.page = 1
      } finally {
        dialogs.value.assignments.loading = false
      }
    }
    const openSheetList = async () => {
      dialogs.value.sheets.visible = true
      dialogs.value.sheets.loading = true
      try {
        const aggregated = []
        let page = 1
        const pageSize = 200
        let total = Infinity
        while ((page - 1) * pageSize < total) {
          const sres = await getEventSheets(currentId.value, { page, page_size: pageSize })
          const data = sres && sres.data ? sres.data : sres
          const results = Array.isArray(data?.results) ? data.results : []
          total = Number(data?.count || results.length || 0)
          aggregated.push(...results)
          if (results.length < pageSize) {
            break
          }
          page += 1
          if (page > 50) {
            break
          }
        }
        dialogs.value.sheets.items = aggregated
        paginations.value.sheets.total = Array.isArray(dialogs.value.sheets.items)
          ? dialogs.value.sheets.items.length
          : 0
        paginations.value.sheets.page = 1
      } finally {
        dialogs.value.sheets.loading = false
      }
    }

    const openAdminList = async () => {
      dialogs.value.admins.visible = true
      dialogs.value.admins.loading = true
      try {
        const res = await getEventAdmins(currentId.value, { page_size: 200 })
        dialogs.value.admins.items = res?.data?.results || []
        paginations.value.admins.total = Array.isArray(dialogs.value.admins.items)
          ? dialogs.value.admins.items.length
          : 0
        paginations.value.admins.page = 1
      } finally {
        dialogs.value.admins.loading = false
      }
    }

    const openMemberList = async () => {
      dialogs.value.members.visible = true
      dialogs.value.members.loading = true
      try {
        const res = await getEventMembers(currentId.value, { page_size: 200 })
        dialogs.value.members.items = res?.data?.results || []
        paginations.value.members.total = Array.isArray(dialogs.value.members.items)
          ? dialogs.value.members.items.length
          : 0
        paginations.value.members.page = 1
      } finally {
        dialogs.value.members.loading = false
      }
    }

    const adminsPage = computed(() => {
      const pg = paginations.value.admins
      const data = dialogs.value.admins.items || []
      const start = (pg.page - 1) * pg.pageSize
      return data.slice(start, start + pg.pageSize)
    })
    const membersPage = computed(() => {
      const pg = paginations.value.members
      const data = dialogs.value.members.items || []
      const start = (pg.page - 1) * pg.pageSize
      return data.slice(start, start + pg.pageSize)
    })
    const checkinsPage = computed(() => {
      const pg = paginations.value.checkins
      const data = dialogs.value.checkins.items || []
      const start = (pg.page - 1) * pg.pageSize
      return data.slice(start, start + pg.pageSize)
    })
    const assignmentsPage = computed(() => {
      const pg = paginations.value.assignments
      const data = dialogs.value.assignments.items || []
      const start = (pg.page - 1) * pg.pageSize
      return data.slice(start, start + pg.pageSize)
    })
    const sheetsPage = computed(() => {
      const pg = paginations.value.sheets
      const data = dialogs.value.sheets.items || []
      const start = (pg.page - 1) * pg.pageSize
      return data.slice(start, start + pg.pageSize)
    })
    const adminsTotalPages = computed(() => {
      const pg = paginations.value.admins
      const size = Number(pg.pageSize) || 10
      if (!pg.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pg.total / size))
    })
    const membersTotalPages = computed(() => {
      const pg = paginations.value.members
      const size = Number(pg.pageSize) || 10
      if (!pg.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pg.total / size))
    })
    const checkinsTotalPages = computed(() => {
      const pg = paginations.value.checkins
      const size = Number(pg.pageSize) || 10
      if (!pg.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pg.total / size))
    })
    const assignmentsTotalPages = computed(() => {
      const pg = paginations.value.assignments
      const size = Number(pg.pageSize) || 10
      if (!pg.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pg.total / size))
    })
    const sheetsTotalPages = computed(() => {
      const pg = paginations.value.sheets
      const size = Number(pg.pageSize) || 10
      if (!pg.total || !size) {
        return 1
      }
      return Math.max(1, Math.ceil(pg.total / size))
    })
    const handlePageSize = (key, val) => {
      const pg = paginations.value[key]
      pg.pageSize = val
      const maxPage = Math.max(1, Math.ceil((pg.total || 0) / (pg.pageSize || 1)))
      if (pg.page > maxPage) {
        pg.page = maxPage
      }
    }
    const handleCurrentPage = (key, val) => {
      paginations.value[key].page = val
    }

    const canEdit = computed(() => isAdmin.value || event.value?.relation === 'event_admin')
    const canViewEventContent = computed(() => {
      return canEdit.value || event.value?.is_participant === true
    })
    const canJoin = computed(() => {
      if (!user.value || event.value?.is_participant) {
        return false
      }
      if (event.value?.relation === 'event_admin') {
        return true
      }
      if (myStatus.value === 'ALUMNI') {
        return event.value?.visible_to_alumni === true
      }
      const vis = event.value.visibility
      if (vis === 'ALL') {
        return true
      }
      if (vis === 'FIRST') {
        return myTier.value === '一队'
      }
      if (vis === 'SECOND') {
        return myTier.value === '二队'
      }
      return false
    })
    const isParticipantMember = computed(() => {
      return event.value?.is_participant === true
    })
    const canSubmitCheckin = computed(
      () => !!checkin.value.active && isParticipantMember.value && !hasCheckedIn.value
    )

    // 获取返回目标路径（不导航）
    const getBackDestination = () => {
      const ref = route.query && route.query.ref
      if (ref && typeof ref === 'string') {
        return ref
      }
      return '/events'
    }

    const goEdit = () => {
      // 传递详情页的返回目标给编辑页，编辑页保存后返回详情页时保留原 ref
      const backDest = getBackDestination()
      router.push(`/events/${currentId.value}/edit?ref=${encodeURIComponent(backDest)}`)
    }
    const goMember = m => {
      // 跳转到成员详情，使用成员主键ID作为路由参数，并带上返回ref
      if (m && (m.id || m.member_id)) {
        const mid = m.id || m.member_id
        router.push({
          path: `/personnel/members/${mid}`,
          query: { ref: `/events/${currentId.value}` }
        })
      }
    }
    const doDelete = async () => {
      await deleteEvent(currentId.value)
      router.push('/events')
    }
    const doJoin = async () => {
      await joinEvent(currentId.value)
      await fetchDetail()
    }

    const openStartCheckin = () => {
      startDialog.value.form = {
        type: 'NONE',
        password: '',
        location_lat: null,
        location_lng: null,
        radius_m: 500
      }
      startDialog.value.visible = true
    }
    const doStartCheckin = async () => {
      if (startFormRef.value) {
        startFormRef.value.validate(async valid => {
          if (!valid) {
            return
          }
          await startCheckin(currentId.value, { ...startDialog.value.form })
          startDialog.value.visible = false
          await fetchDetail()
          if (dialogs.value.checkins.visible) {
            await openCheckinList()
          }
        })
      } else {
        await startCheckin(currentId.value, { ...startDialog.value.form })
        startDialog.value.visible = false
        await fetchDetail()
        if (dialogs.value.checkins.visible) {
          await openCheckinList()
        }
      }
    }
    const doStopCheckin = async () => {
      await stopCheckinApi(currentId.value)
      await fetchDetail()
      if (dialogs.value.checkins.visible) {
        await openCheckinList()
      }
    }
    const doBeginCheckin = async sessionId => {
      await beginCheckin(currentId.value, sessionId)
      await fetchDetail()
      if (dialogs.value.checkins.visible) {
        await openCheckinList()
      }
    }
    const goSessionManage = sessionId => {
      router.push(`/events/${currentId.value}/checkin/${sessionId}`)
    }
    const openCheckinDialog = () => {
      submitDialog.value.password = ''
      submitDialog.value.lat = null
      submitDialog.value.lng = null
      submitDialog.value.visible = true
    }
    const handleGeolocationError = error => {
      const code = error && error.code
      if (code === 1) {
        notify.error('已拒绝定位权限，请在浏览器设置中允许定位')
      } else if (code === 2) {
        notify.error('无法获取位置信息，请稍后重试')
      } else if (code === 3) {
        notify.error('获取位置超时，请再次尝试')
      } else {
        notify.error('获取位置失败，请检查网络与权限设置')
      }
    }
    const requestGeolocation = onSuccess => {
      if (!('geolocation' in navigator)) {
        notify.error('当前浏览器不支持定位')
        return
      }
      if (!window.isSecureContext) {
        // 非安全上下文下大多数浏览器会拒绝定位
        notify.warning('定位需在 HTTPS 或 localhost 环境下使用')
      }
      const options = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
      navigator.geolocation.getCurrentPosition(onSuccess, handleGeolocationError, options)
    }
    const getLocation = () => {
      requestGeolocation(pos => {
        submitDialog.value.lat = Number(pos.coords.latitude.toFixed(6))
        submitDialog.value.lng = Number(pos.coords.longitude.toFixed(6))
        notify.success('已获取当前位置')
      })
    }
    const fillCurrentLocation = () => {
      requestGeolocation(pos => {
        startDialog.value.form.location_lat = Number(pos.coords.latitude.toFixed(6))
        startDialog.value.form.location_lng = Number(pos.coords.longitude.toFixed(6))
        notify.success('已填充为当前位置')
      })
    }
    const doSubmitCheckin = async () => {
      const payload = {}
      if (checkin.value.session?.type === 'PASSWORD') {
        payload.password = submitDialog.value.password
      }
      if (checkin.value.session?.type === 'LOCATION') {
        payload.lat = submitDialog.value.lat
        payload.lng = submitDialog.value.lng
      }
      try {
        const result = await submitCheckin(currentId.value, payload)
        submitDialog.value.visible = false

        // 检查是否是重复签到
        if (result?.data?.duplicate || result?.data?.data?.duplicate) {
          notify.warning('您已签到过，无需重复签到')
        } else {
          notify.success('签到成功！')
        }

        await refreshMyCheckinFlag(currentId.value)
        if (dialogs.value.checkins.visible) {
          await openCheckinList()
        }
      } catch (error) {
        const resp = error?.response
        const data = resp?.data
        const httpStatus = resp?.status

        if (httpStatus === 422) {
          // 验证错误：密码错误、坐标缺失等
          const message = data?.message || data?.detail || '签到验证失败'
          notify.error(message)
          // 不关闭对话框，让用户可以重新输入
          return
        }

        if (httpStatus === 403) {
          // 权限不足或位置不在范围内
          const message = data?.message || data?.detail || '签到失败'
          notify.error(message)
          submitDialog.value.visible = false
          return
        }

        // 其他错误
        const message = data?.message || data?.detail || '签到失败，请重试'
        notify.error(message)
        submitDialog.value.visible = false
      }
    }

    const isAssignmentClosed = row => {
      try {
        return (
          dayjs(row.deadline).tz('Asia/Shanghai').valueOf() <= dayjs().tz('Asia/Shanghai').valueOf()
        )
      } catch (e) {
        return false
      }
    }
    const goAssignment = row => {
      router.push(`/events/${currentId.value}/assignments/${row.id}`)
    }
    const goAssignmentManage = row => {
      router.push(`/events/${currentId.value}/assignments/${row.id}/manage`)
    }
    const goSheet = row => {
      router.push({ path: `/sheets/${row.id}`, query: { ref: `/events/${currentId.value}` } })
    }
    const download = async row => {
      const loadingMsg = notify.loading('正在生成PDF，请稍候...')

      try {
        const initResp = await initiateDownload(row.id)
        const taskId = initResp.data?.task_id

        if (!taskId) {
          throw new Error('无法获取任务ID')
        }

        const pollTask = async () => {
          try {
            const resp = await getDownloadTask(taskId, false)

            const contentType = resp.headers['content-type'] || resp.headers['Content-Type']

            if (contentType && contentType.includes('application/json')) {
              const text = await resp.data.text()
              const jsonData = JSON.parse(text)

              if (jsonData.data?.status === 'PENDING' || jsonData.data?.status === 'PROCESSING') {
                setTimeout(pollTask, 1000)
              } else if (jsonData.data?.status === 'FAILED') {
                loadingMsg.close()
                notify.error(jsonData.message || '生成水印失败')
              } else {
                loadingMsg.close()
                notify.error('任务状态异常')
              }
            } else {
              loadingMsg.close()

              const blob = new Blob([resp.data], { type: 'application/pdf' })
              let filename = `${row.title}.pdf`

              const cd = resp.headers['content-disposition'] || resp.headers['Content-Disposition']
              if (cd && cd.includes('filename=')) {
                const match =
                  cd.match(/filename\*=UTF-8''([^;\n]+)/) || cd.match(/filename="?([^";\n]+)"?/)
                if (match && match[1]) {
                  filename = decodeURIComponent(match[1])
                }
              }

              const url = window.URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = filename
              document.body.appendChild(a)
              a.click()
              a.remove()
              window.URL.revokeObjectURL(url)

              notify.success('下载成功')
            }
          } catch (pollError) {
            loadingMsg.close()
            console.error('Polling error:', pollError)
            notify.error('下载失败，请重试')
          }
        }

        pollTask()
      } catch (e) {
        loadingMsg.close()
        console.error('Download error:', e)
        notify.error('下载失败')
      }
    }

    const createDialog = ref({
      visible: false,
      form: { title: '', description: '', deadline: '' },
      files: []
    })
    const createFormRef = ref(null)
    const creating = ref(false)
    const createRules = {
      title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
      deadline: [{ required: true, message: '请选择截止时间', trigger: 'change' }]
    }
    const openCreateAssignment = () => {
      // 计算上海当天 23:59，格式匹配 value-format="YYYY-MM-DDTHH:mm:ssZZ"
      const nowShanghai = new Date(Date.now() + 8 * 60 * 60 * 1000) // UTC+8，无夏令时
      const y = nowShanghai.getUTCFullYear()
      const m = String(nowShanghai.getUTCMonth() + 1).padStart(2, '0')
      const d = String(nowShanghai.getUTCDate()).padStart(2, '0')
      const defaultDeadline = `${y}-${m}-${d}T23:59:59+08:00`
      createDialog.value.form = { title: '', description: '', deadline: defaultDeadline }
      createDialog.value.files = []
      createDialog.value.visible = true
    }
    const onCreateFileChange = (_file, files) => {
      createDialog.value.files = files
    }
    const onCreateFileRemove = (_file, files) => {
      createDialog.value.files = files
    }
    const doCreateAssignment = async () => {
      if (createFormRef.value) {
        createFormRef.value.validate(async valid => {
          if (!valid) {
            return
          }
          await actuallyCreateAssignment()
        })
      } else {
        await actuallyCreateAssignment()
      }
    }
    const actuallyCreateAssignment = async () => {
      creating.value = true
      try {
        const created = await createAssignment(currentId.value, { ...createDialog.value.form })
        const createdId = created?.data?.id
        for (const f of createDialog.value.files.map(x => x.raw).filter(Boolean)) {
          await uploadAssignmentAttachment(currentId.value, createdId, f)
        }
        createDialog.value.visible = false
        await fetchDetail()
        if (dialogs.value.assignments.visible) {
          await openAssignmentList()
        }
      } finally {
        creating.value = false
      }
    }

    const dialogWidth = ref('520px')
    const createDialogWidth = ref('560px')
    const computeDialogWidths = () => {
      const vw = window.innerWidth || 1024
      if (vw <= 360) {
        dialogWidth.value = '95vw'
        createDialogWidth.value = '96vw'
        return
      }
      if (vw <= 768) {
        dialogWidth.value = '92vw'
        createDialogWidth.value = '94vw'
        return
      }
      if (vw <= 1024) {
        dialogWidth.value = '640px'
        createDialogWidth.value = '700px'
        return
      }
      dialogWidth.value = '720px'
      createDialogWidth.value = '780px'
    }

    onMounted(() => {
      computeDialogWidths()
      window.addEventListener('resize', computeDialogWidths, { passive: true })
    })
    onUnmounted(() => {
      window.removeEventListener('resize', computeDialogWidths)
    })

    onMounted(() => fetchDetail({ reset: true }))
    watch(
      () => route.params.id,
      () => {
        fetchDetail({ reset: true })
      }
    )
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

    const getVisibilityLabel = v =>
      ({ ALL: '面向全体', FIRST: '面向一队', SECOND: '面向二队', PARTIAL: '面向部分' })[v] ||
      '面向部分'
    const getCheckinTypeLabel = t =>
      ({ NONE: '无条件签到', PASSWORD: '口令签到', LOCATION: '地点签到' })[t] || '-'

    // 分享签到
    const handleShareCheckin = async row => {
      const userName = user.value?.name || user.value?.user_id || '有人'
      const eventName = event.value?.name || '活动'
      await doCheckinShare(userName, currentId.value, eventName, row)
    }

    return {
      id: currentId,
      loading,
      pageLoaded,
      event,
      checkin,
      pendingAssignmentsCount,
      dialogs,
      paginations,
      adminsPage,
      membersPage,
      checkinsPage,
      assignmentsPage,
      sheetsPage,
      adminsTotalPages,
      membersTotalPages,
      checkinsTotalPages,
      assignmentsTotalPages,
      sheetsTotalPages,
      handlePageSize,
      handleCurrentPage,
      isAdmin,
      formatDate,
      formatDateTime,
      canEdit,
      canViewEventContent,
      canJoin,
      isParticipantMember,
      canSubmitCheckin,
      hasCheckedIn,
      goEdit,
      doDelete,
      doJoin,
      goMember,
      openCheckinList,
      openAssignmentList,
      openSheetList,
      openAdminList,
      openMemberList,
      openStartCheckin,
      doStartCheckin,
      doStopCheckin,
      doBeginCheckin,
      openCheckinDialog,
      doSubmitCheckin,
      getLocation,
      fillCurrentLocation,
      goSessionManage,
      getVoicePartType,
      getVisibilityLabel,
      getCheckinTypeLabel,
      handleShareCheckin,
      startDialog,
      submitDialog,
      startFormRef,
      startRules,
      isSessionChecked,
      isAssignmentClosed,
      goAssignment,
      goAssignmentManage,
      createDialog,
      createFormRef,
      createRules,
      openCreateAssignment,
      onCreateFileChange,
      onCreateFileRemove,
      doCreateAssignment,
      creating,
      download,
      goSheet,
      dialogWidth,
      createDialogWidth
    }
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
:deep(.el-dialog) {
  border-radius: 10px;
  border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
:deep(.el-dialog__header) {
  padding: 10px 12px;
  margin-right: 0;
  margin-bottom: 6px;
  border-bottom: 1px solid var(--border);
}
:deep(.el-dialog__title) {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}
:deep(.el-dialog__body) {
  padding: 4px 0px;
}
:deep(.el-dialog__footer) {
  padding: 10px 0px 0px 0px;
  border-top: 1px solid var(--border);
}
.profile-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
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
}
.value {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
}
.meta {
  flex: 1;
  min-width: 0;
}
.name {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  line-height: 1.35;
  margin: 0 0 2px 0;
}
.tags {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.card-content {
  padding: 10px 12px;
}
.alerts-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.alerts-grid > * {
  grid-column: span 12;
}
.alert-card {
  border: 1px solid var(--border);
  border-left: 4px solid var(--el-color-primary);
  border-radius: 8px;
  padding: 16px 16px;
  background: #fff;
}
.alert-title {
  font-weight: 700;
  margin-bottom: 6px;
  color: #111827;
}
.alert-desc {
  color: #6b7280;
  margin-bottom: 8px;
}
.alert-actions {
  display: inline-flex;
  gap: 8px;
}
.list-card {
  margin-top: 16px;
}
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-title {
  font-weight: 600;
  color: #303133;
}
.pagination-container {
  margin-top: 16px;
  text-align: right;
}
.cards-row .card.flat.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.stat-content {
  display: flex;
  align-items: center;
}
.stat-info {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
}
.stat-number {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}
.stat-label {
  color: #6b7280;
  font-size: 0.9rem;
}

.stat-icon {
  font-size: 18px;
  color: var(--brand-500, #9a56b5);
  margin-right: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(154, 86, 181, 0.1);
}

.table-wrapper {
  width: 100%;
  overflow: auto;
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
.data-table thead th.sticky-right {
  position: sticky;
  right: 0;
  z-index: 2;
  background: var(--background);
  border-left: 1px solid var(--border);
}
.data-table tbody td.sticky-right {
  position: sticky;
  right: 0;
  z-index: 1;
  background: #fff;
  border-left: 1px solid var(--border);
}
.data-table tbody tr:hover td.sticky-right {
  background: #f9fafb;
}
.empty-cell {
  text-align: center;
  color: #9ca3af;
  padding: 24px 0;
}
.row-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}
.share-checkin-btn {
  padding: 4px 6px !important;
  min-width: auto;
}
.share-checkin-btn:hover {
  color: var(--brand-500, #9a56b5);
}
</style>
