<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1 class="login-title">TaCOS</h1>
        <p class="login-subtitle">清华合唱队在线系统</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin" novalidate>
        <div class="form-item">
          <label class="form-label" for="user_id">学号</label>
          <div class="input-wrapper">
            <input
              id="user_id"
              v-model="loginForm.user_id"
              placeholder="请输入学号"
              inputmode="numeric"
              pattern="\\d{10}"
              class="input-modern"
              autocomplete="username"
              required
            />
          </div>
          <p v-if="fieldErrors.user_id" class="field-error">{{ fieldErrors.user_id }}</p>
        </div>

        <div class="form-item">
          <label class="form-label" for="password">密码</label>
          <div class="input-wrapper">
            <input
              id="password"
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              class="input-modern"
              autocomplete="current-password"
              required
              minlength="6"
            />
          </div>
          <p v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</p>
        </div>

        <!-- <div class="form-item form-inline">
          <label class="checkbox-modern">
            <input type="checkbox" v-model="rememberMe" />
            <span>记住我</span>
          </label>
        </div> -->

        <div class="form-item">
          <button type="submit" class="btn-modern primary w-full" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>
      </form>

      <div class="login-footer">
        <p class="footer-text">如有问题，请联系管理员</p>
      </div>
    </div>

    <div class="login-bg">
      <div class="bg-decoration"></div>
    </div>
    <SiteFooter dark fixed />
  </div>
</template>

<script>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { notify } from '@/utils/notify'
import SiteFooter from '@/components/common/SiteFooter.vue'

export default {
  name: 'Login',
  components: {
    SiteFooter
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()

    const loginFormRef = ref()
    const loading = ref(false)
    const rememberMe = ref(false)

    const loginForm = reactive({
      user_id: '',
      password: ''
    })

    const fieldErrors = reactive({ user_id: '', password: '' })

    const handleLogin = async () => {
      try {
        fieldErrors.user_id = ''
        fieldErrors.password = ''

        if (!/^\d{10}$/.test(loginForm.user_id)) {
          fieldErrors.user_id = '学号应为10位数字'
          return
        }
        if (!loginForm.password || loginForm.password.length < 6) {
          fieldErrors.password = '密码长度不能少于6位'
          return
        }

        loading.value = true

        const response = await store.dispatch('auth/login', loginForm)

        notify.success('登录成功')

        // 检查是否是首次登录
        if (response.data && response.data.is_first_login) {
          notify.info('检测到您是首次登录，请完善个人信息并修改密码')
          router.push('/first-login')
          return
        }

        // 跳转到目标页面或默认页面
        const redirectPath = route.query.redirect || '/dashboard'
        router.push(redirectPath)
      } catch (error) {
        console.error('Login error:', error)

        // 处理详细的错误信息
        const resp = error && error.response
        const data = resp && resp.data
        let message = '登录失败'
        let hasFieldError = false

        if (data && typeof data === 'object') {
          // 处理字段级别的错误并设置表单错误状态
          if (data.user_id && Array.isArray(data.user_id)) {
            message = data.user_id[0]
            hasFieldError = true
            // 清除表单验证并聚焦到学号字段
            loginFormRef.value?.clearValidate()
            // 聚焦到学号输入框
            setTimeout(() => {
              const userIdInput = document.querySelector('input[placeholder="请输入学号"]')
              if (userIdInput) {
                userIdInput.focus()
              }
            }, 100)
          } else if (data.password && Array.isArray(data.password)) {
            message = data.password[0]
            hasFieldError = true
            // 清除表单验证并聚焦到密码字段
            loginFormRef.value?.clearValidate()
            // 聚焦到密码输入框
            setTimeout(() => {
              const passwordInput = document.querySelector('input[placeholder="请输入密码"]')
              if (passwordInput) {
                passwordInput.focus()
              }
            }, 100)
          } else if (data.message) {
            message = data.message
          } else if (data.detail) {
            message = data.detail
          } else if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
            message = data.non_field_errors[0]
          }
        } else if (error.message) {
          message = error.message
        }

        // 根据错误类型显示不同的提示
        notify.error(message, { duration: hasFieldError ? 4000 : 3000 })
      } finally {
        loading.value = false
      }
    }

    return {
      loginFormRef,
      loginForm,
      fieldErrors,
      loading,
      rememberMe,
      handleLogin
    }
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #6a2c86 0%, #9a56b5 100%);
}

.login-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
  z-index: 2;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
  color: white;

  .login-title {
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  }

  .login-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
  }
}

.login-form {
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);

  .el-form-item {
    margin-bottom: 1.5rem;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .el-input {
    --el-input-border-radius: 8px;
  }

  .el-button {
    border-radius: 8px;
    font-weight: 600;
  }
}

.login-footer {
  margin-top: 2rem;
  text-align: center;

  .footer-text {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
  }
}

.login-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  overflow: hidden;

  .bg-decoration {
    position: absolute;
    width: 200%;
    height: 200%;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="rgba(255,255,255,0.1)"/></svg>')
      repeat;
    animation: float 20s ease-in-out infinite;
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

@media (max-width: 768px) {
  .login-container {
    padding: 1rem;
    max-width: 350px;
  }

  .login-header {
    .login-title {
      font-size: 2.5rem;
    }

    .login-subtitle {
      font-size: 1rem;
    }
  }

  .login-form {
    padding: 1.5rem;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: 0.5rem;
    max-width: 300px;
  }

  .login-form {
    padding: 1rem;
  }
}
</style>
