# 小红书热点 Agent

基于 DeepSeek 大模型的智能助手，可以实时查询小红书热搜榜单。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue 3 + Vite
- **AI**: DeepSeek (Function Calling)
- **数据源**: TikHub API (小红书热搜)

## 快速开始（本地开发）

### 1. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入 DEEPSEEK_API_KEY 和 TIKHUB_API_TOKEN
```

### 2. 启动后端

```bash
cd backend
uv sync
uv run main.py
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:10002

---

## 服务器部署（Docker 一键部署）

**节省流量**：前后端同域、Gzip 压缩、静态资源合并  
**快速部署**：单容器，一条命令启动

### 1. 配置环境变量

在项目根目录创建 `.env`（或复制 `docker/env.example`）：

```bash
cp docker/env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY、TIKHUB_API_TOKEN 等
```

### 2. 构建并启动

```bash
docker compose up -d --build
```

### 3. 访问

打开 http://服务器IP:8000 即可使用（前后端已合并，无需单独访问前端端口）

### 数据持久化

SQLite 数据库存储在 Docker volume `xhs_data`，重启容器数据不丢失。
