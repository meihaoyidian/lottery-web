# 部署与更新文档

> lottery-web 生产部署运维手册。服务器：腾讯云 CentOS 7，公网 `62.234.160.215`，域名 `sportlens.online`（已配 443 SSL）。

## 生产环境速览

| 组件 | 说明 |
|------|------|
| 项目路径 | `/root/codes/lottery-web` |
| 后端 | FastAPI，systemd 服务 `lottery-web`，监听 `127.0.0.1:8000` |
| 前端 | Vite 构建产物 `frontend/dist/`，由 nginx 静态托管 |
| 反向代理 | nginx，`/api/*` → `127.0.0.1:8000`，其余走前端静态 |
| 数据库 | 本机 MySQL `localhost:3306/lottery_wxapp`，Web 用户表 `user_web` |
| Python | pyenv 环境 `py3.11.9` |
| Node | 服务器 **跑不了** Node 20（CentOS 7 glibc 2.17 太旧），前端只能本地构建后上传 |

关键配置文件：
- 后端环境变量：`/root/codes/lottery-web/backend/.env`
- systemd：`/etc/systemd/system/lottery-web.service`
- nginx：`/etc/nginx/conf.d/sportlens.online.conf`

---

## 日常更新流程

### 一、后端更新（改了 backend/ 代码）

```bash
cd /root/codes/lottery-web
git pull                        # 拉最新代码（github 慢就用镜像：git pull https://ghfast.top/https://github.com/meihaoyidian/lottery-web.git master）
systemctl restart lottery-web   # 重启后端
systemctl status lottery-web --no-pager   # 确认 active (running)
curl http://127.0.0.1:8000/health          # {"status":"ok"...}
```

> 若改了 `requirements.txt`，先激活环境装依赖：
> `pyenv activate py3.11.9 && pip install -r backend/requirements.txt`，再 restart。

### 二、前端更新（改了 frontend/ 代码）

服务器无法构建，**在本地 Mac 构建后 scp 上传**：

```bash
# ① 本地 Mac
cd /Users/apple/Documents/chendb/lottery-web/frontend
npm run build                   # 或 pnpm run build

# ② 上传到服务器（提示输入服务器密码）
scp -r dist root@62.234.160.215:/root/codes/lottery-web/frontend/

# ③ 服务器上重设权限（有新文件时必做，否则 nginx 403）
ssh root@62.234.160.215 "chmod -R o+rX /root/codes/lottery-web/frontend/dist"
```

> nginx 直接读静态文件，**前端更新不用重启 nginx**。

### 三、数据库变更（新增 alembic 迁移）

```bash
cd /root/codes/lottery-web/backend
pyenv activate py3.11.9
python -c "from alembic.config import Config; from alembic import command; command.upgrade(Config('alembic.ini'),'head')"
```

---

## 首次部署步骤（重装/迁移服务器时用）

### 1. 拉代码

```bash
cd /root/codes
git clone https://ghfast.top/https://github.com/meihaoyidian/lottery-web.git   # 国内用镜像前缀
cd lottery-web && git remote set-url origin https://github.com/meihaoyidian/lottery-web.git
```

### 2. 后端 .env

`/root/codes/lottery-web/backend/.env`：
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=<MySQL密码>
DB_NAME=lottery_wxapp
DB_CHARSET=utf8mb4
JWT_SECRET_KEY=<openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=30
API_V1_PREFIX=/api/v1
PROJECT_NAME=赛事推演预测系统
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False
CORS_ORIGINS=["https://sportlens.online","https://www.sportlens.online"]
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
REVIEW_MODE=False
```

### 3. 后端依赖 + systemd

```bash
pyenv activate py3.11.9
pip install -r /root/codes/lottery-web/backend/requirements.txt

cat > /etc/systemd/system/lottery-web.service << 'EOF'
[Unit]
Description=Lottery Web Backend
After=network.target mysqld.service
[Service]
Type=simple
User=root
WorkingDirectory=/root/codes/lottery-web/backend
ExecStart=/root/.pyenv/versions/py3.11.9/bin/python -m app.main
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now lottery-web
```

### 4. 前端（本地构建上传，见"日常更新·二"）

### 5. nginx

`/etc/nginx/conf.d/sportlens.online.conf`：
```nginx
server {
    listen 80;
    server_name sportlens.online www.sportlens.online;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl default_server;
    server_name sportlens.online www.sportlens.online;
    ssl_certificate     /etc/nginx/ssl/sportlens.online/sportlens.online_bundle.pem;
    ssl_certificate_key /etc/nginx/ssl/sportlens.online/sportlens.online.key;
    root /root/codes/lottery-web/frontend/dist;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /assets/ { expires 30d; add_header Cache-Control "public, immutable"; }
    location /img/ { expires 7d; }
}
```

### 6. 目录权限（关键，否则前端 403/500）

`/root` 默认 700，nginx 进不去。执行：
```bash
chmod o+x /root /root/codes /root/codes/lottery-web /root/codes/lottery-web/frontend
chmod -R o+rX /root/codes/lottery-web/frontend/dist
nginx -t && systemctl reload nginx
```

---

## 常用运维命令

```bash
# 后端状态 / 日志
systemctl status lottery-web --no-pager
journalctl -u lottery-web -f
tail -f /root/codes/lottery-web/backend/logs/app.log

# nginx
nginx -t                       # 测配置
systemctl reload nginx         # 重载
tail -20 /var/log/nginx/error.log

# 健康检查
curl http://127.0.0.1:8000/health
curl -I https://sportlens.online
```

---

## 排错速查

| 现象 | 原因 | 处理 |
|------|------|------|
| 前端 500/403，error.log 里 `Permission denied` | `/root` 目录权限，nginx 读不了 dist | 重跑上面"目录权限"两条 chmod |
| 打开域名是 JSON 不是网站 | nginx 把 `/` 也代理到 8000 了 | 检查 nginx 配置 `location /` 是 `try_files` 而非 `proxy_pass` |
| API 404 | 健康检查在 `/health` 不在 `/api/v1/health` | 用 `/api/v1/...` 访问业务接口 |
| `git clone/pull` 卡住 | 服务器连不上 github（国内） | 加镜像前缀 `https://ghfast.top/` |
| 服务器 `npm run build` 报 glibc 错 | CentOS 7 glibc 太旧跑不了 Node 20 | 本地构建 + scp 上传，服务器不装 Node |
| 后端起不来 | `.env` 缺失 / DB 密码错 / python 路径错 | 看 `journalctl -u lottery-web`；确认 systemd `ExecStart` 指向 `/root/.pyenv/versions/py3.11.9/bin/python` |

---

## 注意事项

- 前端 API 地址硬编码在 `frontend/src/api/request.js`：生产走 `https://sportlens.online/api/v1`。换域名需同步改这里并重新构建。
- 数据库 `user_web` 与小程序的 `users` 表**共库不共表**，Web 端改动不影响小程序。
- 付费老用户从 `users` 同步到 `user_web` 是**一次性快照**，非自动，需手动同步。
- JWT 登录态 30 天，改 `.env` 的 `JWT_EXPIRE_DAYS` 后需 `systemctl restart lottery-web`。
