# TaCOS Frontend

TaCOS (Tsinghua Chorus Online System) 前端应用，基于 Vue.js 3 构建的现代化单页面应用。

## 项目概述

清华合唱队在线系统前端，为清华大学学生艺术团合唱队提供人事管理、谱务管理、活动管理和签到系统等功能。

## 技术栈

- **框架**: Vue.js 3.3.4
- **构建工具**: Vite 4.4.9
- **状态管理**: Vuex 4.1.0
- **路由**: Vue Router 4.2.4
- **UI框架**: Element Plus 2.3.9 + shadcn-vue + Tailwind CSS 3.3.3 + Vant 4.6.2 + NutUI 4.0.8
- **HTTP客户端**: Axios 1.5.0
- **样式**: SCSS/Sass
- **图表**: ECharts 5.4.3 + Vue-ECharts 6.6.0
- **工具库**: Day.js 1.11.18, js-cookie 3.0.5, nprogress 0.2.0

## 功能特性

### 用户认证与权限
- 🔐 用户登录/登出
- 👤 用户信息管理
- 🔑 首次登录引导（完善个人信息）
- 🎯 基于角色的权限控制（SuperAdmin、Admin、Member）
- 🛡️ 路由守卫和权限验证

### 人事管理
- 👥 队员档案管理（创建、编辑、查看、删除）
- 🖼️ 成员头像上传、裁剪和点击预览
- 👨‍🏫 外请教师管理
- 🤝 校友状态与联系窗口
- 📊 队员信息统计
- 🏫 院系管理配置
- 📋 队员列表筛选与搜索

### 谱务管理
- 📄 乐谱上传与管理
- 📥 乐谱下载（支持水印）
- 👀 校友可见乐谱范围控制
- 📊 下载记录跟踪
- 🔍 乐谱搜索与筛选
- 📄 乐谱详情展示

### 活动管理
- 🗓️ 活动创建与编辑
- 📢 活动公告发布
- 👀 活动可见性控制
- 🤝 校友可见活动控制
- 📝 活动报名管理
- 📅 活动列表与详情展示
- 🔍 活动搜索与筛选（支持"仅显示我参加的活动"）

### 签到系统
- ✅ 多种签到方式（密码签到、定位签到）
- 📱 签到会话管理
- 📊 签到统计与记录
- 🎯 实时签到状态查看
- 📈 签到数据可视化

### 作业系统
- 📝 作业发布与管理
- 📎 作业附件上传（支持多文件）
- 📤 作业提交（文本 + 文件）
- 📋 提交列表查看与筛选
- ✏️ 作业批改与评分
- 📊 提交状态统计

### 系统管理
- ⚙️ 系统设置管理
- 📢 公告管理
- 🏷️ 称号管理
- 👥 用户管理

### 界面特性
- 📱 响应式设计
- 🎨 现代化UI界面
- 💫 流畅的页面切换
- 💫 加载进度条
- 🌙 友好的用户体验

## 开发环境要求

- Node.js >= 20.0.0
- npm >= 9.0.0

