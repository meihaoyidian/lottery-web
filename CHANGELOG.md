# lottery-web 更新日志

> lottery-wxapp（微信小程序）→ lottery-web（浏览器端），后端逻辑和数据库复用。

## 2026-07-10（移动端输入修复 + 全局字号提升 + 已确认角标修复）

### 移动端输入框无法弹出键盘

- `index.html`：去掉 viewport 中的 `maximum-scale=1.0, user-scalable=no`，这两个属性阻止了 iOS Safari 聚焦输入框时的自动缩放行为
- `global.css`：去掉 `html` 上的 `-webkit-touch-callout: none`，过激的全局设置影响了移动端输入交互

### 全局字号系统性上调

**问题**：手机端整体字体偏小、看不清。之前已做过一轮调整（body 17px），用户反馈仍不够。

**方案**：所有字号整体上移 1-2px，确立最小字号底线 11px，正文不低于 14px，标题不低于 17px。

| 文件 | 调整范围 |
|---|---|
| `global.css` | body 18px（移）、input/select/textarea 17px |
| `Login.vue` | 标语 14、tab 15、标签 13、输入框 16、错误提示 14 |
| `RecommendationCard.vue` | 标题 17、队名 17(桌)/16(移)、标签类 11、预测 14、摘要 14、组合 15 |
| `Recommendations.vue` | 状态 15、热度条 14、筛选 16(移)、战绩标题 21(桌)/18(移)、描述 14、空状态 18 |
| `History.vue` | Hero 数字 26→34、仪表盘 34、统计卡 28、趋势 24、全部标签/正文 +1~2px |
| `Profile.vue` | 昵称 19、按钮 16、输入 16、标签/正文全面 +1~2px |
| `App.vue` | 底部标签图标 24px、标签文字 11px |

### 场次卡片「方案已确认」角标修复

- `.mc-confirmed-badge` 的 CSS 样式完全丢失，导致 DOM 中存在但不可见
- 对照小程序原版 `recommendation-card.wxss` 恢复：teal 渐变 `#0d9488→#0f766e`、左上角折叠角标 `border-radius:0 0 8px 0`、无阴影无虚线、`padding-top` 给角标留空间

---

## 2026-07-10（代码清理 + UI 优化）

### 清理游客/审核模式残留

- `deps.py`：去掉 REVIEW_MODE 和游客模式注释逻辑
- `config.py`：保留 `REVIEW_MODE=False` 兼容，去掉文档注释
- `main.py`：`/system/config` 返回空对象
- `recommendations.py`：去掉审核模式禁止创建逻辑
- `RecommendationCard.vue`：去掉 `reviewMode` prop
- `Recommendations.vue`：去掉 `:reviewMode="false"` 传参

---

## 2026-07-10（UI 优化 + 浏览记录 + 推荐管理）

### 全局移动端字号提升

- `global.css` body 字号：移动端 17px
- History.vue：标题 16px、统计数字 22px、卡片标题 16px
- Recommendations.vue：状态文字 14px、筛选按钮 15px
- 底部标签栏：图标 24px、文字 12px

### 场次卡片简化（RecommendationCard.vue）

- 去掉了渐变角标、旋转标签、虚线边框、彩色小圆点等装饰
- 重心场次：金色左边线 + 浅金底色
- 精选场次：紫色左边线 + 浅紫底色
- 与历史战绩卡风格统一

### 浏览记录功能补齐

**前端**
- `Recommendations.vue`：加载推荐列表时上报 `POST /view-records`（`viewedIds` Set 去重）
- `ManageRecommendations.vue`：浏览弹窗显示用户列表（手机号/角色/浏览时间）
- 补全 `formatViewTime` 函数，修复弹窗无数据 bug
- 弹窗空状态提示

**API**
- `api/index.js`：新增 `recordView(recommendationId)`

### 推荐管理页优化（ManageRecommendations.vue）

- 筛选按钮居中
- 场次卡片：左侧色条区分重心/精选、状态切换按钮加边框、对阵+预测居中
- 卡片 hover 阴影、操作按钮 hover 反馈
- `formatViewTime` 补全

### 管理后台全局

- 三页（推荐管理/用户管理/战绩Banner）统一"← 返回"按钮回个人中心
- 路由 `/admin/achievements/edit/:id?` 支持创建和编辑两种模式

---

## 2026-07-09（会员体系重构 + 部署）

### 用户体系：独立 user_web 表

- 新建 `user_web` 表，Web 端用户数据从共享的 `users` 表独立出来（拷贝有效数据，保留 id）
- 精简为纯 Web 字段：去掉 `openid`、`is_key_match_member`、`key_match_recommendation_ids`、trial 相关列
- **`backend/app/models/user.py`**：`User.__tablename__` → `user_web`
- **`backend/alembic/versions/009_add_user_web.py`**：建表 + 幂等拷贝（表空才拷）+ 解除三张业务表（recommendations/view_records/daily_achievements）指向 `users.id` 的外键约束
- 模型关系（recommendation/view_record）改用显式 `primaryjoin`，脱离 DB 外键
- 清理 88 个 `wx_` 开头的小程序合成账号（无法用手机号密码登录）
- 同步 `users` 中付费未过期的老用户到 `user_web`（保留权益）

