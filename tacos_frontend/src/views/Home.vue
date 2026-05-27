<template>
  <div class="home-page">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="logo">
            <span class="logo-text">TaCOS</span>
          </span>
        </h1>
        <h2 class="hero-subtitle">清华合唱队在线系统</h2>
        <p class="hero-description">
          Tsinghua Chorus Online System - 提升清华大学学生艺术团合唱队内部管理效率的在线信息系统
        </p>
        <div class="hero-actions">
          <button
            class="btn-modern primary"
            @click="navigateToLogin"
            v-if="!isLoggedIn"
            style="
              min-width: 160px;
              border-color: var(--brand-300);
              margin-left: 0;
              box-shadow: 0 2px 8px rgba(154, 86, 181, 0.07);
              border-width: 2px;
            "
          >
            立即登录
          </button>
          <button
            class="btn-modern primary"
            @click="navigateToDashboard"
            v-else
            style="
              min-width: 160px;
              border-color: var(--brand-300);
              margin-left: 0;
              box-shadow: 0 2px 8px rgba(154, 86, 181, 0.07);
              border-width: 2px;
            "
          >
            进入系统
          </button>
        </div>
      </div>
    </div>

    <div class="features-section">
      <div class="container">
        <h3 class="section-title">核心功能</h3>
        <div class="features-stack">
          <div class="feature-card">
            <div class="card-header">
              <div class="feature-icon"><i-lucide-user /></div>
              <h4 class="feature-title">人事管理</h4>
            </div>
            <p class="feature-description">
              为每一位合唱队员创建、管理、查询和维护个人档案，支持队员信息的系统化管理
            </p>
          </div>

          <div class="feature-card">
            <div class="card-header">
              <div class="feature-icon"><i-lucide-file-text /></div>
              <h4 class="feature-title">谱务管理</h4>
            </div>
            <p class="feature-description">
              提供安全的乐谱上传、管理和下载平台，支持动态水印确保乐谱安全和可追溯性
            </p>
          </div>

          <div class="feature-card">
            <div class="card-header">
              <div class="feature-icon"><i-lucide-sparkles /></div>
              <h4 class="feature-title">丰富功能</h4>
            </div>
            <p class="feature-description">
              支持活动创建、作业管理、签到管理，内建称呼系统、公告系统等有趣内容
            </p>
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
import {
  User as LucideUser,
  FileText as LucideFileText,
  Sparkles as LucideSparkles
} from 'lucide-vue-next'
import SiteFooter from '@/components/common/SiteFooter.vue'

export default {
  name: 'Home',
  components: {
    'i-lucide-user': LucideUser,
    'i-lucide-file-text': LucideFileText,
    'i-lucide-sparkles': LucideSparkles,
    SiteFooter
  },
  setup() {
    const router = useRouter()
    const store = useStore()

    const stats = reactive({
      memberCount: 0,
      sheetCount: 0,
      downloadCount: 0
    })

    const isLoggedIn = computed(() => store.getters['auth/isLoggedIn'])

    const navigateToLogin = () => {
      router.push('/login')
    }

    const navigateToDashboard = () => {
      router.push('/dashboard')
    }

    const loadStats = async () => {
      try {
        // 这里可以调用API获取统计数据

        // 模拟数据
        stats.memberCount = 120
        stats.sheetCount = 85
        stats.downloadCount = 1250
      } catch (error) {
        console.error('Failed to load stats:', error)
      }
    }

    onMounted(() => {
      loadStats()
    })

    return {
      stats,
      isLoggedIn,
      navigateToLogin,
      navigateToDashboard
    }
  }
}
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
}

.hero-section {
  background: linear-gradient(135deg, #6a2c86 0%, #9a56b5 100%);
  color: white;
  padding: 100px 0;
  text-align: center;

  .hero-content {
    max-width: 800px;
    margin: 0 auto;
    padding: 0 20px;
  }

  .hero-title {
    font-size: 4rem;
    font-weight: bold;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  }

  .logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
  }
  .logo-mark {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--brand-500) 0%, var(--brand-700) 100%);
    box-shadow: 0 4px 16px rgba(154, 86, 181, 0.25);
  }
  .logo-text {
    letter-spacing: 0.5px;
  }

  .hero-subtitle {
    font-size: 2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
  }

  .hero-description {
    font-size: 1.2rem;
    line-height: 1.6;
    margin-bottom: 3rem;
    opacity: 0.8;
  }

  .hero-actions {
    .el-button {
      padding: 15px 30px;
      font-size: 1.1rem;
    }
  }
}

.features-section {
  padding: 80px 0;
  background: #f8f9fa;

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }

  .section-title {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
  }

  .features-stack {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.25rem;
    max-width: 720px;
    margin: 0 auto;
  }

  .feature-card {
    background: #fff;
    padding: 1.25rem 1.25rem 1rem;
    border-radius: 12px;
    border: 1px solid rgba(154, 86, 181, 0.18);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    transition:
      border-color 0.2s,
      box-shadow 0.2s;
  }
  .feature-card:hover {
    border-color: var(--brand-300);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
  }
  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
  }
  .feature-icon {
    font-size: 22px;
    line-height: 1;
    color: $primary-color;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: rgba(154, 86, 181, 0.1);
  }
  .feature-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
  }
  .feature-description {
    color: #4b5563;
    line-height: 1.65;
    margin-top: 4px;
  }
}

.stats-section {
  padding: 80px 0;
  background: white;

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }

  .section-title {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: #333;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
  }

  .stat-item {
    text-align: center;

    .stat-number {
      font-size: 3rem;
      font-weight: bold;
      color: $primary-color;
      margin-bottom: 0.5rem;
    }

    .stat-label {
      font-size: 1.2rem;
      color: #666;
    }
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 60px 0;

    .hero-title {
      font-size: 3rem;
    }

    .hero-subtitle {
      font-size: 1.5rem;
    }

    .hero-description {
      font-size: 1rem;
    }
  }

  .features-section,
  .stats-section {
    padding: 60px 0;

    .section-title {
      font-size: 2rem;
    }
  }
}
</style>
