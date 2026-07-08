# lottery-web 更新日志

> lottery-wxapp（微信小程序）→ lottery-web（浏览器端），后端逻辑和数据库复用。

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
- 身份标签（管理员/完整版/体验版/基础版）
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

- [ ] 推荐管理：编辑推荐后列表刷新
- [ ] 创建推荐：联赛字段（wxapp 有，web 暂缺）
- [ ] 搜索功能
- [ ] 暗色模式
- [ ] PWA 支持
