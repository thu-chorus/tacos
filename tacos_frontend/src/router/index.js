import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import routes from './routes'
import store from '@/store'
import { getEventDetail } from '@/api/events'
import { getProfile } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫：支持 requiresAuth 与 roles 元信息
router.beforeEach(async (to, from, next) => {
  NProgress.start()

  try {
    // 若持有token但store未初始化用户信息，尝试同步
    // 修复：不仅检查isLoggedIn，还要检查用户信息是否已加载
    if (!store.getters['auth/isLoggedIn'] || !store.getters['auth/user']) {
      await store.dispatch('auth/checkAuth')
    }

    const requiresAuth = to.matched.some(record => record.meta && record.meta.requiresAuth)
    const requiredRoles = to.matched.map(record => (record.meta && record.meta.roles) || []).flat()

    // 需要登录
    if (requiresAuth && !store.getters['auth/isLoggedIn']) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }

    // 全局首次登录和成员档案补全强制跳转到 /first-login
    // 避免与登录页、首次登录页自身相互跳转造成循环
    if (
      store.getters['auth/isLoggedIn'] &&
      store.getters['auth/user'] &&
      (store.getters['auth/user'].is_first_login ||
        store.getters['auth/user'].needs_profile_setup) &&
      to.name !== 'FirstLogin' &&
      to.name !== 'Login'
    ) {
      return next({ path: '/first-login' })
    }

    // 首次登录页面的特殊处理
    if (to.name === 'FirstLogin') {
      // 如果用户已登录，检查用户信息是否完整
      if (store.getters['auth/isLoggedIn']) {
        // 这里可以添加更复杂的检查逻辑，比如检查Member信息是否完整
        // 暂时允许已登录用户访问首次登录页面
      } else {
        return next({ path: '/login' })
      }
    }

    // 需要角色（或事件管理员、或编辑自己的信息）
    const needsEventAdmin = to.matched.some(record => record.meta && record.meta.allowEventAdmin)
    const allowSelfEdit = to.matched.some(record => record.meta && record.meta.allowSelfEdit)
    if (requiredRoles && requiredRoles.length > 0) {
      const hasAnyRole = requiredRoles.some(role => store.getters['auth/hasRole'](role))
      if (!hasAnyRole) {
        // 检查是否允许编辑自己的个人信息
        if (allowSelfEdit) {
          const memberIdParam = to.params && to.params.id
          const memberId = Array.isArray(memberIdParam) ? memberIdParam[0] : memberIdParam
          if (memberId) {
            try {
              const profileRes = await getProfile()
              const myMemberId = profileRes?.data?.member?.id
              if (myMemberId && myMemberId === memberId) {
                // 用户正在编辑自己的信息，允许访问
                return next()
              }
            } catch (e) {
              // 获取个人信息失败，继续检查其他权限
            }
          }
        }

        if (needsEventAdmin) {
          // 当路由允许事件管理员时，检查当前用户是否为该活动的管理员
          const eventIdParam = to.params && (to.params.id || to.params.eventId)
          const eventId = Array.isArray(eventIdParam) ? eventIdParam[0] : eventIdParam
          if (!eventId) {
            return next({ path: '/403' })
          }
          try {
            const res = await getEventDetail(eventId)
            // 活动基础序列化器返回 relation 字段表示用户与活动的关系
            // 字段 relation === 'event_admin' 表示用户是活动管理员
            const isEventAdmin = res?.data?.relation === 'event_admin'
            if (!isEventAdmin) {
              return next({ path: '/403' })
            }
          } catch (e) {
            return next({ path: '/403' })
          }
        } else {
          return next({ path: '/403' })
        }
      }
    }

    return next()
  } catch (e) {
    // 出错时兜底放行到登录页或原路由
    if (to.meta && to.meta.requiresAuth) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    return next()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
