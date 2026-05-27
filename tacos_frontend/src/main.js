import { createApp } from 'vue'
import App from './App.vue'

// UI库
import 'vue-sonner/style.css'
import './assets/styles/theme.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 路由与状态管理
import router from './router'
import store from './store'
// 初始化全局时区设置（Asia/Shanghai）
import './utils/format'

// 全局样式与进度条样式
import './assets/styles/main.scss'
import 'nprogress/nprogress.css'

// 创建应用实例
const app = createApp(App)

// 使用插件（迁移期间临时保留 Element Plus 以避免未迁移页面报错）
app.use(router)
app.use(store)
app.use(ElementPlus)

// 在挂载前同步校验登录状态，确保刷新后角色可用
// 不阻塞首屏过久：无论成功与否都继续挂载
;(async () => {
  try {
    // 尝试从Cookie读取token并拉取用户信息
    // 这样Dashboard等页面的角色判断在首屏就能生效
    await store.dispatch('auth/checkAuth')
  } catch (e) {
    // 忽略错误，继续挂载
  } finally {
    app.mount('#app')
  }
})()