### 去掉体验用户 + 订阅推送

- 删除全部 trial 逻辑：4 个 trial 字段、`TrialUsage` 表、`/set-trial` 端点、注册赠送体验、前端体验横幅/锁态
- 删除微信订阅推送：`subscription` 模型/schema/service/api 四个文件，推荐确认时的推送触发，`WECHAT_SUBSCRIPTION_TEMPLATE_ID` 配置
- 用户体系简化为：**付费会员 / 非会员**（管理员为运营角色）

### 非会员付费墙 + 二维码引导

**`backend/app/api/recommendations.py`**
- 修复失效的付费墙：非会员真正**剥离**未出结果非公开场次的 `total_points`/`handicap`/`prediction_basis`，设 `_blur`（数据不再下发到浏览器）
- 公开场次、已出结果场次对所有人完整可见（引流 + 战绩可信度）

**`frontend/src/components/UpgradeGuide.vue`**（新增共享组件）
- 二维码升级弹窗（`/img/erweima.jpg`）+ 右下角"开通会员"浮动按钮
- 今日赛事页、历史战绩页复用，非会员自动弹一次（`sessionStorage` 去重）
- 卡片锁态、"查看更多"按钮均可触发

### 今日赛事页

**`frontend/src/views/Recommendations.vue`**
- 状态栏重做为 7 段流程状态机（场次→数据→确认），对应"下午2点前更新场次 / 4-6点更新数据 / 晚7-8点确认方案"节奏；数据优先、时间辅助；统一 Python 时钟修时区隐患；移动端精简文案
- 昨日战绩 Banner：从小程序迁移并重设计（渐变光晕卡片），后续去掉关闭按钮、去掉圆形环图、描述保留换行（`white-space: pre-line`）与编辑页一致
- 实时热度条改造：累计会员数改为基于上线基准日**单调累加**（跨天不回落），标签改"位会员在用"

**`backend/app/api/stats.py`**
- `social-proof` 说明为营销展示数；`total_users` 连续累加只增不减

### 历史战绩页

**`frontend/src/views/History.vue`**
- 近期好评：改两行布局，长队名不再截断（去 ellipsis，`word-break`）
- 底部加"查看更多好评战绩"按钮 → 弹二维码
- 非会员浮动"开通会员"按钮

### 登录/注册体验

**`frontend/src/views/Login.vue` + `backend/app/api/auth.py`**
- 未注册手机号登录 → 后端返回 404，前端**静默切到注册页**（保留手机号）
- 密码校验对齐后端：6-20 位 + 必须含字母和数字
- **`frontend/src/api/request.js`**：解析 FastAPI 422 校验错误数组，不再显示 `[object Object]`

### 密码管理

**`backend/app/api/profile.py`**
- 管理员重置密码：随机 6 位数字 → 固定 `123qwe`（含字母数字，可通过登录校验）
- 修改密码端点加字母+数字校验
- **`frontend/src/views/Profile.vue`**：个人中心补齐"修改密码"功能（弹窗，改后自动登出重登）

### 推荐管理 / 战绩编辑

- **`ManageRecommendations.vue`**：补上总结简述展示（`white-space: pre-line`）
- **`EditAchievement.vue`**：修复 emoji 图标列表（原为空字符串）；创建模式自动发现同日已有战绩并跳编辑；同日期冲突返回 409 + 一键跳编辑

### 配置

- `JWT_EXPIRE_DAYS`：7 → **30 天**（`.env` + `config.py`）
- `.gitignore`：补全 Python 忽略规则（`__pycache__`、`*.pyc`、`.venv` 等），从索引移除已追踪的 `.pyc`

### 部署

- 目标：腾讯云 `62.234.160.215` / 域名 `sportlens.online`（已配 443 SSL）
- nginx 托管前端静态 `dist/` + 代理 `/api` → `127.0.0.1:8000`；后端 systemd 常驻；Node 升级到 20 构建 Vite
- 数据库改动已直接作用于生产库（本地 `.env` 曾指向生产 MySQL）

## 2026-07-09

### 架构：前后端分离

- 前端代码收敛到 `frontend/`，后端保持在 `backend/`
- 数据库指向生产库 `62.234.160.215:3306/lottery_wxapp`
- 后端 `.env` 配置独立

### 登录/注册

**`frontend/src/views/Login.vue`**

- 手机号 + 密码登录/注册，去掉短信验证码
- 手机号 11 位校验（`1[3-9]\d{9}`），密码 6-10 位
- 注册/登录 Tab 切换
- 亮色主题：白底卡片 + SVG 神经网络节点背景 + 靛紫渐变强调色
- API：`POST /auth/login`、`POST /auth/register`