## 安装和启动

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
# 开发服务器默认运行在 http://localhost:3000
# 已配置代理，后端 API 请求自动转发到 http://localhost:8000
npm run serve
```

如需修改后端 API 地址，请从 `.env.example` 创建本地环境文件：
- 开发环境：创建 `.env.local`
- 生产构建：创建 `.env.production.local`

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 目录结构

```
src/
├── api/               # API接口模块
│   ├── auth.js        # 认证相关API
│   ├── events.js      # 活动相关API
│   ├── personnel.js   # 人事管理API
│   ├── sheets.js      # 谱务管理API
│   ├── common.js      # 通用API
│   └── index.js       # API配置和请求封装
├── assets/            # 静态资源
│   └── styles/        # 样式文件
│       ├── main.scss       # 主样式文件
│       ├── variables.scss  # SCSS变量
│       ├── mixins.scss     # SCSS混入
│       └── components.scss # 组件样式
├── components/        # 公共组件
│   └── common/        # 通用组件
│       ├── SiteFooter.vue  # 页脚组件
│       └── TitleBadge.vue  # 标题徽章组件
├── router/            # 路由配置
│   ├── index.js       # 路由实例和导航守卫
│   └── routes.js      # 路由定义
├── store/             # Vuex状态管理
│   ├── index.js       # Store实例
│   └── modules/       # Store模块
│       ├── auth.js    # 认证状态
│       ├── common.js  # 公共状态
│       ├── personnel.js # 人事状态
│       └── sheets.js  # 谱务状态
├── utils/             # 工具函数
│   ├── auth.js        # 认证工具
│   ├── constants.js   # 常量定义
│   ├── download.js    # 下载工具
│   ├── format.js      # 格式化工具
│   └── validation.js  # 验证工具
├── views/             # 页面组件
│   ├── Home.vue       # 首页
│   ├── Login.vue      # 登录页
│   ├── FirstLogin.vue # 首次登录页
│   ├── Dashboard.vue  # 仪表板
│   ├── admin/         # 管理员页面
│   │   ├── AnnouncementManagement.vue # 公告管理
│   │   ├── SystemSettings.vue         # 系统设置
│   │   ├── TitleManagement.vue        # 称号管理
│   │   └── UserManagement.vue         # 用户管理
│   ├── error/         # 错误页面
│   │   ├── 403.vue    # 无权限页面
│   │   └── 404.vue    # 未找到页面
│   ├── events/        # 活动模块
│   │   ├── EventList.vue           # 活动列表
│   │   ├── EventDetail.vue         # 活动详情
│   │   ├── EventForm.vue           # 活动表单
│   │   ├── EventCheckinStats.vue   # 签到统计
│   │   ├── AssignmentDetail.vue    # 作业详情
│   │   └── AssignmentManage.vue    # 作业管理
│   ├── personnel/     # 人事管理页面
│   │   ├── MemberList.vue          # 队员列表
│   │   ├── MemberDetail.vue        # 队员详情
│   │   ├── MemberForm.vue          # 队员表单
│   │   ├── InstructorList.vue      # 教师列表
│   │   └── InstructorForm.vue      # 教师表单
│   ├── profile/       # 个人中心
│   │   ├── Profile.vue             # 个人信息
│   │   └── ChangePassword.vue      # 修改密码
│   └── sheets/        # 谱务管理页面
│       ├── SheetList.vue           # 乐谱列表
│       ├── SheetDetail.vue         # 乐谱详情
│       ├── SheetEdit.vue           # 乐谱编辑
│       └── SheetUpload.vue         # 乐谱上传
├── App.vue            # 根组件
└── main.js            # 应用入口
```

## 可用脚本

- `npm run serve` - 启动开发服务器（默认端口 3000）
- `npm run build` - 构建生产版本
- `npm run preview` - 预览生产版本
- `npm run test:unit` - 运行单元测试（Vitest）
- `npm run test:e2e` - 运行E2E测试（Cypress）
- `npm run test:e2e:dev` - 打开Cypress测试界面
- `npm run lint` - 代码检查和修复（ESLint）
- `npm run format` - 代码格式化（Prettier）

## 环境变量

### 本地环境文件

仓库提供 `.env.example` 作为模板。实际环境文件不会提交到版本控制。

### 开发环境 (.env.local)

```env
# API基础URL（也可以使用 /api/v1 走 Vite proxy）
VITE_API_BASE_URL=/api/v1

# 是否开启调试模式
VITE_DEBUG=true
VITE_DEV_MODE=true
```

### 生产构建 (.env.production.local)

```env
# API基础URL（生产环境）
VITE_API_BASE_URL=/api/v1

# 关闭调试模式
VITE_DEBUG=false
VITE_DEV_MODE=false
```

说明：
- `.env.local` 和 `.env.production.local` 用于本机覆盖变量，不提交到版本控制
- 开发服务器已配置代理，API 请求会自动转发到 `http://localhost:8000`
- 环境变量必须以 `VITE_` 开头才能在前端代码中使用

## 编码规范

### Vue组件命名
- 文件名使用 PascalCase（如：`MemberList.vue`、`EventDetail.vue`）
- 组件名使用 PascalCase
- 路由名使用 PascalCase

