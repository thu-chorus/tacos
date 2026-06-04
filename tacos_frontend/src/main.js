import { createApp } from 'vue'
import App from './App.vue'

// UI库
import 'vue-sonner/style.css'
import './assets/styles/theme.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import {
  ArrowLeft as LucideArrowLeft,
  BadgeCheck as LucideBadgeCheck,
  CalendarPlus as LucideCalendarPlus,
  Check as LucideCheck,
  ClipboardCheck as LucideClipboardCheck,
  ClipboardList as LucideClipboardList,
  Copy as LucideCopy,
  Download as LucideDownload,
  ExternalLink as LucideExternalLink,
  Eye as LucideEye,
  FileText as LucideFileText,
  GraduationCap as LucideGraduationCap,
  House as LucideHouse,
  ImagePlus as LucideImagePlus,
  KeyRound as LucideKeyRound,
  Link as LucideLink,
  ListChecks as LucideListChecks,
  LogIn as LucideLogIn,
  MapPin as LucideMapPin,
  Navigation as LucideNavigation,
  Pencil as LucidePencil,
  Plus as LucidePlus,
  RotateCcw as LucideRotateCcw,
  Save as LucideSave,
  Search as LucideSearch,
  Send as LucideSend,
  Settings as LucideSettings,
  Share2 as LucideShare2,
  ShieldCheck as LucideShieldCheck,
  Trash2 as LucideTrash2,
  Upload as LucideUpload,
  UserPlus as LucideUserPlus,
  X as LucideX
} from 'lucide-vue-next'

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

const globalIcons = {
  'i-lucide-arrow-left': LucideArrowLeft,
  'i-lucide-badge-check': LucideBadgeCheck,
  'i-lucide-calendar-plus': LucideCalendarPlus,
  'i-lucide-check': LucideCheck,
  'i-lucide-clipboard-check': LucideClipboardCheck,
  'i-lucide-clipboard-list': LucideClipboardList,
  'i-lucide-copy': LucideCopy,
  'i-lucide-download': LucideDownload,
  'i-lucide-external-link': LucideExternalLink,
  'i-lucide-eye': LucideEye,
  'i-lucide-file-text': LucideFileText,
  'i-lucide-graduation-cap': LucideGraduationCap,
  'i-lucide-house': LucideHouse,
  'i-lucide-image-plus': LucideImagePlus,
  'i-lucide-key-round': LucideKeyRound,
  'i-lucide-link': LucideLink,
  'i-lucide-list-checks': LucideListChecks,
  'i-lucide-log-in': LucideLogIn,
  'i-lucide-map-pin': LucideMapPin,
  'i-lucide-navigation': LucideNavigation,
  'i-lucide-pencil': LucidePencil,
  'i-lucide-plus': LucidePlus,
  'i-lucide-rotate-ccw': LucideRotateCcw,
  'i-lucide-save': LucideSave,
  'i-lucide-search': LucideSearch,
  'i-lucide-send': LucideSend,
  'i-lucide-settings': LucideSettings,
  'i-lucide-share-2': LucideShare2,
  'i-lucide-shield-check': LucideShieldCheck,
  'i-lucide-trash-2': LucideTrash2,
  'i-lucide-upload': LucideUpload,
  'i-lucide-user-plus': LucideUserPlus,
  'i-lucide-x': LucideX
}

Object.entries(globalIcons).forEach(([name, component]) => {
  app.component(name, component)
})

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
