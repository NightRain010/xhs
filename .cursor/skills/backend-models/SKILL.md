---
name: backend-models
description: >-
  SQLAlchemy ORM 模型定义，包含 Conversation、Message、EmailSchedule 三张表。
  当需要修改表结构、新增字段、调整关系映射或理解数据模型时使用。
---

# 后端 Models 模块

文件：`backend/models.py`

## 数据模型

### Conversation（对话）

表名：`conversations`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` (PK, 自增) | 对话 ID |
| `title` | `String(200)` | 对话标题，默认"新对话" |
| `created_at` | `DateTime` | 创建时间，`server_default=func.now()` |

关系：`messages` → 一对多关联 Message，级联删除 (`cascade="all, delete-orphan"`)

### Message（消息）

表名：`messages`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` (PK, 自增) | 消息 ID |
| `conversation_id` | `int` (FK) | 关联 `conversations.id` |
| `role` | `String(20)` | 角色：`user` / `assistant` / `tool` |
| `content` | `Text` | 消息内容，默认空字符串 |
| `tool_name` | `String(100)` | 工具名称（可空） |
| `created_at` | `DateTime` | 创建时间 |

关系：`conversation` → 多对一关联 Conversation

### EmailSchedule（邮件定时任务）

表名：`email_schedules`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` (PK, 自增) | 任务 ID |
| `recipient_email` | `String(200)` | 收件人邮箱 |
| `email_subject` | `String(300)` | 邮件主题模板，支持 `{date}` 变量，默认 "小红书热点日报 - {date}" |
| `prompt` | `Text` | 发送给 Agent 的提示词 |
| `cron_hour` | `int` | 发送小时（0-23），默认 9 |
| `cron_minute` | `int` | 发送分钟（0-59），默认 0 |
| `cron_day_of_week` | `String(50)` | 发送星期，APScheduler cron 格式（如 `mon,wed,fri`），`*` 表示每天 |
| `enabled` | `bool` | 是否启用，默认 True |
| `last_sent_at` | `DateTime` | 上次发送时间（可空） |
| `last_send_status` | `String(20)` | 上次发送状态：`success` / `failed` / `empty`（可空） |
| `created_at` | `DateTime` | 创建时间 |

## ER 关系

```
Conversation 1 ──── N Message
     │                   │
     ├─ id (PK)          ├─ id (PK)
     ├─ title             ├─ conversation_id (FK)
     └─ created_at        ├─ role
                          ├─ content
                          ├─ tool_name
                          └─ created_at

EmailSchedule（独立表）
     ├─ id (PK)
     ├─ recipient_email
     ├─ email_subject
     ├─ prompt
     ├─ cron_hour / cron_minute / cron_day_of_week
     ├─ enabled
     ├─ last_sent_at / last_send_status
     └─ created_at
```

## ORM 特性

- 使用 SQLAlchemy 2.0 `Mapped` 类型注解风格
- 基类从 `database.py` 导入 `Base`（`DeclarativeBase`）
- 消息按 `created_at` 排序（在 relationship 中指定）

## 扩展指南

新增字段时：
1. 在模型类中添加 `Mapped` 字段
2. 如果需要在 API 响应中暴露，同步更新 `main.py` 中对应的 `*Out` Schema
3. 删除旧的 `xhs_agent.db` 文件或使用 Alembic 迁移（当前无迁移工具，重建数据库即可）

新增模型时：
1. 在 `models.py` 中定义新类，继承 `Base`
2. 确保在 `main.py` 或 `database.py` 中导入，使 `Base.metadata` 能发现它
3. 应用启动时 `init_db()` 会自动建表

## 相关模块

- 数据库引擎 → [backend-db](../backend-db/SKILL.md)
- API Schema → [backend-api](../backend-api/SKILL.md)