### JavaScript
- 变量名使用 camelCase（如：`userName`、`eventList`）
- 常量使用 UPPER_SNAKE_CASE（如：`API_BASE_URL`、`DEPARTMENTS`）
- 函数名使用 camelCase（如：`getUserInfo`、`handleSubmit`）
- 类名使用 PascalCase

### CSS/SCSS
- 类名使用 kebab-case（如：`member-list`、`event-card`）
- 变量名使用 kebab-case（如：`$primary-color`、`$border-radius`）

### 代码风格
- 使用 ESLint 进行代码检查
- 使用 Prettier 进行代码格式化
- 提交前运行 `npm run lint` 确保代码质量

## API接口

后端API接口遵循RESTful设计规范，基础URL为 `/api/v1`。

### 认证相关
- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `GET /auth/me` - 获取当前用户信息
- `GET /auth/profile` - 获取个人资料
- `PUT /auth/profile` - 更新个人资料
- `POST /auth/refresh` - 刷新访问令牌
- `PUT /auth/password` - 修改密码
- `PUT /auth/first-login` - 首次登录完善信息

### 人事管理
- `GET /members/` - 获取队员列表
- `POST /members/` - 创建队员档案
- `GET /members/:public_id/` - 获取队员详情
- `PATCH /members/:public_id/` - 更新队员信息
- `POST /members/:public_id/avatar/` - 上传本人或管理员维护的头像
- `DELETE /members/:public_id/avatar/` - 删除本人或管理员维护的头像
- `DELETE /members/:public_id/` - 删除队员档案
- `GET /alumni-profiles/me/` - 获取当前校友信息
- `PATCH /alumni-profiles/me/` - 更新当前校友信息
- `GET /instructors/` - 获取教师列表
- `POST /instructors/` - 创建教师档案
- `GET /instructors/:public_id/` - 获取教师详情
- `PUT /instructors/:public_id/` - 更新教师信息
- `DELETE /instructors/:public_id/` - 删除教师档案

### 谱务管理
- `GET /sheets/` - 获取乐谱列表
- `POST /sheets/` - 上传乐谱
- `GET /sheets/:public_id/` - 获取乐谱详情
- `PUT /sheets/:public_id/` - 更新乐谱信息
- `DELETE /sheets/:public_id/` - 删除乐谱
- `POST /sheets/:public_id/download/` - 发起乐谱水印下载/预览任务
- `GET /sheets/task/:task_id/` - 轮询任务状态或下载结果
- `GET /sheets/task/:task_id/stream/` - 签名链接流式预览完整乐谱

### 活动管理
- `GET /events/` - 获取活动列表（支持 `only_participated`、搜索、分页）
- `POST /events/` - 创建活动（管理员）
- `GET /events/:public_id/` - 获取活动详情
- `PUT /events/:public_id/` - 更新活动（管理员）
- `DELETE /events/:public_id/` - 删除活动（管理员）
- `POST /events/:public_id/join/` - 报名活动（成员）

### 签到系统
- `GET /events/:public_id/checkin/status/` - 当前签到状态
- `GET /events/:public_id/checkin/sessions/` - 签到会话列表
- `POST /events/:public_id/checkin/start/` - 创建签到会话（管理员）
- `POST /events/:public_id/checkin/begin/` - 开始签到会话（管理员）
- `POST /events/:public_id/checkin/stop/` - 结束签到会话（管理员）
- `POST /events/:public_id/checkin/submit/` - 提交签到（成员；支持密码/定位签到）
- `GET /events/:public_id/checkin/records/` - 签到记录（成员仅看自己，管理员可筛选）
- `DELETE /events/:public_id/checkin/sessions/:session_id/` - 删除签到会话

### 作业管理
- `GET /events/:public_id/assignments/` - 作业列表
- `POST /events/:public_id/assignments/create/` - 创建作业（管理员）
- `GET /events/:public_id/assignments/:assignment_id/` - 作业详情
- `PUT /events/:public_id/assignments/:assignment_id/edit/` - 更新作业（管理员）
- `POST /events/:public_id/assignments/:assignment_id/attachments/` - 上传作业附件（管理员；支持多文件）
- `POST /events/:public_id/assignments/:assignment_id/submit/` - 提交作业（成员；支持文本 + 多文件）
- `GET /events/:public_id/assignments/:assignment_id/submissions/` - 提交列表（管理员可筛选）
- `GET /events/:public_id/assignments/:assignment_id/my-submission/` - 我的提交（成员）
- `POST /events/:public_id/assignments/:assignment_id/grade/` - 批改提交（管理员）

