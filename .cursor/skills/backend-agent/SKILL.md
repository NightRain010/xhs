---
name: backend-agent
description: >-
  DeepSeek Agent 对话模块，实现 function calling 循环。
  当需要修改 AI 对话逻辑、调整 System Prompt、增加工具调用、
  或理解 Agent 运行机制时使用。
---

# 后端 Agent 模块

文件：`backend/agent.py`

## 概述

使用 OpenAI 兼容接口对接 DeepSeek，支持 function calling 工具调用循环。
工具调用支持带参数，自动解析 `tool_call.function.arguments` 并以 `**kwargs` 传入工具函数。

## 配置

| 配置项 | 值 |
|--------|-----|
| 模型 | `deepseek-chat` |
| API Base | `https://api.deepseek.com` |
| 客户端 | `openai.AsyncOpenAI` |
| 环境变量 | `DEEPSEEK_API_KEY` |

## System Prompt

定义 Agent 角色为小红书内容助手，指示其拥有 7 项能力：
1. 查询实时热搜榜单
2. 按关键词搜索笔记（支持排序和类型筛选）
3. 查看笔记详情（标题、正文、互动数据）
4. 查询用户个人资料
5. 按关键词搜索用户/博主
6. 查看用户发布的笔记列表
7. 查看笔记评论

## 核心函数

### `chat_with_agent_stream(messages: list[dict]) -> AsyncGenerator[dict, None]`

入参：OpenAI 格式的对话历史（不含 system prompt）

流程：
1. 在消息列表前插入 system prompt
2. 调用 `client.chat.completions.create()`，传入 `tools=XHS_TOOLS`，`stream=True`
3. **循环处理工具调用**：若返回 `tool_calls`
   - 将 assistant 消息加入上下文
   - 逐个执行工具函数（**解析 arguments 并传入参数**），将结果以 `role: "tool"` 追加
   - 再次调用模型，直到不再请求工具
4. yield SSE 事件：`delta`（流式文本）、`tool_call`（工具调用通知）、`done`（完成）

## Function Calling 循环图

```
调用模型(stream) ──▶ 收集 tool_calls?
                        │
                   ┌────┴────┐
                   │ Yes     │ No
                   ▼         ▼
              解析参数    yield done
              执行工具
              追加结果
              再次调用模型
                   │
                   └──▶ 回到判断
```

## 工具参数传递

```python
args = json.loads(tc["function"]["arguments"] or "{}")
result = await fn(**args)
```

无参数的工具（如 `fetch_xhs_hot_list`）会收到空 dict，`**{}` 等价于无参调用。

## 工具注册

- 工具定义：从 `tools.py` 导入 `XHS_TOOLS`（7 个 OpenAI function schema）
- 工具函数：从 `tools.py` 导入 `TOOL_FUNCTIONS`（`dict[str, Callable]`）
- `tool_choice="auto"` — 模型自行决定是否调用工具

## 扩展指南

添加新工具时：
1. 在 `tools.py` 中定义工具的 OpenAI schema（加入 `XHS_TOOLS` 列表）
2. 实现对应的异步函数
3. 注册到 `TOOL_FUNCTIONS` 字典
4. Agent 会自动发现和调用新工具，无需修改 `agent.py`

修改 Agent 行为时：
- 调整 `SYSTEM_PROMPT` 改变角色和回答风格
- 修改 `tool_choice` 参数控制工具调用策略

## 相关模块

- 工具定义 → [backend-tools](../backend-tools/SKILL.md)
- API 路由（调用入口） → [backend-api](../backend-api/SKILL.md)
