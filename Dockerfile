# ========== 阶段 1: 前端构建 ==========
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ========== 阶段 2: 后端 + 静态文件 ==========
FROM python:3.12-slim

WORKDIR /app

# 后端依赖（使用 pip，兼容性更好）
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy aiosqlite \
    openai httpx pydantic python-dotenv aiosmtplib apscheduler markdown email-validator

# 后端代码（.dockerignore 排除 .venv .env *.db）
COPY backend/ ./

# 前端构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

# 数据目录（SQLite 持久化）
RUN mkdir -p /app/data

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite+aiosqlite:////app/data/xhs_agent.db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
