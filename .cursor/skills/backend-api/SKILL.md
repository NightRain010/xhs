---
name: backend-api
description: >-
  后端 FastAPI 路由与请求/响应 Schema。包含聊天、对话管理等 API 端点定义。
  当需要新增/修改 API 路由、调整请求格式、处理 CORS 或理解接口契约时使用。
---

# 后端 API 模块

文件：`backend/main.py`

## FastAPI 应用

- 标题：`小红书热点 Agent`
- 启动时通过 `lifespan` 调用 `init_db()` 自动建表
- CORS 全开放（`allow_origins=["*"]`）
- 默认端口 `8000`

## 请求/响应 Schema

### ChatRequest

```python
class ChatRequest(BaseModel):
    conversation_id: int | None = None   # 可选，继续已有对话
    message: str                          # 用户消息
```

### MessageOut

```python
class MessageOut(BaseModel):
    id: int
    role: str          # "user" | "assistant" | "tool"
    content: str
    tool_name: str | None = None
```

### ConversationOut

```python
class ConversationOut(BaseModel):
    id: int
    title: str
    messages: list[MessageOut] = []
```

## API 端点

| 方法 | 路径 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/chat` | 发送消息并获取 AI 回复 | `ChatRequest` | `{ conversation_id, reply }` |
| GET | `/api/conversations` | 获取所有对话列表（含消息） | — | `list[ConversationOut]` |
| GET | `/api/conversations/{conv_id}` | 获取单个对话详情 | — | `ConversationOut` |
| DELETE | `/api/conversations/{conv_id}` | 删除指定对话 | — | `{ ok: true }` |

## POST /api/chat 流程

1. 若 `conversation_id` 存在且有效 → 复用对话；否则创建新对话（标题取消息前 30 字）
2. 保存用户消息到 `messages` 表
3. 查询该对话所有历史消息，构造 OpenAI 格式 `messages` 列表
4. 调用 `chat_with_agent(openai_messages)` 获取回复
5. 保存助手回复，返回 `{ conversation_id, reply }`

## 依赖注入

- `db: AsyncSession = Depends(get_db)` — 所有路由通过依赖注入获取异步数据库会话

## 扩展指南

新增 API 端点时：
1. 在 `main.py` 中定义路由函数
2. 如需新 Schema，在同文件 `# Schemas` 区域添加 Pydantic 模型
3. 使用 `Depends(get_db)` 获取数据库会话
4. 遵循 `/api/` 前缀命名约定

## 相关模块

- Agent 逻辑 → [backend-agent](../backend-agent/SKILL.md)
- 数据模型 → [backend-models](../backend-models/SKILL.md)
- 数据库会话 → [backend-db](../backend-db/SKILL.md)
