# 项目：小红书热点 Agent

## 技术栈

- 后端：Python + FastAPI + SQLAlchemy (async) + aiosqlite + SQLite
- 前端：Vue 3 + Vite + Axios + markdown-it
- AI：OpenAI 兼容接口对接 DeepSeek（model: deepseek-chat），支持 function calling
- 外部 API：TikHub（小红书全量数据 — 热搜/搜索/笔记/用户/评论，共 7 个工具）

## 项目结构

```
backend/
  main.py            # FastAPI 入口，路由定义，请求/响应 Schema
  agent.py           # DeepSeek Agent 对话逻辑，function calling 循环
  tools.py           # 小红书工具定义与实现（TikHub API，7 个工具）
  models.py          # SQLAlchemy ORM 模型（Conversation / Message / EmailSchedule）
  database.py        # 异步数据库引擎 & 会话管理
  email_service.py   # 邮件发送模块（aiosmtplib + SMTP）
  scheduler.py       # 定时调度模块（APScheduler，邮件定时发送）
  .env               # 环境变量（不提交）
  pyproject.toml     # uv 依赖管理

frontend/
  src/
    App.vue              # 主应用（完整版）
    components/
      ChatInput.vue      # 输入框
      ChatMessages.vue   # 消息列表（Markdown 渲染）
      Sidebar.vue        # 侧边栏对话列表
```

## .env 文件模板

在 `backend/` 目录创建 `.env`，不提交到 git：

```env
DEEPSEEK_API_KEY=your_api_key_here
TIKHUB_API_TOKEN=your_tikhub_token_here

# SMTP 邮件服务（以 QQ 邮箱为例，需开启 SMTP 并获取授权码）
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=your_smtp_auth_code
SMTP_FROM=your_email@qq.com
SMTP_USE_TLS=true
```

## 模块文档索引（Skills）

开发前请先阅读对应模块的 Skill 文档，了解已有实现和设计约定：

| Skill | 路径 | 内容 |
|-------|------|------|
| 项目总览 | `.cursor/skills/overview/SKILL.md` | 架构、技术栈、启动方式、数据流、模块索引 |
| 后端 API | `.cursor/skills/backend-api/SKILL.md` | 路由清单、Schema 定义、请求响应格式 |
| 后端 Agent | `.cursor/skills/backend-agent/SKILL.md` | DeepSeek 对话、function calling 循环机制 |
| 后端 Tools | `.cursor/skills/backend-tools/SKILL.md` | 小红书全量工具（7 个）、TikHub API 接入、新增工具模板 |
| 后端 Models | `.cursor/skills/backend-models/SKILL.md` | ORM 模型、表结构、ER 关系 |
| 后端 Database | `.cursor/skills/backend-db/SKILL.md` | 异步引擎、会话管理、建表逻辑 |
| 后端 Email | `.cursor/skills/backend-email/SKILL.md` | 邮件发送、定时调度、SMTP 配置 |
