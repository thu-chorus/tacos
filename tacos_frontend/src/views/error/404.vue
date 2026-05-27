<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-icon">
        <el-icon><QuestionFilled /></el-icon>
      </div>
      <h1 class="error-title">404</h1>
      <h2 class="error-subtitle">页面不存在</h2>
      <p class="error-description">抱歉，您访问的页面不存在或已被删除。</p>
      <div class="error-actions">
        <button class="btn-modern primary" @click="goHome">返回首页</button>
        <button class="btn-modern ghost" @click="goBack">返回上页</button>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { QuestionFilled } from '@element-plus/icons-vue'

export default {
  name: 'Error404',
  components: {
    QuestionFilled
  },
  setup() {
    const router = useRouter()

    const goHome = () => {
      router.push('/')
    }

    const goBack = () => {
      router.go(-1)
    }

    return {
      goHome,
      goBack
    }
  }
}
</script>

<style lang="scss" scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.error-content {
  text-align: center;
  color: white;

  .error-icon {
    font-size: 6rem;
    margin-bottom: 2rem;
    opacity: 0.8;
  }

  .error-title {
    font-size: 6rem;
    margin-bottom: 1rem;
    font-weight: bold;
  }

  .error-subtitle {
    font-size: 2rem;
    margin-bottom: 1rem;
  }

  .error-description {
    font-size: 1.2rem;
    margin-bottom: 3rem;
    opacity: 0.9;
    max-width: 500px;
  }

  .error-actions {
    display: flex;
    gap: 16px;
    justify-content: center;
  }
}
</style>
