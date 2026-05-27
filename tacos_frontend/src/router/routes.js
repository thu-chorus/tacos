export default [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: {
      title: '首页',
      noSidebar: true
    }
  },

  // 活动模块
  {
    path: '/events',
    name: 'Events',
    meta: {
      title: '活动'
    },
    children: [
      {
        path: '',
        name: 'EventList',
        component: () => import('@/views/events/EventList.vue'),
        meta: {
          title: '活动列表'
        }
      },
      {
        path: 'create',
        name: 'EventCreate',
        component: () => import('@/views/events/EventForm.vue'),
        meta: {
          title: '创建活动',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          showBackButton: true,
          isFormPage: true
        }
      },
      {
        path: ':id',
        name: 'EventDetail',
        component: () => import('@/views/events/EventDetail.vue'),
        meta: {
          title: '活动详情',
          showBackButton: true,
          backTo: '/events'
        }
      },
      {
        path: ':id/assignments/:assignmentId',
        name: 'AssignmentDetail',
        component: () => import('@/views/events/AssignmentDetail.vue'),
        meta: {
          title: '作业详情',
          requiresAuth: true,
          showBackButton: true
        }
      },
      {
        path: ':id/assignments/:assignmentId/manage',
        name: 'AssignmentManage',
        component: () => import('@/views/events/AssignmentManage.vue'),
        meta: {
          title: '作业管理',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          allowEventAdmin: true,
          showBackButton: true
        }
      },
      {
        path: ':id/checkin/:sessionId',
        name: 'CheckinSessionDetail',
        component: () => import('@/views/events/EventCheckinStats.vue'),
        meta: {
          title: '签到详情',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          allowEventAdmin: true,
          showBackButton: true
        }
      },
      {
        path: ':id/edit',
        name: 'EventEdit',
        component: () => import('@/views/events/EventForm.vue'),
        meta: {
          title: '编辑活动',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          allowEventAdmin: true,
          showBackButton: true,
          isFormPage: true
        }
      },
      {
        path: ':id/checkin-share',
        name: 'CheckinShare',
        component: () => import('@/views/events/CheckinShare.vue'),
        meta: {
          title: '签到分享',
          requiresAuth: true,
          noSidebar: true
        }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      title: '登录',
      noSidebar: true
    }
  },
  {
    path: '/first-login',
    name: 'FirstLogin',
    component: () => import('@/views/FirstLogin.vue'),
    meta: {
      title: '完善个人信息',
      requiresAuth: true,
      noSidebar: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: '仪表板',
      requiresAuth: true
    }
  },

  // 人事管理模块
  {
    path: '/personnel',
    name: 'Personnel',
    meta: {
      title: '人事管理',
      requiresAuth: true
    },
    children: [
      {
        path: 'members',
        name: 'MemberList',
        component: () => import('@/views/personnel/MemberList.vue'),
        meta: {
          title: '队员列表',
          requiresAuth: true
        }
      },
      {
        path: 'members/create',
        name: 'MemberCreate',
        component: () => import('@/views/personnel/MemberForm.vue'),
        meta: {
          title: '新增队员',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          isFormPage: true
        }
      },
      {
        path: 'members/:id',
        name: 'MemberDetail',
        component: () => import('@/views/personnel/MemberDetail.vue'),
        meta: {
          title: '队员详情',
          requiresAuth: true,
          showBackButton: true
        }
      },
      {
        path: 'members/:id/edit',
        name: 'MemberEdit',
        component: () => import('@/views/personnel/MemberForm.vue'),
        meta: {
          title: '编辑队员',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          allowSelfEdit: true,
          showBackButton: true,
          isFormPage: true
        }
      },
      {
        path: 'instructors',
        name: 'InstructorList',
        component: () => import('@/views/personnel/InstructorList.vue'),
        meta: {
          title: '外请教师',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin']
        }
      },
      {
        path: 'instructors/create',
        name: 'InstructorCreate',
        component: () => import('@/views/personnel/InstructorForm.vue'),
        meta: {
          title: '新增教师',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          showBackButton: true,
          backTo: '/personnel/instructors',
          isFormPage: true
        }
      },
      {
        path: 'instructors/:id/edit',
        name: 'InstructorEdit',
        component: () => import('@/views/personnel/InstructorForm.vue'),
        meta: {
          title: '编辑教师',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          showBackButton: true,
          backTo: '/personnel/instructors',
          isFormPage: true
        }
      }
    ]
  },

  // 谱务管理模块
  {
    path: '/sheets',
    name: 'Sheets',
    meta: {
      title: '谱务管理'
    },
    children: [
      {
        path: '',
        name: 'SheetList',
        component: () => import('@/views/sheets/SheetList.vue'),
        meta: {
          requiresAuth: true,
          title: '乐谱列表'
        }
      },
      {
        path: 'upload',
        name: 'SheetUpload',
        component: () => import('@/views/sheets/SheetUpload.vue'),
        meta: {
          title: '上传乐谱',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          showBackButton: true,
          isFormPage: true
        }
      },
      {
        path: ':id',
        name: 'SheetDetail',
        component: () => import('@/views/sheets/SheetDetail.vue'),
        meta: {
          title: '乐谱详情',
          requiresAuth: true,
          showBackButton: true
        }
      },
      {
        path: ':id/edit',
        name: 'SheetEdit',
        component: () => import('@/views/sheets/SheetEdit.vue'),
        meta: {
          title: '编辑乐谱',
          requiresAuth: true,
          roles: ['SuperAdmin', 'Admin'],
          showBackButton: true,
          isFormPage: true
        }
      }
    ]
  },

  // 个人中心
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/Profile.vue'),
    meta: {
      title: '个人中心',
      requiresAuth: true
    }
  },

  // 系统管理：称号
  {
    path: '/titles',
    name: 'TitleManagement',
    component: () => import('@/views/admin/TitleManagement.vue'),
    meta: {
      title: '称号管理',
      requiresAuth: true,
      roles: ['SuperAdmin', 'Admin']
    }
  },
  {
    path: '/titles/:id',
    name: 'TitleDetail',
    component: () => import('@/views/admin/TitleDetail.vue'),
    meta: {
      title: '称号详情',
      requiresAuth: true,
      roles: ['SuperAdmin', 'Admin'],
      showBackButton: true,
      backTo: '/titles'
    }
  },
  // 系统管理：公告
  {
    path: '/announcements',
    name: 'AnnouncementManagement',
    component: () => import('@/views/admin/AnnouncementManagement.vue'),
    meta: {
      title: '公告管理',
      requiresAuth: true,
      roles: ['SuperAdmin', 'Admin'],
      showBackButton: true,
      backTo: '/dashboard'
    }
  },

  // 错误页面
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/403.vue'),
    meta: {
      title: '权限不足',
      showBackButton: true
    }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      title: '页面不存在',
      showBackButton: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    showBackButton: true
  }
]
