# TaCOS 开发者文档

**版本**: v2.3.1
**最后更新**: 2026-06-04

## 目录

1. [项目概述](#一项目概述)
2. [技术架构](#二技术架构)
3. [核心模块设计](#三核心模块设计)
4. [API 接口文档](#四api-接口文档)
5. [数据库设计](#五数据库设计)
6. [项目结构](#六项目结构)
7. [配置管理](#七配置管理)
8. [部署运维](#八部署运维)
9. [开发规范](#九开发规范)
10. [更新日志](#十更新日志)
11. [附录](#附录)

## 一、项目概述

### 1.1 项目简介

**TaCOS**（Tsinghua Chorus Online System，清华合唱队在线系统）是为清华大学学生艺术团合唱队开发的综合管理系统，旨在实现队伍管理的数字化、流程化和智能化。

### 1.2 核心功能

| 功能模块 | 描述 |
|---------|------|
| **人事管理** | 队员档案管理、成员头像、教师信息管理、称号系统 |
| **校友系统** | 管理员维护校友状态，校友维护联系窗口 |
| **谱务管理** | 乐谱上传下载、权限控制、水印保护 |
| **活动管理** | 活动创建、报名管理、公告发布 |
| **签到系统** | 密码签到、定位签到、统计分析 |
| **作业系统** | 作业发布、提交批改、成绩管理 |

### 1.3 用户角色

| 角色 | 权限说明 |
|-----|---------|
| **SuperAdmin** | 超级管理员，拥有所有权限 |
| **Admin** | 管理员，负责日常管理工作 |
| **Member** | 普通队员，查看和使用基本功能 |
| **Alumni** | 由 Member 档案状态标识，查看校友可见活动和乐谱，维护联系方式 |

### 1.4 校友系统

校友系统保持轻量边界：

- 成员状态主要由管理员维护，不根据毕业时间自动转换。
- `Member.status` 支持 `ACTIVE`、`ALUMNI`、`INACTIVE`。
- 队员列表明确展示成员状态，并按 `ACTIVE`、`ALUMNI`、`INACTIVE` 优先排序。
- 成员相关列表复用统一排序：状态、梯队、声部、姓名拼音、学号；活动管理员、参与成员、签到统计、作业全员列表和成员导出均遵循该顺序。
- 乐谱列表和活动关联乐谱按曲名拼音排序，外请教师按姓名拼音排序。
- 成员切换为 `ALUMNI` 后创建 `AlumniProfile`，用于当前城市、行业、单位、职位、毕业时间、简介、备注和开放联系开关；微信、电话、邮箱沿用 `Member` 档案字段。`Member.graduate_month` 仍表示预计毕业时间，管理员创建成员时可暂空，用户首次登录补全时必填；`AlumniProfile.graduation_month` 表示校友毕业时间且保存时必填。
- 活动增加 `visible_to_alumni`，校友只看到显式开放给校友的活动，并可报名这些活动。
- 校友只能担任 `visible_to_alumni=true` 活动的活动管理员。
- 乐谱增加 `visible_to_alumni`，校友可查看显式开放给校友的乐谱；关联到校友可见活动的乐谱也会对校友可见。
- 本版本不包含导师制、校友活动组织、自动毕业转状态。

### 1.5 成员生命周期

- `Member.status` 是成员生命周期状态来源，支持 `ACTIVE`、`ALUMNI`、`INACTIVE`。
- `User.is_active` 仅表示平台级账号是否启用，不作为成员状态字段使用。
- 系统每天会将超过 6 个月未登录的 `ACTIVE` 成员设为 `INACTIVE`，`ALUMNI` 不受影响。
- `INACTIVE` 成员登录时会被拒绝，并提示“账号已停用，请联系管理员协助处理”。
- 任意账号若还没有成员档案，登录后会进入首次信息完善流程；管理员权限由 `User.role` 控制。

### 1.6 成员头像

- 成员可上传本人头像，管理员可维护任意成员头像。
- 头像上传支持 JPG、PNG、WebP，大小不超过 2 MB。
- 前端裁剪并上传方形图片；列表、详情和个人页的小头像按圆形展示。
- 点击成员详情头像时展示方形原图，透明图片导出时使用白色背景。

### 1.7 技术特性

- ✅ 前后端分离架构
- ✅ JWT 身份认证
- ✅ RESTful API 设计
- ✅ 异步任务处理（Celery）
- ✅ 响应式 UI 设计
- ✅ 文件安全管理
- ✅ 完整的权限控制

## 二、技术架构

### 2.1 技术栈总览

| 层级 | 主要组件 | 职责 | 下游 |
|------|----------|------|------|
| 前端层 | Vue 3、Vite、Vuex、Tailwind CSS、Element Plus、Vant、NutUI | 页面渲染、路由、状态管理、API 调用 | API 网关 |
| API 网关层 | Nginx | 静态文件服务、HTTPS 终止、反向代理 | 应用层 |
| 应用层 | Gunicorn、Django、Django REST Framework、SimpleJWT | 业务 API、鉴权、权限控制、异步任务调度 | 数据库、Redis、文件存储 |
| 数据层 | PostgreSQL / SQLite | 生产 / 开发测试关系型数据存储 | - |
| 缓存与队列 | Redis、Celery | 缓存、消息队列、后台任务执行 | 应用层、任务结果 |
| 文件存储 | `tacos_media/`、可选 OSS | 乐谱、作业附件、公告图片、水印文件 | 应用层 |

请求链路：浏览器 -> Nginx -> Gunicorn -> Django/DRF -> PostgreSQL、Redis、Celery、文件存储。

### 2.2 前端技术

| 技术 | 版本 | 用途 |
|-----|------|------|
| Vue.js | 3.3+ | 前端框架 |
| Vite | 4.x | 构建工具 |
| Vue Router | 4.2+ | 路由管理 |
| Vuex | 4.1+ | 状态管理 |
| Axios | 1.x | HTTP 客户端 |
| Tailwind CSS | 3.3+ | 样式框架 |
| Element Plus | 2.3+ | PC 端 UI 组件 |
| Vant | 4.6+ | 移动端 UI 组件 |
| NutUI | 4.0+ | 移动端 UI 组件 |
| Day.js | 1.11+ | 日期时间处理 |

前端 API 层对高频读取接口使用内存 TTL 缓存和并发请求合并：个人档案缓存 5 分钟，详情接口缓存 2 分钟，列表接口缓存 30 秒。登录、登出、401 退出和相关写操作会清理或失效对应缓存，避免跨账号或编辑后的旧数据残留。

### 2.3 后端技术

| 技术 | 版本 | 用途 |
|-----|------|------|
| Python | 3.9+ | 编程语言 |
| Django | 4.x | Web 框架 |
| Django REST Framework | 3.x | API 框架 |
| djangorestframework-simplejwt | 最新 | JWT 认证 |
| PostgreSQL | 13+ | 生产数据库 |
| SQLite | 3.x | 开发数据库 |
| Redis | 6+ | 缓存与消息队列 |
| Celery | 5.x | 异步任务 |
| Gunicorn | 最新 | WSGI 服务器 |
| Nginx | 最新 | Web 服务器 |
| reportlab + pypdf | 最新 | PDF 水印处理 |

### 2.4 安全机制

#### 身份认证
- **JWT Token**: 使用 `djangorestframework-simplejwt`
- **密码加密**: BCrypt 算法（`BCryptSHA256PasswordHasher`）
- **Token 刷新**: Access Token 默认 1 天 + Refresh Token 默认 10 天

#### 文件安全
- **访问控制**: 所有文件通过后端 API 鉴权后访问
- **水印保护**: PDF 文件动态添加用户水印
- **路径隐藏**: 使用 `public_id` 代替真实文件路径
- **文件隔离**: 媒体文件存储在 `tacos_media/` 独立目录

#### 权限控制
- **基于角色**: SuperAdmin、Admin、Member 三级权限
- **资源级控制**: 每个 API 端点独立权限验证
- **所有权验证**: 用户只能访问自己的资源

### 2.5 时区与日期时间规范

**全局时区**: `Asia/Shanghai` (UTC+8)

#### 后端规范

```python
# Django 配置
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True  # 数据库存储 UTC，显示转换为本地时间

# 获取当前本地时间
from django.utils import timezone
now = timezone.localtime()
today = timezone.localdate()
current_month = timezone.localdate().month

# 生成时间戳文件名
timestamp = timezone.localtime().strftime('%Y%m%d%H%M%S')
```

#### 前端规范

```javascript
// src/utils/format.js 初始化
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(relativeTime)
dayjs.tz.setDefault('Asia/Shanghai')

// 使用示例
const displayTime = dayjs.tz(value).format('YYYY-MM-DD HH:mm:ss')

// 表单提交（带时区）
value-format="YYYY-MM-DDTHH:mm:ssZZ"  // 生成 2025-10-31T23:59:59+08:00
```

#### API 时间格式

- **日期**: `YYYY-MM-DD` (如: `2025-10-31`)
- **日期时间**: `YYYY-MM-DDTHH:mm:ss+08:00` (ISO 8601 格式)

### 2.6 部署架构

#### 开发环境
```
开发者本地
├── Django 开发服务器 (localhost:8000)
└── Vite 开发服务器 (localhost:5173)
```

#### 生产环境
```
Internet
    ↓
Nginx (80/443)
    ├── 静态文件 (/dist)
    └── API 反向代理
            ↓
        Gunicorn (unix socket)
            ↓
        Django Application
            ↓
    ┌───────┴───────┬──────────┐
PostgreSQL      Redis      Celery Worker
```

## 三、核心模块设计

### 3.1 认证与权限模块

#### 认证机制
- **技术**: JWT (JSON Web Token) via `djangorestframework-simplejwt`
- **Token 类型**:
  - Access Token: 默认有效期 1 天，用于 API 请求
  - Refresh Token: 默认有效期 10 天，用于刷新 Access Token
  - 每次刷新会签发新的 Refresh Token，保持活跃用户登录态
- **初始密码**: `ChangeMe123!`（首次登录强制修改）
- **密码策略**: 最小 8 位，支持字母、数字、特殊字符
系统提供以下权限类（位于 `apps/common/permissions.py` 和各模块的 `permissions.py`）：

1. **IsAuthenticated**（DRF内置）
   - 要求用户已登录
   - 用于所有需要身份验证的端点

2. **IsAuthenticatedReadAdminWrite**
   - 读操作（GET/HEAD/OPTIONS）：要求已登录
   - 写操作（POST/PUT/PATCH/DELETE）：要求管理员权限（is_staff 或 role in Admin/SuperAdmin）
   - 用于：系统公告、乐谱管理等

3. **IsAdmin**
   - 所有操作都要求管理员权限
   - 用于：人事管理、外请教师管理、称号管理等

4. **IsAdminOrSelfReadOnly**
   - 列表和详情查看：已登录用户
   - 创建/更新/删除：管理员
   - 用于：队员信息管理

5. **IsAdminOrEventAdmin**
   - 读操作：已登录用户
   - 创建：管理员
   - 更新/删除：管理员或活动管理员
   - 用于：活动管理

6. **AllowAny**（DRF内置，仅特殊端点）
   - 无需认证即可访问
   - 仅用于：登录、token刷新、加密下载链接（`/api/v1/common/media/`）

**重要**：除登录、token刷新和加密下载链接外，所有API端点都要求用户登录。匿名用户无法访问任何业务数据。

### 3.2 角色与权限矩阵

#### 用户角色

```python
class UserRole:
    SUPERADMIN = 'SuperAdmin'  # 超级管理员
    ADMIN = 'Admin'            # 管理员
    MEMBER = 'Member'          # 普通队员
```

#### 权限级别

| 功能 | Member | Admin | SuperAdmin |
|-----|--------|-------|------------|
| 查看个人信息 | ✅ | ✅ | ✅ |
| 修改个人信息 | ✅ | ✅ | ✅ |
| 查看其他队员信息 | ✅ | ✅ | ✅ |
| 修改其他队员信息 | ❌ | ✅ | ✅ |
| 创建/删除队员 | ❌ | ✅ | ✅ |
| 上传/删除乐谱 | ❌ | ✅ | ✅ |
| 下载乐谱 | ✅ | ✅ | ✅ |
| 创建/管理活动 | ❌ | ✅ | ✅ |
| 报名活动 | ✅ | ✅ | ✅ |
| 发起签到 | ❌ | ✅ | ✅ |
| 签到 | ✅ | ✅ | ✅ |
| 发布/批改作业 | ❌ | ✅ | ✅ |
| 提交作业 | ✅ | ✅ | ✅ |
| 系统配置 | ❌ | ❌ | ✅ |

### 3.3 人事管理模块

#### 队员档案 (Member)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `user_id` | String(10) | ✅ | 学号（主键） |
| `avatar` | Image | ❌ | 头像，JPG/PNG/WebP，最大 2 MB；前端上传方形裁剪图，小头像圆形展示 |
| `name` | String(50) | ✅ | 姓名 |
| `gender` | Choice | ✅ | 性别：男/女 |
| `voice_part` | Choice | ✅ | 声部：S1/S2/A1/A2/T1/T2/B1/B2/Other |
| `department` | String(100) | ✅ | 院系（前端下拉） |
| `department_other` | String(100) | ❌ | 院系为"其他"时的具体名称 |
| `class_name` | String(50) | ✅ | 班级 |
| `phone_number` | String(11) | ✅ | 手机号（中国大陆） |
| `email` | Email | ✅ | 邮箱 |
| `wechat_id` | String(50) | ✅ | 微信号 |
| `dorm` | String(50) | ❌ | 宿舍房间号 |
| `birthday` | Date | ❌ | 出生日期 |
| `hometown` | String(100) | ❌ | 籍贯 |
| `ethnicity` | String(50) | ❌ | 民族 |
| `political_status` | Choice | ❌ | 政治面貌 |
| `political_affiliation` | Choice | ❌ | 党团关系所在 |
| `is_specialty` | Boolean | ❌ | 是否为特长生 |
| `is_centralized` | Boolean | ❌ | 是否为集中班班员 |
| `position` | String(100) | ❌ | 队内职务 |
| `join_month` | String(7) | ✅ | 入队年月 (YYYY-MM) |
| `graduate_month` | String(7) | 首次登录必填 | 预计毕业时间 (YYYY-MM)，管理员创建可暂空 |
| `tier` | Choice | ✅ | 梯队：一队/二队 |
| `portfolio` | Text | ❌ | 业务档案 |

**声部选项**:
- S1, S2 (女高音)
- A1, A2 (女低音)
- T1, T2 (男高音)
- B1, B2 (男低音)
- Other (其他/待定)

**政治面貌选项**:
- 中共党员
- 中共预备党员
- 共青团员
- 群众
- 民主党派成员
- 无党派人士
- 留学生

#### 教师信息 (Instructor)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `instructor_id` | String(18) | ✅ | 身份证号（主键） |
| `name` | String(50) | ✅ | 姓名 |
| `phone_number` | String(11) | ✅ | 手机号 |
| `vehicle_number` | String(20) | ❌ | 车牌号 |
| `title` | String(50) | ❌ | 学位/职级 |
| `affiliation` | String(100) | ❌ | 工作单位 |
| `address` | String(200) | ❌ | 校外居住地 |
| `fee` | String(100) | ❌ | 费用标准 |

#### 称号系统 (Title)

**功能**:
- 支持为队员授予各类称号（如"本月寿星"、"优秀队员"等）
- 支持自动化称号管理（如生日称号自动更新）
- 支持称号历史记录

**核心模型**:
- `Title`: 称号定义
- `TitleGrant`: 称号授予记录（多对多关系）

### 3.4 谱务管理模块

#### 乐谱模型 (SheetMusic)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `id` | UUID | ✅ | 主键（自动生成） |
| `public_id` | String | ✅ | 公开ID（用于URL） |
| `title` | String(200) | ✅ | 曲名 |
| `lyricist` | String(100) | ❌ | 作词 |
| `composer` | String(100) | ❌ | 作曲 |
| `arranger` | String(100) | ❌ | 编曲 |
| `introduction` | Text | ❌ | 曲目介绍 |
| `original_file` | File | ✅ | PDF 文件（≤ 20MB） |
| `copyright_notice` | Text | ❌ | 版权声明 |
| `is_restricted` | Boolean | ❌ | 是否受限 |
| `visible_to_all` | Boolean | ✅ | 是否全员可见 |
| `visible_events` | M2M | ❌ | 可见活动列表 |
| `visible_members` | M2M | ❌ | 可见成员列表 |
| `upload_time` | DateTime | ✅ | 上传时间（自动） |
| `updated_at` | DateTime | ✅ | 更新时间（自动） |

#### 水印机制

**水印内容**: `清华合唱-{姓名}-{学号}`

**技术实现**:
```python
# 使用 reportlab + pypdf
# 水印特性：
# - 单个对角线水印
# - 浅灰色（透明度低）
# - 字体支持中文（通过 WATERMARK_FONT_PATH 环境变量配置）
```

**字体配置**:
```bash
# 环境变量示例
WATERMARK_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc  # Linux
WATERMARK_FONT_PATH=/System/Library/Fonts/PingFang.ttc  # macOS
```

#### 下载流程（异步）

```
用户请求下载
    ↓
POST /api/v1/sheets/{id}/download/
    ↓
创建异步任务（返回 task_id）
    ↓
Celery Worker 处理
    ├─ 读取原始 PDF
    ├─ 生成水印
    ├─ 合并PDF
    └─ 保存到临时文件（1小时有效期）
    ↓
GET /api/v1/sheets/task/{task_id}/
    ↓
返回带水印的 PDF 文件
```

详情页预览使用同一套异步流程生成完整带水印 PDF。任务完成后前端使用返回的
`stream_url` 作为浏览器 PDF 查看器地址，避免先把完整 PDF 下载成 Axios blob。

### 3.5 活动管理模块

#### 活动模型 (Event)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `id` | UUID | ✅ | 主键 |
| `public_id` | String | ✅ | 公开ID |
| `title` | String(200) | ✅ | 活动标题 |
| `description` | Text | ❌ | 活动描述 |
| `start_time` | DateTime | ✅ | 开始时间 |
| `end_time` | DateTime | ✅ | 结束时间 |
| `location` | String(200) | ❌ | 活动地点 |
| `visibility` | Choice | ✅ | 可见性 |
| `announcement` | Text | ❌ | 活动公告 |
| `is_open_for_registration` | Boolean | ❌ | 是否开放报名 |
| `participants` | M2M | ❌ | 参与成员 |
| `administrators` | M2M | ❌ | 活动管理员 |
| `related_sheets` | M2M | ❌ | 关联乐谱 |
| `created_at` | DateTime | ✅ | 创建时间 |

**可见性选项**:
- `ALL`: 全体队员
- `FIRST`: 仅一队
- `SECOND`: 仅二队
- `PARTIAL`: 部分成员（由管理员指定）

#### 公告图片

- 支持上传多张图片
- 格式: JPG/PNG/GIF
- 大小限制: ≤ 5MB
- 存储路径: `tacos_media/event_announcements/`

### 3.6 签到系统

#### 签到会话 (CheckInSession)

**签到类型**:
- **PASSWORD**: 密码签到（管理员设置密码，队员输入）
- **LOCATION**: 定位签到（队员提交地理位置）

**会话状态**:
- `PENDING`: 已创建，未开始
- `ACTIVE`: 进行中
- `ENDED`: 已结束

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `event` | FK | ✅ | 关联活动 |
| `type` | Choice | ✅ | 签到类型 |
| `password` | String | ❌ | 密码（PASSWORD类型） |
| `status` | Choice | ✅ | 会话状态 |
| `started_at` | DateTime | ❌ | 开始时间 |
| `ended_at` | DateTime | ❌ | 结束时间 |
| `created_by` | FK | ✅ | 创建者 |

#### 签到记录 (CheckInRecord)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `session` | FK | ✅ | 关联会话 |
| `member` | FK | ✅ | 签到成员 |
| `checked_in_at` | DateTime | ✅ | 签到时间 |
| `latitude` | Decimal | ❌ | 纬度（LOCATION类型） |
| `longitude` | Decimal | ❌ | 经度（LOCATION类型） |

### 3.7 作业系统

#### 作业模型 (Assignment)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `id` | UUID | ✅ | 主键 |
| `public_id` | String | ✅ | 公开ID |
| `event` | FK | ✅ | 关联活动 |
| `title` | String(200) | ✅ | 作业标题 |
| `description` | Text | ✅ | 作业描述 |
| `due_date` | DateTime | ✅ | 截止时间 |
| `max_score` | Integer | ❌ | 满分值 |
| `created_by` | FK | ✅ | 创建者 |
| `created_at` | DateTime | ✅ | 创建时间 |

#### 作业提交 (AssignmentSubmission)

**核心字段**:

| 字段 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `assignment` | FK | ✅ | 关联作业 |
| `member` | FK | ✅ | 提交成员 |
| `content` | Text | ❌ | 文字内容 |
| `score` | Integer | ❌ | 分数 |
| `feedback` | Text | ❌ | 教师评语 |
| `submitted_at` | DateTime | ✅ | 提交时间 |
| `graded_at` | DateTime | ❌ | 批改时间 |
| `is_late` | Boolean | ✅ | 是否迟交 |

#### 作业附件

- **教师附件**: 作业发布时上传的参考资料
- **学生附件**: 作业提交时上传的作业文件
- **格式限制**: 常见文档格式（PDF、DOCX、图片等）
- **大小限制**: 单文件 ≤ 10MB

## 四、API 接口文档

### 4.1 基础规范

**Base URL**: `/api/v1`
**认证**: JWT Bearer Token (`Authorization: Bearer <token>`)
**Content-Type**: `application/json` (除文件上传为 `multipart/form-data`)

**统一响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": { /* 具体数据 */ }
}
```

**例外**: `/api/v1/auth/refresh` 直接返回 SimpleJWT 格式 `{"access": "..."}`

### 4.2 HTTP 状态码

| 码 | 说明 | 码 | 说明 |
|----|------|----|------|
| 200 | 成功 | 401 | 未授权 |
| 201 | 创建成功 | 403 | 权限不足 |
| 202 | 已接受（异步） | 404 | 不存在 |
| 400 | 参数错误 | 409 | 冲突 |
| 410 | 已过期 | 422 | 验证失败 |
| 500 | 服务器错误 | | |

### 4.3 认证 API (`/auth`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| POST | `/login` | 登录 | Public |
| POST | `/logout` | 登出 | Auth |
| POST | `/refresh` | 刷新Token | Public |
| GET | `/me` | 当前用户信息 | Auth |
| PUT | `/password` | 修改密码 | Auth |
| PUT | `/first-login` | 首次登录完善信息 | Auth |

**登录示例**:
```http
POST /api/v1/auth/login
{"user_id": "2021012345", "password": "pass123"}

→ {"code": 200, "data": {"token": "...", "refresh_token": "...", "user": {...}}}
```

### 4.4 队员管理 API (`/members`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 队员列表 | Auth |
| POST | `/` | 创建队员 | Admin |
| GET | `/{public_id}/` | 队员详情 | Auth |
| PUT/PATCH | `/{public_id}/` | 更新队员，状态和梯队等管理员字段仅 Admin 可改 | Self/Admin |
| POST | `/{public_id}/avatar/` | 上传本人或管理员维护的头像 | Self/Admin |
| DELETE | `/{public_id}/avatar/` | 删除本人或管理员维护的头像 | Self/Admin |
| DELETE | `/{public_id}/` | 删除队员 | Admin |
| POST | `/bulk-import/` | 批量导入 | Admin |
| GET | `/bulk-template/` | 下载模板 | Admin |
| GET | `/export/` | 导出Excel | Admin |

**查询参数**:
- `page`, `page_size`: 分页
- `search`: 模糊搜索（姓名/学号）
- `voice_part`, `tier`, `status`, `birthday_month`: 过滤

### 4.5 校友信息 API (`/alumni-profiles`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 校友信息列表 | Admin |
| POST | `/` | 创建校友信息 | Admin |
| GET | `/me/` | 当前校友信息 | Alumni |
| PATCH | `/me/` | 更新当前校友信息 | Alumni |

`/me/` 仅允许 `Member.status = ALUMNI` 的用户访问。普通成员不能自行切换状态。
`AlumniProfile` 支持 `current_city`、`industry`、`company`（界面显示为“单位”）、`job_title`、`graduation_month`、`bio`、`contact_note`、`allow_contact`，其中 `graduation_month` 为必填。微信、电话、邮箱等联系字段使用成员档案的 `wechat_id`、`phone_number`、`email`；预计毕业时间使用 `Member.graduate_month`（管理员创建可暂空，用户首次登录必填），校友毕业时间使用 `AlumniProfile.graduation_month`。

**批量导入**:
```http
POST /api/v1/members/bulk-import/
Content-Type: multipart/form-data

file: <xlsx/csv>
override: true  # 可选，覆盖已有信息
```

### 4.6 教师管理 API (`/instructors`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 教师列表 | Auth |
| POST | `/` | 创建教师 | Admin |
| GET | `/{public_id}/` | 教师详情 | Auth |
| PUT | `/{public_id}/` | 更新教师 | Admin |
| DELETE | `/{public_id}/` | 删除教师 | Admin |

### 4.7 谱务管理 API (`/sheets`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 乐谱列表 | Auth |
| POST | `/` | 上传乐谱 | Admin |
| GET | `/{public_id}/` | 乐谱详情 | Auth |
| PUT | `/{public_id}/` | 更新乐谱 | Admin |
| DELETE | `/{public_id}/` | 删除乐谱 | Admin |
| POST | `/{public_id}/download/` | 发起下载任务 | Auth |
| GET | `/task/{task_id}/` | 获取下载结果 | Auth |
| GET | `/task/{task_id}/stream/` | 签名链接流式预览 | Signed URL |

`Sheet` 可见性字段：
- `visible_to_all`: 在队成员全员可见。
- `visible_to_alumni`: 校友可见。
- `visible_events`: 关联活动可见；若活动 `visible_to_alumni=true`，校友也可通过该活动看到关联乐谱。
- `visible_members`: 指定成员可见。

**异步下载流程**:
```
1. POST /{public_id}/download/ → {"task_id": "..."}
2. 轮询 GET /task/{task_id}/ (1秒间隔)
   - JSON响应 → 处理中
   - PDF响应 → 下载完成
```

**查询参数**:
- `preview=true`: 浏览器预览模式（默认 false 触发下载）
- `status_only=true`: 仅返回任务状态 JSON，不下载 PDF blob；用于详情页等待完整预览生成。

**完整预览**:
- 详情页预览仍生成完整带水印 PDF。
- 任务完成后使用 `stream_url` 进入 `/task/{task_id}/stream/`，浏览器 PDF 查看器可直接加载完整文件并使用 Range 请求。

### 4.8 活动管理 API (`/events`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 活动列表 | Auth |
| POST | `/` | 创建活动 | Admin |
| GET | `/{public_id}/` | 活动详情 | Auth |
| PUT | `/{public_id}/` | 更新活动 | Admin |
| DELETE | `/{public_id}/` | 删除活动 | Admin |
| POST | `/{public_id}/join/` | 报名活动 | Auth |
| GET | `/{public_id}/members/export/` | 导出活动参与队员名单（.xlsx） | Admin/EventAdmin |

**GET 返回字段（列表/详情）仅包含基础信息与关系标识：**
- `id, name, introduction, announcement, start_date, end_date, visibility, visible_to_alumni, created_at, updated_at`
- `relation`: 当前用户与活动关系，取值为：
  - `event_admin`: 活动管理员
  - `member`: 活动参与成员
  - `not_member`: 非成员

校友账号只能查看 `visible_to_alumni=true` 的活动或显式加入其参与/管理关系的活动，并可通过 `/join/` 报名校友可见活动。

说明：作业、关联乐谱与签到等详细数据不再嵌入活动详情，请通过以下专属端点获取：
- 作业：`/api/v1/events/{public_id}/assignments/` 及其子端点
- 乐谱：`/api/v1/events/{public_id}/sheets`
- 队员：`/api/v1/events/{public_id}/members/`，导出使用 `/api/v1/events/{public_id}/members/export/`
- 签到：`/api/v1/events/{public_id}/checkin/...`

**公告图片**:
- POST `/{public_id}/announcement/images/`: 上传图片 (JPG/PNG/GIF, ≤5MB)
- DELETE `/{public_id}/announcement/images/{image_id}/`: 删除图片

**查询参数**:
- `only_participated=true`: 仅显示我参与的

### 4.9 签到 API (`/events/{public_id}/checkin`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/status/` | 当前签到状态 | Auth |
| GET | `/sessions/` | 会话列表 | Auth |
| POST | `/start/` | 创建会话 | Admin |
| POST | `/begin/` | 开始会话 | Admin |
| POST | `/stop/` | 结束会话 | Admin |
| POST | `/submit/` | 提交签到 | Auth |
| GET | `/records/` | 签到记录 | Auth |
| GET | `/summary/` | 签到统计 | Admin |

**创建会话**:
```json
{
  "type": "PASSWORD",  // 或 LOCATION
  "password": "123456" // PASSWORD类型必填
}
```

**提交签到**:
```json
// PASSWORD
{"password": "123456"}

// LOCATION
{"latitude": 39.9999, "longitude": 116.3333}
```

### 4.10 作业 API (`/events/{public_id}/assignments`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| GET | `/` | 作业列表 | Auth |
| POST | `/create/` | 创建作业 | Admin |
| GET | `/{aid}/` | 作业详情 | Auth |
| PUT | `/{aid}/edit/` | 更新作业 | Admin |
| POST | `/{aid}/attachments/` | 上传附件(教师) | Admin |
| POST | `/{aid}/submit/` | 提交作业(学生) | Auth |
| GET | `/{aid}/my-submission/` | 我的提交 | Auth |
| GET | `/{aid}/submissions/` | 提交列表 | Admin |
| POST | `/{aid}/grade/` | 批改作业 | Admin |
| POST | `/{aid}/submissions/export/` | 导出任务 | Admin |
| GET | `/{aid}/export-task/{task_id}/` | 导出结果 | Admin |

**提交作业**:
```http
POST /api/v1/events/{id}/assignments/{aid}/submit/
Content-Type: multipart/form-data

content: "作业文字内容"
files: <文件1>
files: <文件2>
```

**批改作业**:
```json
{
  "submission_id": "...",
  "score": 95,
  "feedback": "完成得很好！"
}
```

### 4.11 称号管理 API (`/titles`)

| 方法 | 端点 | 说明 | 权限 |
|-----|------|------|------|
| POST | `/update-birthday-titles/` | 更新生日称号 | Admin |

```json
{
  "title_name": "本月寿星",  // 可选
  "month": 9                // 可选，默认当前月
}
```

### 4.12 媒体文件访问 (`/common/media`)

```http
GET /api/v1/common/media/?path=<相对路径>&token=<临时token>
```

用于访问受保护的媒体文件（公告图片、作业附件等）。

## 五、数据库设计

### 5.1 核心表关系

```
User (认证)
  ├─ 1:1 → Member (队员档案)
  │          ├─ M:N → Title (称号)
  │          ├─ M:N → Event (活动参与)
  │          └─ 1:N → AssignmentSubmission (作业提交)
  │
  └─ 1:N → Event (创建的活动)

Event (活动)
  ├─ 1:N → CheckInSession (签到会话)
  │          └─ 1:N → CheckInRecord (签到记录)
  ├─ 1:N → Assignment (作业)
  │          └─ 1:N → AssignmentSubmission
  ├─ M:N → SheetMusic (关联乐谱)
  └─ M:N → Member (参与者)

SheetMusic (乐谱)
  └─ 1:N → DownloadTask (下载任务)

Instructor (教师)
```

### 5.2 索引策略

```sql
-- 用户表
CREATE INDEX idx_users_role ON users(role);

-- 队员表
CREATE INDEX idx_members_name ON members(name);
CREATE INDEX idx_members_voice_part ON members(voice_part);
CREATE INDEX idx_members_tier ON members(tier);
CREATE INDEX idx_members_join_month ON members(join_month);
CREATE INDEX idx_members_birthday_month ON members(EXTRACT(MONTH FROM birthday));
CREATE INDEX idx_members_voice_tier ON members(voice_part, tier);  -- 复合索引

-- 乐谱表
CREATE INDEX idx_sheets_title ON sheets(title);
CREATE INDEX idx_sheets_composer ON sheets(composer);
CREATE INDEX idx_sheets_upload_time ON sheets(upload_time);
CREATE INDEX idx_sheets_public_id ON sheets(public_id);  -- UUID查询

-- 活动表
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_visibility ON events(visibility);

-- 作业表
CREATE INDEX idx_assignments_due_date ON assignments(due_date);
CREATE INDEX idx_submissions_submitted_at ON assignment_submissions(submitted_at);
```

### 5.3 数据库配置

```python
# config/settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'tacos_db'),
        'USER': os.getenv('DB_USER', 'tacos_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # 连接池
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

## 六、项目结构

### 6.1 后端结构

```
tacos_backend/
├── manage.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── config/
│   ├── settings/
│   │   ├── base.py          # 基础配置
│   │   ├── development.py   # 开发环境
│   │   ├── production.py    # 生产环境
│   │   └── testing.py       # 测试环境
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py            # Celery配置
├── apps/
│   ├── authentication/      # 认证模块
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── personnel/           # 人事模块
│   │   ├── models.py        # Member, Instructor, Title
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── filters.py
│   │   ├── validators.py
│   │   ├── importers.py     # 批量导入
│   │   ├── tasks.py         # Celery任务
│   │   └── signals.py       # 信号处理
│   ├── sheet_music/         # 谱务模块
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── watermark.py     # 水印处理
│   │   └── tasks.py         # 异步下载
│   ├── events/              # 活动模块
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── permissions.py
│   └── common/              # 公共模块
│       ├── models.py        # 基础模型
│       ├── permissions.py
│       ├── pagination.py
│       ├── exceptions.py
│       └── utils.py
└── static/                  # 静态文件
```

### 6.2 前端结构

```
tacos_frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js
│   ├── store/               # Vuex状态管理
│   │   └── modules/
│   │       ├── auth.js
│   │       ├── personnel.js
│   │       └── sheets.js
│   ├── views/               # 页面组件
│   │   ├── Home.vue
│   │   ├── Login.vue
│   │   ├── personnel/
│   │   │   ├── MemberList.vue
│   │   │   ├── MemberDetail.vue
│   │   │   └── MemberForm.vue
│   │   ├── sheets/
│   │   │   ├── SheetList.vue
│   │   │   └── SheetDetail.vue
│   │   └── events/
│   │       ├── EventList.vue
│   │       └── EventDetail.vue
│   ├── components/          # 组件
│   │   ├── layout/
│   │   │   ├── Header.vue
│   │   │   └── Sidebar.vue
│   │   └── common/
│   │       ├── LoadingSpinner.vue
│   │       └── ConfirmDialog.vue
│   ├── api/                 # API调用
│   │   ├── index.js         # Axios配置
│   │   ├── auth.js
│   │   ├── personnel.js
│   │   └── sheets.js
│   └── utils/
│       ├── auth.js          # Token管理
│       ├── format.js        # 日期格式化
│       └── constants.js     # 常量配置
└── public/
```

### 6.3 媒体文件结构

```
tacos_media/                 # 项目同级目录
├── sheet_music/             # 乐谱PDF
│   └── {UUID}.pdf
├── sheet_music_watermarked/ # 水印PDF(临时)
│   └── {task_id}.pdf
├── event_announcements/     # 活动公告图片
│   └── {UUID}_{timestamp}.jpg
├── assignment_attachments/  # 作业附件(教师)
│   └── {UUID}_{filename}
└── submission_attachments/  # 作业附件(学生)
    └── {UUID}_{filename}
```

## 七、配置管理

### 7.1 环境变量 (.env)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

# 数据库
DB_NAME=tacos_db
DB_USER=tacos_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 文件存储
MEDIA_ROOT=/var/www/tacos/tacos_media
WATERMARK_FONT_PATH=/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc

# 安全
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=1440  # 默认 1 天
REFRESH_TOKEN_LIFETIME_DAYS=10      # 默认 10 天
```

### 7.2 下拉列表配置

**配置文件**: `tacos_frontend/src/utils/constants.js`

```javascript
// 声部选项
export const VOICE_PARTS = [
  { value: 'S1', label: '女高音1' },
  { value: 'S2', label: '女高音2' },
  { value: 'A1', label: '女低音1' },
  { value: 'A2', label: '女低音2' },
  { value: 'T1', label: '男高音1' },
  { value: 'T2', label: '男高音2' },
  { value: 'B1', label: '男低音1' },
  { value: 'B2', label: '男低音2' },
  { value: 'Other', label: '其他' }
]

// 院系选项
export const DEPARTMENTS = [
  '电子系', '物理系', '计算机系', '数学系',
  '化学系', '交叉信息研究院', '其他'
]

// 政治面貌
export const POLITICAL_STATUS = [
  '中共党员', '中共预备党员', '共青团员',
  '群众', '民主党派成员', '无党派人士', '留学生'
]

// 民族
export const ETHNICITIES = [
  '汉族', '满族', '回族', '藏族', '蒙古族',
  '维吾尔族', '壮族', '其他'
]

// 籍贯（省级）
export const HOMETOWNS = [
  '北京市', '天津市', '上海市', '重庆市',
  '河北省', '山西省', '辽宁省', '吉林省',
  // ... 其他省份
]

// 活动可见性
export const EVENT_VISIBILITY = [
  { value: 'ALL', label: '全体队员' },
  { value: 'FIRST', label: '仅一队' },
  { value: 'SECOND', label: '仅二队' },
  { value: 'PARTIAL', label: '部分队员' }
]
```

**特性**:
- ✅ 前端控制，无需重启后端
- ✅ 支持动态添加选项
- ✅ 后端兼容任意文本值
- ✅ 历史数据无需迁移

## 八、部署运维

### 8.1 系统要求

**服务器**:
- OS: Ubuntu 20.04+ / CentOS 8+
- RAM: ≥ 4GB
- Disk: ≥ 50GB
- Python: 3.9+
- PostgreSQL: 13+
- Redis: 6+
- Node.js: 20+ (构建用)

### 8.2 部署步骤

#### 1. 后端部署

```bash
# 1. 克隆代码
cd /var/www
git clone <repo-url> tacos
cd tacos/tacos_backend

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env.production.local
nano .env.production.local  # 编辑配置

# 5. 数据库迁移
python manage.py migrate

# 6. 创建超级用户
python manage.py createsuperuser

# 7. 收集静态文件
python manage.py collectstatic --noinput

# 8. 定时任务由 Celery Beat 执行，确认服务已配置
sudo systemctl status tacos-celery-beat
```

#### 2. 前端部署

```bash
cd /var/www/tacos/tacos_frontend

# 1. 安装依赖
npm install

# 2. 构建生产版本
npm run build

# 3. 产物位于 dist/
```

#### 3. Systemd 服务配置

参见 [SYSTEMD_DEPLOYMENT.md](./SYSTEMD_DEPLOYMENT.md) 获取详细配置：

- `tacos.service` - Gunicorn 服务
- `tacos-celery-worker.service` - Celery Worker
- `tacos-celery-beat.service` - Celery Beat

**快速启动**:
```bash
# 启动服务
sudo systemctl start tacos
sudo systemctl start tacos-celery-worker
sudo systemctl start tacos-celery-beat

# 开机自启
sudo systemctl enable tacos
sudo systemctl enable tacos-celery-worker
sudo systemctl enable tacos-celery-beat

# 查看状态
sudo systemctl status tacos
```

#### 4. Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/tacos/tacos_frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API反向代理
    location /api/ {
        proxy_pass http://unix:/run/gunicorn/tacos.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 媒体文件（通过API鉴权，不直接暴露）
    # 已通过 /api/v1/common/media/ 端点处理
}
```

### 8.3 数据备份

#### 自动备份脚本

参见 [scripts/BACKUP_README.md](./scripts/BACKUP_README.md)，其中包含 SQLite 和 PostgreSQL 备份说明。

**快速备份**:
```bash
# 数据库备份
cd /var/www/tacos/scripts
./backup_tacos.sh

# 备份文件位置
ls -lh /var/backups/tacos/
```

**恢复数据**:
```bash
./restore_tacos.sh /var/backups/tacos/backup_20251031_120000.sql
```

### 8.4 资源清理

参见 [scripts/ASSET_CLEANUP_README.md](./scripts/ASSET_CLEANUP_README.md)

**清理未使用的文件**:
```bash
cd /var/www/tacos/scripts
./cleanup_unused_assets.sh
```

**清理作业附件**:
1. 在 Django Admin (`/admin`) 中删除附件记录
2. 运行清理脚本删除孤立文件

### 8.5 监控与日志

**日志位置**:
```
/var/log/tacos/
├── access.log       # Gunicorn访问日志
├── error.log        # Gunicorn错误日志
├── django.log       # Django应用日志
└── celery.log       # Celery任务日志

/var/log/tacos/celery-beat.log  # Celery Beat 定时任务日志
```

**查看日志**:
```bash
# 实时查看
tail -f /var/log/tacos/error.log

# 搜索错误
grep "ERROR" /var/log/tacos/django.log

# 查看Celery任务
tail -f /var/log/tacos/celery.log
```

### 8.6 常见故障排除

#### 服务无法启动
```bash
# 检查配置
python manage.py check

# 查看详细错误
journalctl -u tacos.service -n 50

# 测试Gunicorn
gunicorn --check-config config.wsgi:application
```

#### Celery任务不执行
```bash
# 检查Redis连接
redis-cli ping

# 查看Celery状态
celery -A config inspect active

# 重启Worker
sudo systemctl restart tacos-celery-worker
```

#### 数据库连接问题
```bash
# 测试连接
psql -h localhost -U tacos_user -d tacos_db

# 检查配置
cat .env.production.local | grep DB_

# 查看连接数
SELECT count(*) FROM pg_stat_activity;
```

## 九、开发规范

### 9.1 生日称号自动更新

**功能**: 每月自动更新"本月寿星"称号

**配置**:
```python
# config/celery.py
app.conf.beat_schedule["update-monthly-birthday-title"] = {
    "task": "apps.personnel.tasks.update_monthly_birthday_title",
    "schedule": crontab(minute=0, hour=0, day_of_month=1),
}
```

**手动触发**:
```bash
# 命令行
python manage.py update_birthday_titles --month 10

# 试运行
python manage.py update_birthday_titles --dry-run

# API
POST /api/v1/titles/update-birthday-titles/
{"title_name": "本月寿星", "month": 10}
```

**扩展示例**:
```python
# 每季度更新
app.conf.beat_schedule["update-quarterly-birthday-title"] = {
    "task": "apps.personnel.tasks.update_quarterly_birthday_title",
    "schedule": crontab(minute=0, hour=3, day_of_month=1, month_of_year="1,4,7,10"),
}

# 每日生日提醒
app.conf.beat_schedule["send-birthday-notifications"] = {
    "task": "apps.personnel.tasks.send_birthday_notifications",
    "schedule": crontab(minute=0, hour=9),
}
```

### 9.2 长期未登录成员停用

该定时任务每天自动将超过 6 个月未登录的在队成员设为停用。

| 项目 | 说明 |
|------|------|
| 任务名 | `apps.personnel.tasks.deactivate_stale_active_members` |
| 调度 | Celery Beat 每日 02:30 执行 |
| 处理范围 | 仅处理 `Member.status=ACTIVE` 的成员 |
| 排除范围 | `ALUMNI` 和已有 `INACTIVE` 成员不会被自动修改 |
| 时间判断 | 有登录记录时按 `User.last_login` 判断；从未登录过的账号按 `User.date_joined` 判断 |
| 登录拦截 | `User.is_active=false` 表示账号被禁用，`Member.status=INACTIVE` 表示成员停用 |
| 档案补全 | 任意账号若没有成员档案，登录后进入首次信息完善流程；管理员权限由 `User.role` 控制 |

### 9.3 代码格式化规范

本项目使用自动化工具保持代码风格一致性。

#### 工具配置

**Python (Backend)**:
- **Black**: 代码格式化（行长度 88）
- **isort**: import 语句排序（与 Black 兼容）
- 配置文件: `tacos_backend/pyproject.toml`

**JavaScript/Vue (Frontend)**:
- **Prettier**: 代码格式化
- **ESLint**: 代码检查和修复
- 配置文件: `tacos_frontend/.prettierrc`

#### 快速使用

**推荐方式 - 使用格式化脚本**:
```bash
cd /var/www/tacos
chmod +x scripts/format_code.sh
./scripts/format_code.sh
```

**单独格式化 Python**:
```bash
cd tacos_backend
black .      # 格式化所有 Python 文件
isort .      # 排序 imports
```

**单独格式化前端**:
```bash
cd tacos_frontend
npm run format    # 格式化所有文件
npm run lint      # 运行 ESLint 修复
```

#### 编辑器集成 (VS Code)

**安装扩展**:
- Python: `ms-python.black-formatter`
- Prettier: `esbenp.prettier-vscode`
- ESLint: `dbaeumer.vscode-eslint`

**保存时自动格式化** (`.vscode/settings.json`):
```json
{
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

#### 最佳实践

1. ✅ **提交前格式化**: 运行格式化脚本
2. ✅ **编辑器配置**: 启用保存时自动格式化
3. ✅ **团队统一**: 使用相同的配置文件
4. ❌ **避免手动**: 不要手动调整格式

#### CI/CD 检查

```bash
# Python 检查
black --check .
isort --check-only .

# 前端检查
npm run format -- --check
npm run lint
```

详见 [代码格式化指南](./scripts/FORMATTING_GUIDE.md)

### 9.4 Git 工作流

```bash
# 开发分支
git checkout -b feature/new-feature dev

# 提交
git add .
git commit -m "feat: add new feature"

# 合并到dev
git checkout dev
git merge feature/new-feature

# 发布到生产
git checkout main
git merge dev
git tag v1.0.2
git push origin main --tags
```

## 十、更新日志

### v2.3.1 (2026-06-04)

- 修复分页状态变更触发筛选监听的问题，避免队员、乐谱和活动列表翻页被重置。
- 统一分页组件事件命名，确保分页按钮与页面监听器保持一致。

### v2.3.0 (2026-06-04)

- 优化前端加载状态、缓存复用和并发请求，减少首屏闪烁和重复加载。
- 增加活动队员导出能力，活动管理员无需加入活动也可管理活动。
- 增加成员列表头像轻量预览，并优化成员列表展示密度。
- 优化活动乐谱下拉选择排序，已选乐谱置顶。
- 统一乐谱上传表单操作，将重置调整为取消返回。

### v2.2.0 (2026-05-28)

- 增加长期未登录成员自动停用任务，`ALUMNI` 不受影响。
- 增加停用成员登录拦截和中文管理员协助提示。
- 增加成员头像上传、方形裁剪、圆形展示和点击预览。
- 明确 `User.is_active` 与 `Member.status` 的职责边界。
- 明确 Django Admin 创建的管理员账号仍需成员档案。

### v2.1.0 (2026-05-27)

- 增加轻量校友联系窗口。
- 增加校友可见活动和乐谱范围控制。
- 优化完整乐谱预览、水印处理和相关权限规则。

### v2.0.0 (2026-01-04)

- 重构前端交互和移动端体验。
- 增加链接分享和快速签到等能力。

### v1.1.1 (2025-11-03)
**Bug修复**:
- 活动可见范围没有正确应用
- 修正仅在单页排序的bug
- 增加First Login失败Backup

### v1.1.0 (2025-11-02)
**功能改进**:
- 增加“作词”在乐谱列表中的显示
- 更换部分tag的颜色
- 所有成员显示列表均按照声部+拼音排序
- 乐谱按照名称顺序排列
- 修改部分路由

### v1.0.1 (2025-10-28)
**修复**:
- 管理员无法编辑已有乐谱

**功能改进**:
- 增加队员总数系统缓存，减轻数据库压力
- 异步实现乐谱水印添加和下载、防止请求堵塞，增加下载和处理的前端提示
- 异步实现作业导出、队员导出，防止请求堵塞，增加导出的前端提示
- 生日称号更新支持模糊匹配（包含"本月寿星"字段即可）

**安全更新**:
- 禁止匿名访问所有业务数据

### v1.0.0 (2025-10-26)

**正式发布**:
- 完善部署方案
- 修复多个小错误
- 生产环境验证通过

### v1.4-beta (2025-10-16)

**Bug修复**:
- 无法发布作业
- 队员详情页返回按钮未加载
- 登录界面重复报错提示
- 管理员签到统计页面空白
- 普通成员无法查看部分活动
- 公告图片删除确认异常

**功能优化**:
- 公告图片删除按钮改为"×"图标
- 活动时间验证改进
- 公告图片大小提示更明显
- 增加备案信息
- 调整声部和梯队Logo颜色
- 个人信息增加预计毕业时间

**安全更新**:
- 媒体文件统一鉴权
- 文件存储隔离到 `tacos_media/`

### v1.3-beta (2025-10-14)

**Bug修复**:
- 部分汉化问题
- 队员编辑路由错误
- 作业截止时间时区Bug
- Django后台缺少乐谱数据

**功能更新**:
- 更浅的乐谱水印
- 支持院系搜索
- 主页显示开放报名活动数
- 优化教师和称号管理界面
- 增加网页图标

**安全更新**:
- 所有资源使用加密 `public_id` 路由

### v1.2-beta (2025-10-13)

**Bug修复**:
- 首次登录界面未显示已有信息
- 生日隐私设置失效
- 活动管理员统计错误
- 公告时间时区错误

**功能更新**:
- 生日和宿舍默认隐私
- 登录错误信息模糊化（安全）
- 作业默认截止时间优化
- 学号隐私保护
- URL使用 `public_id` 代替学号
- 搜索支持回车键
- 列表增加超链接
- 下拉列表支持搜索
- 批量导入支持梯队筛选
- 新增全局公告标题

### v1.1-beta (2025-10-12)

**Bug修复**:
- 作业附件查看问题
- 受限活动访问权限
- 前端显示异常
- 时区显示错误
- 下拉列表选项有限

**功能更新**:
- 籍贯、民族、政治面貌下拉列表
- 批量导入覆盖选项
- 队员信息批量导出
- 日期选择器改进
- 活动关联乐谱功能
- 活动列表UI优化

**交互优化**:
- 作业提交和批改界面
- 快速操作整合到数据面板

### v1.0-beta (2025-09-28)

**初始发布**:
- 人事管理系统
- 谱务管理系统
- 活动管理系统
- 签到系统
- 作业管理系统

## 附录

### A. 待办事项

**优先级高**:
- [ ] API 优化，减少带宽消耗
- [ ] 活动报名时间段配置
- [ ] 队员退出活动功能
- [ ] 分作业、分签到导出表格
- [ ] 输入列表框选择后清空输入
- [ ] 返回时保留翻页位置

**v2.0 计划** (Better UI):
- [ ] 移动端界面优化
- [ ] UI 展示逻辑重构
- [ ] 称号系统前端展示
- [ ] 称号授予顺序管理

**v3.0 计划** (社交系统):
- [ ] 队员上传乐谱（需审核）
- [ ] 匿名信箱功能
- [ ] 评论系统

### B. 相关文档

- [系统部署指南](./SYSTEMD_DEPLOYMENT.md)
- [备份恢复指南](./scripts/BACKUP_README.md)
- [资源清理指南](./scripts/ASSET_CLEANUP_README.md)
- [代码格式化](./scripts/FORMATTING_GUIDE.md)

### C. 技术支持

**问题反馈**: 通过 Issue Tracker 提交
**文档更新**: 欢迎提交 Pull Request
**版本发布**: 遵循语义化版本规范

### D. API 示例补充

#### D.1 队员管理 API

```
POST /api/v1/members/
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "user_id": "2021012345",
  "name": "张三",
  "gender": "男",
  "voice_part": "T1",
  "department": "计算机科学与技术系",
  "class_name": "计15",
  "phone_number": "13812345678",
  "email": "zhangsan@example.com",
  "dorm": "紫荆1号楼101",
  "birthday": "2000-01-01",
  "hometown": "北京市",
  "ethnicity": "汉族",
  "political_status": "共青团员",
  "political_affiliation": "艺术团",
  "is_specialty": true,
  "is_centralized": false,
  "position": "队员",
  "join_month": "2021-09",
  "tier": "二队",
  "portfolio": "新队员档案"
}

Response:
{
  "code": 201,
  "message": "队员档案创建成功",
  "data": {
    "user_id": "2021012345",
    "name": "张三"
  }
}
```

##### D.1.1 批量导入队员
- 下载模板：`GET /api/v1/members/bulk-template/`（Excel .xlsx）
- 执行导入：`POST /api/v1/members/bulk-import/`（multipart/form-data，字段：
  - `file`：上传的 .csv 或 .xlsx 文件
  - `override`：可选，是否覆盖已有队员信息（按学号）。取值支持 `1/0`、`true/false`、`yes/no`，默认不覆盖）
  ）
- 导入规则：
  - 必填字段：`user_id`、`name`
  - 若 `voice_part` 为空，默认 `Other`
  - 若 `wechat_id` 为空，默认 “请及时填写正确微信号”
  - 若 `join_month` 为空，默认为当前月份（`YYYY-MM`）
  - 若 `tier` 为空，默认 “二队”
  - 其它校验规则与创建接口一致；每行独立校验，逐行返回结果
- 成功类型：`status` 为 `created` 或 `updated`（当 override 开启且找到相同学号时为 `updated`）
- 新队员即获得登录账号，初始默认密码为：`ChangeMe123!`

###### D.1.1.1 覆盖导入（override）
- 可选字段：`override`（`1/0`、`true/false`、`yes/no`；默认不覆盖）
- 当 `override=true` 时：若导入行学号已存在，将对该成员执行“选择性更新”——仅更新导入行中非空字段；导入行为空的字段不会覆盖原有非空值。
- 返回 `rows[].status` 可能为：`created`、`updated`、`error`。

##### D.1.2 导出队员信息
- 下载：`GET /api/v1/members/export/`
- 说明：导出当前筛选条件下的队员信息（Excel .xlsx）。支持与列表相同的查询参数（如 `name__icontains`、`user_id`、`voice_part`、`tier`、`birthday_month`）。

##### D.1.3 获取队员列表
```
GET /api/v1/members/?page=1&page_size=20&voice_part=T1&tier=一队&search=张三&birthday_month=9
Authorization: Bearer <token>

Response:
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 80,
    "page": 1,
    "page_size": 20,
    "members": [
      {
        "user_id": "2021012345",
        "name": "张三",
        "voice_part": "T1",
        "tier": "一队",
        "join_month": "2021-09"
      }
    ]
  }
}
```

##### D.1.4 获取队员详细信息
```
GET /api/v1/members/{public_id}/
Authorization: Bearer <token>

Response:
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": "2021012345",
    "name": "张三",
    "gender": "男",
    "avatar": "/api/v1/common/media/?path=members/avatars/...",
    "voice_part": "T1",
    // ... 其他字段
  }
}
```

##### D.1.5 更新队员信息
```
PATCH /api/v1/members/{public_id}/
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "phone_number": "13812345679",
  "portfolio": "更新后的个人签名"
}

Response:
{
  "code": 200,
  "message": "队员信息更新成功"
}
```

普通成员只能更新自己的档案，且不能修改 `status` 和 `tier`；管理员可以维护这些字段。

##### D.1.6 上传或删除队员头像
```
POST /api/v1/members/{public_id}/avatar/
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
avatar=@/path/to/avatar.png
```

头像仅支持 JPG、PNG、WebP，大小不超过 2 MB。普通成员只能维护自己的头像，管理员可维护任意成员头像。前端上传方形裁剪图，小头像圆形展示，点击成员详情头像时预览方图。删除头像使用：

```
DELETE /api/v1/members/{public_id}/avatar/
Authorization: Bearer <token>
```

##### D.1.7 删除队员档案（仅管理员）
```
DELETE /api/v1/members/{public_id}/
Authorization: Bearer <token>

Response:
{
  "code": 200,
  "message": "队员档案删除成功"
}
```

#### D.2 外请教师管理 API

##### D.2.1 创建教师信息
```
POST /api/v1/instructors
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "instructor_id": "110101199001011234",
  "name": "李老师",
  "phone_number": "13912345678",
  "vehicle_number": "京A12345",
  "title": "教授",
  "affiliation": "中央音乐学院",
  "address": "北京市朝阳区",
  "fee": "500元/课时"
}

Response:
{
  "code": 201,
  "message": "教师信息创建成功",
  "data": {
    "instructor_id": "110101199001011234",
    "name": "李老师"
  }
}
```

##### D.2.2 获取教师列表
```
GET /api/v1/instructors?page=1&page_size=20&search=李老师
Authorization: Bearer <token>

Response:
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "instructors": [
      {
        "instructor_id": "110101199001011234",
        "name": "李老师",
        "title": "教授",
        "affiliation": "中央音乐学院"
      }
    ]
  }
}
```

##### D.2.3 更新教师信息
```
PUT /api/v1/instructors/{instructor_id}
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "phone_number": "13912345679",
  "fee": "600元/课时"
}

Response:
{
  "code": 200,
  "message": "教师信息更新成功"
}
```

#### D.3 谱务管理 API

##### D.3.1 上传乐谱（仅管理员）
```
POST /api/v1/sheets
Authorization: Bearer <token>
Content-Type: multipart/form-data

Request Body:
{
  "title": "青春舞曲",
  "lyricist": "王洛宾",
  "composer": "王洛宾",
  "arranger": "张某某",
  "introduction": "经典新疆民歌",
  "file": <PDF文件>
}

Response:
{
  "code": 201,
  "message": "乐谱上传成功",
  "data": {
    "sheet_id": 1,
    "title": "青春舞曲",
    "file_url": "/files/sheets/1.pdf"
  }
}
```

##### D.3.2 获取乐谱列表（公开可读）
```
GET /api/v1/sheets?page=1&page_size=20&search=青春&composer=王洛宾

Response:
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "sheets": [
      {
        "sheet_id": 1,
        "title": "青春舞曲",
        "lyricist": "王洛宾",
        "composer": "王洛宾",
        "arranger": "张某某",
        "introduction": "经典新疆民歌",
        "upload_time": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

##### D.3.3 获取乐谱详情（公开可读）
```
GET /api/v1/sheets/{sheet_id}

Response:
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "sheet_id": 1,
    "title": "青春舞曲",
    "lyricist": "王洛宾",
    "composer": "王洛宾",
    "arranger": "张某某",
    "introduction": "经典新疆民歌",
    "original_file_path": "/files/sheets/1.pdf",
    "upload_time": "2024-01-01T00:00:00Z"
  }
}
```

##### D.3.4 下载乐谱（带水印 - 异步处理）

乐谱下载采用异步任务处理，避免大文件水印生成阻塞服务器。

**步骤1：发起下载任务**
```
POST /api/v1/sheets/{sheet_id}/download/
Authorization: Bearer <token>

Response:
HTTP 202 Accepted
Content-Type: application/json

{
  "code": 202,
  "message": "任务已创建",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PENDING",
    "error_message": "",
    "created_at": "2025-10-28T10:00:00+08:00",
    "updated_at": "2025-10-28T10:00:00+08:00",
    "expires_at": "2025-10-28T11:00:00+08:00",
    "stream_url": "/api/v1/sheets/task/.../stream/?token=..."
  }
}
```

**步骤2：轮询任务状态或获取结果**
```
GET /api/v1/sheets/task/{task_id}/
Authorization: Bearer <token>
Query Parameters:
  - preview (optional): "true" 或 "false"，默认 false
    - false: Content-Disposition 为 attachment（触发下载）
    - true: Content-Disposition 为 inline（浏览器内预览）
  - status_only (optional): "true" 时始终返回任务状态 JSON，不返回 PDF blob

Response（任务处理中）:
HTTP 200 OK
Content-Type: application/json

{
  "code": 200,
  "message": "任务处理中",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PROCESSING",  // 可能是 PENDING 或 PROCESSING
    "error_message": "",
    "created_at": "2025-10-28T10:00:00+08:00",
    "updated_at": "2025-10-28T10:00:05+08:00",
    "expires_at": "2025-10-28T11:00:00+08:00"
  }
}

Response（任务完成）:
HTTP 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="青春舞曲_2021012345_张三.pdf"
  或
Content-Disposition: inline; filename="青春舞曲_2021012345_张三.pdf"

<PDF 文件内容，包含单个、很浅的对角线水印："清华合唱-姓名-学号">

Response（任务失败）:
HTTP 500 Internal Server Error
Content-Type: application/json

{
  "code": 500,
  "message": "生成水印失败: ...",
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "FAILED",
    "error_message": "具体错误信息",
    "created_at": "2025-10-28T10:00:00+08:00",
    "updated_at": "2025-10-28T10:00:10+08:00",
    "expires_at": "2025-10-28T11:00:00+08:00"
  }
}

Response（任务过期）:
HTTP 410 Gone
Content-Type: application/json

{
  "code": 410,
  "message": "任务已过期，请重新发起下载",
  "data": {}
}
```

**完整预览流式地址**

`POST /download/` 和 `status_only=true` 响应会返回 `stream_url`。详情页在任务
完成后将该 URL 作为 PDF iframe/object 地址，以便浏览器直接加载完整带水印 PDF，
并支持 Range 请求。

**任务状态说明**：
- `PENDING`: 任务已创建，等待处理
- `PROCESSING`: 任务正在处理中（生成水印）
- `COMPLETED`: 任务完成，文件可下载
- `FAILED`: 任务失败，查看 error_message
- 任务有效期：1小时，过期后自动清理

**技术实现**：
- 使用 Celery + Redis 异步任务队列
- 前端轮询间隔：1秒
- 水印生成库：reportlab + pypdf
- 字体兼容：若中文显示异常，可在后端环境设置 `WATERMARK_FONT_PATH` 指向系统 CJK 字体（如 macOS: `/System/Library/Fonts/PingFang.ttc`）

**前端使用示例**：
```javascript
// 1. 发起下载任务
const initResp = await initiateDownload(sheetId)
const taskId = initResp.data.task_id

// 2. 轮询任务状态
const pollTask = async () => {
  const resp = await getDownloadTask(taskId, false)
  const contentType = resp.headers['content-type']

  if (contentType.includes('application/json')) {
    // 仍在处理中，继续轮询
    const jsonData = await resp.data.text()
    const data = JSON.parse(jsonData)

    if (data.data?.status === 'PENDING' || data.data?.status === 'PROCESSING') {
      setTimeout(pollTask, 1000)  // 1秒后重试
    }
  } else {
    // 任务完成，下载文件
    const blob = new Blob([resp.data], { type: 'application/pdf' })
    // 触发下载...
  }
}

pollTask()
```

##### D.3.5 更新乐谱信息（仅管理员）
```
PUT /api/v1/sheets/{sheet_id}
Authorization: Bearer <token>
Content-Type: application/json

Request Body:
{
  "title": "青春舞曲（修订版）",
  "introduction": "经典新疆民歌，2024年修订版"
}

Response:
{
  "code": 200,
  "message": "乐谱信息更新成功"
}
```

##### D.3.6 删除乐谱（仅管理员）
```
DELETE /api/v1/sheets/{sheet_id}
Authorization: Bearer <token>

Response:
{
  "code": 200,
  "message": "乐谱删除成功"
}
```

#### D.4 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户已存在） |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### E. 系统目录结构补充

#### E.1 后端目录结构（Django项目）

```
tacos_backend/
├── manage.py                      # Django管理脚本
├── requirements.txt               # Python依赖包
├── .env                          # 环境变量配置
├── .gitignore                    # Git忽略文件
├── README.md                     # 项目说明文档
├── docker-compose.yml            # Docker配置
├── Dockerfile                    # Docker镜像构建文件
├── config/                       # 项目配置
│   ├── __init__.py
│   ├── settings/                 # 分环境配置
│   │   ├── __init__.py
│   │   ├── base.py              # 基础配置
│   │   ├── development.py       # 开发环境配置
│   │   ├── production.py        # 生产环境配置
│   │   └── testing.py           # 测试环境配置
│   ├── urls.py                  # 全局URL配置
│   ├── wsgi.py                  # WSGI应用
│   └── asgi.py                  # ASGI应用
├── apps/                        # 应用模块
│   ├── __init__.py
│   ├── authentication/          # 用户认证模块
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # 用户模型
│   │   ├── serializers.py       # DRF序列化器
│   │   ├── views.py             # 视图逻辑
│   │   ├── urls.py              # URL路由
│   │   ├── permissions.py       # 权限控制
│   │   ├── utils.py             # 工具函数
│   │   ├── tests/               # 测试文件
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_utils.py
│   │   └── migrations/          # 数据库迁移文件
│   ├── personnel/               # 人事管理模块
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # 队员和教师模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── filters.py           # 过滤器
│   │   ├── validators.py        # 数据验证器
│   │   ├── utils.py
│   │   ├── tests/
│   │   └── migrations/
│   ├── sheet_music/             # 谱务管理模块
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py            # 乐谱模型
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── utils.py             # 水印处理等工具
│   │   ├── watermark.py         # 水印处理逻辑
│   │   ├── storage.py           # 文件存储处理
│   │   ├── tests/
│   │   └── migrations/
│   └── common/                  # 公共模块
│       ├── __init__.py
│       ├── models.py            # 公共基础模型
│       ├── serializers.py       # 公共序列化器
│       ├── views.py             # 公共视图
│       ├── permissions.py       # 公共权限
│       ├── pagination.py        # 分页配置
│       ├── exceptions.py        # 异常处理
│       ├── validators.py        # 通用验证器
│       ├── utils.py             # 通用工具函数
│       └── middleware.py        # 中间件
├── static/                      # 静态文件
│   ├── admin/                   # Django Admin静态文件
│   └── media/                   # 用户上传文件
│       └── sheets/              # 乐谱文件存储
├── templates/                   # 模板文件
│   └── admin/                   # 自定义Admin模板
├── logs/                        # 日志文件
│   ├── django.log
│   ├── error.log
│   └── access.log
├── scripts/                     # 部署和维护脚本
│   ├── deploy.sh
│   ├── backup.sh
│   └── init_data.py             # 初始化数据脚本
└── docs/                        # 项目文档
    ├── api.md                   # API文档
    ├── deployment.md            # 部署文档
    └── database.md              # 数据库设计文档
```

#### E.2 前端目录结构（Vue.js项目）

```
tacos_frontend/
├── public/                      # 公共资源
│   └── index.html              # HTML模板
├── src/                        # 源码目录
│   ├── main.js                 # 应用入口文件
│   ├── App.vue                 # 根组件
│   ├── router/                 # 路由配置
│   │   ├── index.js            # 路由主文件
│   │   ├── routes.js           # 路由定义
│   │   └── (路由守卫由路由钩子实现)
│   ├── store/                  # Vuex状态管理
│   │   ├── index.js            # Store主文件
│   │   ├── modules/            # 模块化Store
│   │   │   ├── auth.js         # 认证模块
│   │   │   ├── personnel.js    # 人事模块
│   │   │   ├── sheets.js       # 谱务模块
│   │   │   └── common.js       # 公共模块
│   │   └── modules/*           # 模块内聚
│   ├── views/                  # 页面组件
│   │   ├── Home.vue            # 首页
│   │   ├── Login.vue           # 登录页
│   │   ├── Dashboard.vue       # 仪表板
│   │   ├── personnel/          # 人事管理页面
│   │   │   ├── MemberList.vue  # 队员列表
│   │   │   ├── MemberDetail.vue# 队员详情
│   │   │   ├── MemberForm.vue  # 队员表单
│   │   │   ├── InstructorList.vue # 教师列表
│   │   │   └── InstructorForm.vue # 教师表单
│   │   ├── sheets/             # 谱务管理页面
│   │   │   ├── SheetList.vue   # 乐谱列表
│   │   │   ├── SheetDetail.vue # 乐谱详情
│   │   │   ├── SheetUpload.vue # 乐谱上传
│   │   │   └── SheetEdit.vue   # 乐谱编辑
│   │   ├── profile/            # 个人中心
│   │   │   ├── Profile.vue     # 个人信息
│   │   │   └── ChangePassword.vue # 修改密码
│   │   └── admin/              # 管理员页面
│   │       ├── UserManagement.vue # 用户管理
│   │       └── SystemSettings.vue # 系统设置
│   ├── components/             # 公共组件
│   │   ├── layout/             # 布局组件
│   │   │   ├── Header.vue      # 页头
│   │   │   ├── Sidebar.vue     # 侧边栏
│   │   │   ├── Footer.vue      # 页脚
│   │   │   └── Breadcrumb.vue  # 面包屑导航
│   │   ├── common/             # 通用组件
│   │   │   ├── LoadingSpinner.vue # 加载动画
│   │   │   ├── ConfirmDialog.vue  # 确认对话框
│   │   │   ├── SearchBox.vue      # 搜索框
│   │   │   ├── Pagination.vue     # 分页组件
│   │   │   ├── FileUpload.vue     # 文件上传
│   │   │   └── DataTable.vue      # 数据表格
│   │   ├── forms/              # 表单组件
│   │   │   ├── VoicePartSelect.vue # 声部选择
│   │   │   ├── DepartmentSelect.vue # 院系选择
│   │   │   ├── DatePicker.vue      # 日期选择
│   │   │   └── PhoneInput.vue      # 手机号输入
│   │   └── charts/             # 图表组件
│   │       ├── PieChart.vue    # 饼图
│   │       └── BarChart.vue    # 柱状图
│   ├── api/                    # API接口
│   │   ├── index.js            # Axios实例与拦截器
│   │   ├── auth.js             # 认证接口
│   │   ├── personnel.js        # 人事接口
│   │   ├── sheets.js           # 谱务接口
│   │   └── events.js           # 活动接口
│   ├── utils/                  # 工具函数
│   │   ├── auth.js             # 认证工具（Cookies）
│   │   ├── validation.js       # 表单验证
│   │   ├── format.js           # 日期/数字格式化
│   │   ├── download.js         # 文件下载
│   │   └── constants.js        # 常量定义
│   ├── assets/                 # 静态资源
│   │   ├── images/             # 图片资源
│   │   ├── styles/             # 样式文件
│   │   │   ├── main.scss       # 主样式
│   │   │   ├── variables.scss  # 样式变量
│   │   │   ├── mixins.scss     # 样式混入
│   │   │   └── components.scss # 组件样式
│   │   └── icons/              # 图标文件
│   ├── plugins/                # 插件配置（按需）
│   └── directives/             # 自定义指令（按需）
├── tests/                      # 测试文件
│   ├── unit/                   # 单元测试
│   │   ├── components/
│   │   ├── views/
│   │   └── utils/
│   └── e2e/                    # 端到端测试
├── package.json                # 项目依赖
├── vite.config.js              # Vite配置
├── .gitignore                  # Git忽略文件
├── README.md                   # 项目说明
├── tailwind.config.js          # Tailwind 配置
└── docs/                       # 前端文档
    ├── components.md           # 组件文档
    ├── development.md          # 开发指南
    └── deployment.md           # 部署指南
```

#### E.3 数据库设计补充说明

##### E.3.1 索引设计
```sql
-- users表索引
CREATE INDEX idx_users_role ON users(role);

-- members表索引
CREATE INDEX idx_members_voice_part ON members(voice_part);
CREATE INDEX idx_members_tier ON members(tier);
CREATE INDEX idx_members_join_month ON members(join_month);
CREATE INDEX idx_members_graduate_month ON members(graduate_month);
CREATE INDEX idx_members_name ON members(name);

-- sheets表索引
CREATE INDEX idx_sheets_title ON sheets(title);
CREATE INDEX idx_sheets_composer ON sheets(composer);
CREATE INDEX idx_sheets_upload_time ON sheets(upload_time);

-- 复合索引
CREATE INDEX idx_members_voice_tier ON members(voice_part, tier);
```

##### E.3.2 数据库连接池配置
```python
# Django settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tacos_db',
        'USER': 'tacos_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}
```

#### E.4 部署架构
（一般不会用Docker部署TaCOS，没有必要）
##### E.4.1 开发环境
```
开发者本地 → Django开发服务器(8000) + Vue开发服务器(3000)
```

##### E.4.2 生产环境
```
用户 → Nginx → Gunicorn → Django应用
     → Nginx → 静态文件(Vue构建产物)
     → PostgreSQL数据库
     → Redis缓存
     → 文件存储(阿里云OSS/腾讯云COS)
```

##### E.4.3 Docker部署配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./tacos_backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  frontend:
    build: ./tacos_frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: tacos_db
      POSTGRES_USER: tacos_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine

volumes:
  postgres_data:
```

**文档最后更新**: 2026-06-04
**文档版本**: v2.3.1
**维护者**: TaCOS开发团队
