---
name: xhs-overview
description: >-
  小红书热点 Agent 项目总览。包含架构、技术栈、启动方式、模块索引。
  当需要了解项目全貌、技术选型、模块关系时使用此 Skill。
---

# 小红书热点 Agent — 项目总览

## 架构

```
用户 ──▶ frontend (Vue 3)  ──▶ FastAPI 后端 ──▶ DeepSeek (OpenAI 兼容)
                                │                    │
                                │                    ▼
                                │              function calling
                                │                    │
                                ▼                    ▼
                             SQLite            TikHub API (小红书全量数据)
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| AI 模型 | DeepSeek (`deepseek-chat`)，通过 OpenAI 兼容接口 |
| 工具调用 | OpenAI function calling 协议 |
| 外部 API | TikHub — 小红书全量数据（热搜/搜索/笔记/用户/评论） |
| ORM | SQLAlchemy 2.0 (async) + aiosqlite |
| 数据库 | SQLite (`xhs_agent.db`) |
| 前端 | Vue 3 + Vite + Axios + markdown-it |

## 项目结构

```
backend/
  main.py        # FastAPI 入口，路由定义，请求/响应 Schema
  agent.py       # DeepSeek Agent 对话逻辑，function calling 循环
  tools.py       # 小红书工具定义与实现（TikHub API，7 个工具）
  models.py      # SQLAlchemy ORM 模型（Conversation / Message）
  database.py    # 异步数据库引擎 & 会话管理
  .env           # 环境变量（不提交）
  pyproject.toml # uv 依赖管理

frontend/
  src/
    App.vue              # 主应用（完整版）
    components/
      ChatInput.vue      # 输入框
      ChatMessages.vue   # 消息列表（Markdown 渲染）
      Sidebar.vue        # 侧边栏对话列表
```

## 启动方式

```bash
# 后端
cd backend
uv sync                # 安装依赖（自动创建 .venv）
cp .env.example .env   # 填入 DEEPSEEK_API_KEY 和 TIKHUB_API_TOKEN
uv run main.py         # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev            # http://localhost:10002，API 代理到 8000
```

## 环境变量

| 变量名 | 用途 |
|--------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `TIKHUB_API_TOKEN` | TikHub 小红书热搜 API Token |

## 数据流

1. 用户在前端输入问题
2. 前端 POST `/api/chat`，携带 `message` 和可选 `conversation_id`
3. 后端创建/获取对话，保存用户消息到 SQLite
4. 构造历史消息列表，调用 `chat_with_agent()`
5. Agent 判断是否需要调用工具（function calling）
6. 若需要 → 调用对应工具函数（热搜/搜索/详情/用户/评论等 7 个工具） → 获取数据 → 再次请求模型生成回复
7. 保存助手回复，返回前端展示

## 模块 Skill 索引

开发前请先阅读对应模块的 Skill 文档：

| Skill | 路径 | 内容 |
|-------|------|------|
| 后端 API | [backend-api](../backend-api/SKILL.md) | 路由、Schema、请求响应格式 |
| 后端 Agent | [backend-agent](../backend-agent/SKILL.md) | DeepSeek 对话、function calling 循环 |
| 后端 Tools | [backend-tools](../backend-tools/SKILL.md) | 小红书全量工具（7 个）、TikHub API 接入 |
| 后端 Models | [backend-models](../backend-models/SKILL.md) | ORM 模型、表结构 |
| 后端 Database | [backend-db](../backend-db/SKILL.md) | 异步引擎、会话管理、建表 |
