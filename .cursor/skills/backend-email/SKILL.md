---
name: backend-email
description: >-
  邮件发送与定时调度模块。包含 SMTP 邮件发送、APScheduler 定时任务管理、
  邮件定时 API 端点。当需要修改邮件发送逻辑、调整定时策略、或新增邮件相关功能时使用。
---

# 后端邮件定时发送模块

## 概述

通过 APScheduler 定时调度 + aiosmtplib 异步邮件发送，实现 Agent 结果的定时邮件推送。

## 涉及文件

| 文件 | 职责 |
|------|------|
| `email_service.py` | SMTP 邮件发送、Markdown→HTML 转换 |
| `scheduler.py` | APScheduler 定时任务管理、Agent 执行 + 发送编排 |
| `models.py` | `EmailSchedule` ORM 模型 |
| `main.py` | 邮件定时 API 端点（CRUD + 测试） |

## 数据模型：EmailSchedule

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int (PK) | 自增主键 |
| recipient_email | str(200) | 收件人邮箱 |
| email_subject | str(300) | 邮件主题模板，支持 `{date}` 变量替换 |
| prompt | text | Agent 提示词（默认：获取热搜并分析） |
| cron_hour | int | 发送小时（0-23） |
| cron_minute | int | 发送分钟（0-59） |
| cron_day_of_week | str(50) | 发送星期（APScheduler cron 格式，`*` 表示每天，`mon,wed,fri` 选择特定日） |
| enabled | bool | 是否启用 |
| last_sent_at | datetime | 上次发送时间 |
| last_send_status | str(20) | 上次发送状态：`success` / `failed` / `empty` |
| created_at | datetime | 创建时间 |

## API 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/email-schedules` | 创建定时邮件任务 |
| GET | `/api/email-schedules` | 获取所有定时任务 |
| PUT | `/api/email-schedules/{id}` | 更新定时任务（可改时间/邮箱/主题/星期/启停） |
| DELETE | `/api/email-schedules/{id}` | 删除定时任务 |
| POST | `/api/email-schedules/{id}/test` | 手动触发一次发送（测试） |

## 前端配置项

通过邮件设置弹窗，用户可在前端管理以下配置：

| 配置项 | 说明 |
|--------|------|
| 收件人邮箱 | 接收邮件的邮箱地址 |
| 邮件主题 | 支持 `{date}` 变量自动替换为当天日期 |
| 发送时间 | 小时:分钟 |
| 发送日期 | 星期一到日，可多选；不选则每天发送 |
| Agent 提示词 | 控制 AI 生成什么内容发送 |
| 启用/暂停 | 一键切换任务状态 |
| 编辑 | 修改已有任务的所有配置 |
| 测试发送 | 立即触发一次，用于验证配置 |

## 执行流程

```
APScheduler cron 触发（支持 day_of_week）
    ↓
scheduler._run_agent_and_send(schedule_id)
    ↓
从 DB 读取 EmailSchedule 配置
    ↓
chat_with_agent_stream(prompt) → 获取 Agent 回复
    ↓
email_subject 模板替换 {date} → 生成邮件主题
    ↓
markdown_to_html() → 转为 HTML 邮件
    ↓
email_service.send_email() → 通过 SMTP 发送
    ↓
更新 last_sent_at + last_send_status
```

## 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.qq.com` |
| `SMTP_PORT` | SMTP 端口 | `465` |
| `SMTP_USER` | 登录用户名 | `xxx@qq.com` |
| `SMTP_PASSWORD` | SMTP 授权码（非登录密码） | `abcdefghijklmnop` |
| `SMTP_FROM` | 发件人显示地址 | `xxx@qq.com` |
| `SMTP_USE_TLS` | 是否使用 TLS | `true` |

## 扩展指南

- 调整发送频率：修改 `EmailSchedule` 模型和 `scheduler.py` 中的 `CronTrigger`，可支持更复杂的 cron 表达式
- 添加邮件模板：修改 `email_service.py` 中的 `markdown_to_html()`
- 支持多种邮件服务商：修改 `.env` 中的 SMTP 配置即可（QQ/163/Gmail 等）

## 相关模块

- Agent 逻辑 → [backend-agent](../backend-agent/SKILL.md)
- 数据模型 → [backend-models](../backend-models/SKILL.md)
- API 路由 → [backend-api](../backend-api/SKILL.md)
