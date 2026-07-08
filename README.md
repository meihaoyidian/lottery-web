# AI竞界 - 专业赛事分析

前后端分离项目。

## 目录结构

```
lottery-web/
├── frontend/          # Vue 3 + Vite 前端
│   ├── src/           # Vue 源码
│   ├── public/        # 静态资源
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/           # FastAPI + SQLAlchemy 后端
│   ├── app/           # 应用代码
│   ├── alembic/       # 数据库迁移
│   ├── tests/         # 测试
│   └── requirements.txt
└── README.md
```

## 启动

### 后端

```bash
cd backend
cp .env.example .env  # 编辑配置
bash setup.sh
bash start.sh
```

### 前端

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```