### 系统管理
- `GET /common/announcements/` - 获取公告列表
- `POST /common/announcements/` - 创建公告（管理员）
- `GET /common/titles/` - 获取称号列表
- `POST /common/titles/` - 创建称号（管理员）
- `GET /users/` - 获取用户列表（管理员）

## 权限系统

系统支持基于角色的权限控制（RBAC），包含以下角色：

### 角色定义

- **SuperAdmin（超级管理员）**
  - 拥有系统所有权限
  - 可以管理所有用户、活动、队员、乐谱
  - 可以访问系统设置、公告管理、称号管理

- **Admin（管理员）**
  - 可以创建和管理活动
  - 可以管理队员和教师档案
  - 可以管理乐谱
  - 可以创建签到会话和批改作业
  - 特定活动的管理员可以管理该活动

- **Member（队员）**
  - 可以查看活动列表和详情
  - 可以报名活动
  - 可以参与签到
  - 可以提交作业
  - 可以查看和下载乐谱
  - 可以查看自己的档案信息
  - 首次登录完善信息时必须填写预计毕业时间；管理员创建成员时可暂空

- **Alumni（校友状态）**
  - 可以维护自己的联系窗口，包括当前城市、行业、单位、职位、毕业时间和简介；毕业时间必填，微信、电话、邮箱沿用成员档案
  - 可以查看管理员开放给校友的活动
  - 可以查看管理员开放给校友的乐谱，以及校友可见活动关联的乐谱
  - 不能自行把账号切换为校友状态

### 权限控制实现

- **路由守卫**：在 `router/index.js` 中实现，检查用户认证状态和权限
- **组件级权限**：通过 `v-if` 和用户角色判断显示/隐藏功能
- **API权限**：后端验证用户权限，前端仅做界面控制

## 开发配置

### Vite配置 (vite.config.js)

```javascript
{
  server: {
    port: 3000,           // 开发服务器端口
    open: true,           // 自动打开浏览器
    proxy: {              // API代理配置
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')  // 路径别名
    }
  }
}
```

### SCSS配置

全局变量和混入已自动引入，可在任何组件中直接使用：
- `src/assets/styles/variables.scss` - SCSS变量
- `src/assets/styles/mixins.scss` - SCSS混入

### 构建配置

- **输出目录**: `dist/`
- **资源目录**: `dist/assets/`
- **代码分割**: 自动进行chunk分割优化
- **静态资源**: `public/` 目录中的文件会被直接复制到输出目录

## 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90
- 不支持 IE 浏览器

## 院系管理配置

### 配置院系选项

院系选项可以通过修改常量文件轻松配置，无需修改后端代码：

**配置文件**: `src/utils/constants.js`

```javascript
// 修改此数组来更新院系选项
export const DEPARTMENTS = [
  '电子系',
  '物理系',
  '交叉信息研究院',
  '计算机系',
  // ... 添加或修改院系
  '其他'  // 保持"其他"在最后
]
```

### 使用说明

1. **添加新院系**：在 `DEPARTMENTS` 数组中添加新项目
2. **删除院系**：从数组中移除对应项目
3. **重命名院系**：直接修改数组中的文本
4. **应用更改**：前端重新加载后自动生效

### 相关页面

- 队员创建/编辑表单
- 个人信息管理页面
- 队员详情展示
- 队员列表显示

## 常见问题

### 开发环境启动失败
1. 确认 Node.js 版本 >= 20.0.0
2. 删除 `node_modules` 和 `package-lock.json`，重新运行 `npm install`
3. 检查端口 3000 是否被占用

### API请求失败
1. 确认后端服务已启动（默认 http://localhost:8000）
2. 检查 `.env.local` 中的 API 地址配置
3. 查看浏览器控制台网络请求详情

### 权限相关问题
1. 确认用户已登录且 token 有效
2. 检查用户角色是否有对应权限
3. 清除浏览器缓存和 cookies 后重新登录

## 许可证

Apache License 2.0