### 全局设计系统

**`frontend/src/styles/global.css`**

- CSS 变量：`--primary: #6366F1`（靛蓝）、`--primary-hover: #4F46E5`
- 亮色基调：`--bg: #F8FAFC`、`--surface: #FFFFFF`
- 移动端适配：`input` 16px 防 iOS 缩放、`button` 最小 44px 触摸、safe-area

### 导航

**`frontend/src/App.vue`**

- 桌面端（≥768px）：顶部 sticky 导航栏
- 移动端（<768px）：底部固定标签栏（SVG 图标 + 文字）
- 登录页和管理页隐藏导航

### 今日赛事页

**`frontend/src/views/Recommendations.vue`**

- 状态条：结算中/更新中/已更新，带动画
- 实时热度条
- 体验提示横幅
- 昨日战绩卡片（白底 + 靛紫 SVG 环形图）
- 运动类型筛选（全部/足球/篮球）
- 推荐卡片列表（`RecommendationCard.vue`）
- 配色对齐靛蓝紫设计系统

### 历史战绩页

**`frontend/src/views/History.vue`**

- Hero 统计卡片：白底 + 顶部靛紫渐变条 + SVG 仪表盘环形图
- 4 卡统计网格：足球整体、足球重心、篮球整体、篮球重心
- 月度趋势：横向滚动卡片，每张显示月份/好评率/进度条/场次
- 历史列表：卡片 + 左侧结果色条 + 胶囊戳（好评/走水/部分/蓄力）
- 展开显示场次详情（对阵/预测/组合方案）
- 总结说明始终可见
- 免费用户：Hero + 月度趋势 + 近期好评
- 付费用户：完整统计 + 筛选 + 历史列表
- 所有百分比 `Math.ceil()` 向上取整

### 个人中心页

**`frontend/src/views/Profile.vue`**

- 用户卡片：白底 + 靛紫渐变顶条 + 头像 + 昵称编辑 + 手机号复制
- 身份标签（管理员/会员/非会员）
- 会员状态卡片：状态指示器 + 剩余天数 + 进度条
- 会员使用指南（可折叠）
- 管理员入口：推荐管理 / 战绩Banner / 用户管理
- 复制账号兼容非 HTTPS 环境

### 管理后台

**推荐管理 `ManageRecommendations.vue`**
- 推荐列表：筛选/确认/浏览记录/编辑/标结果/删除
- 标结果弹窗、浏览记录弹窗
- 单场命中状态循环切换
- 创建入口 + 返回按钮

**创建/编辑推荐 `CreateRecommendation.vue`**
- 共用页面：有 ID 则编辑，无 ID 则创建
- 类型切换（足球/篮球）
- 标题 + 推广标题（textarea）
- 单场模块（可折叠）：场次ID、主队 vs 客队、总分、让分、置信度
- CSS switch 开关：公开/重心/精选/冷门预警
- AI 预测依据 + 使用模板按钮（足球/篮球两套模板）
- 组合方案模块（可折叠）
- 参照小程序原版结构

**用户管理 `ManageMembership.vue`**
- 手机号搜索 + 用户信息展示
- 4 档会员：15天/1月/3月/1年
- 取消会员 + 重置密码

**战绩 Banner `EditAchievement.vue`**
- 日期/标题/副标题
- 亮点数据管理（图标选择器）
- 详细描述 + 效果预览
- 首页展示开关

### 后端修复

**`backend/app/deps.py`**
- `get_current_user_optional` 容错：过期 token 返回 `None` 而非 401

**`backend/app/api/auth.py`**
- 已有 `/auth/login` 和 `/auth/register` 接口直接使用

### API 层

**`frontend/src/api/index.js`** 新增方法：
- `login` / `register` / `updateNickname`
- `getAdminRecommendations` / `getRecommendationDetail` / `createRecommendation` / `updateRecommendation` / `deleteRecommendation`
- `toggleConfirm` / `markResult` / `getViewRecords`
- `getStatistics` / `getMonthlyStatistics`（支持 params 筛选）
- `getAchievement` / `createAchievement` / `updateAchievement` / `deleteAchievement`
- `searchUser` / `setMembership` / `cancelMembership` / `resetPassword`

---

## 待优化

- [ ] 创建推荐：联赛字段（wxapp 有，web 暂缺）
- [ ] 场次卡片 UI 布局精简（去多层嵌套、对阵区优化）
- [ ] 统计口径统一：`/statistics` 与 `/monthly-statistics` 对空白状态处理不一致；`partial` 结果被忽略
- [ ] 昨日战绩（管理员手填）与历史统计（自动算）两套数字无法对齐
- [ ] 会员开通操作审计日志
- [ ] 付费老用户自动/定时同步（当前为一次性快照）
- [ ] 搜索功能
- [ ] 暗色模式
- [ ] PWA 支持
