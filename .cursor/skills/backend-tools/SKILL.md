---
name: backend-tools
description: >-
  小红书工具模块，封装 TikHub API 全量调用（7 个工具）。包含 OpenAI function calling 工具定义
  和实际数据获取逻辑。当需要新增外部 API 工具、修改数据解析、或接入新数据源时使用。
---

# 后端 Tools 模块

文件：`backend/tools.py`

## 概述

定义 Agent 可调用的外部工具。包含 7 个小红书相关工具，覆盖热搜、搜索、笔记详情、用户信息、评论等功能。

## 外部 API

| 项目 | 值 |
|------|-----|
| 提供商 | TikHub |
| 基础路径 | `https://api.tikhub.io/api/v1/xiaohongshu/web_v2/` |
| 认证 | `Bearer {TIKHUB_API_TOKEN}` |
| 环境变量 | `TIKHUB_API_TOKEN` |
| 超时 | 15 秒 |
| HTTP 客户端 | `httpx.AsyncClient` |

## 辅助函数

### `_tikhub_get(path, params) -> dict`

所有工具共用的 HTTP GET 请求函数，拼接基础路径、添加认证 Header，返回解析后的 JSON。

## 工具一览（XHS_TOOLS）

| 工具名 | API 端点 | 参数 | 用途 |
|--------|----------|------|------|
| `fetch_xhs_hot_list` | `fetch_hot_list` | 无 | 获取热搜榜单 |
| `search_xhs_notes` | `fetch_search_notes` | keywords(必填), page, sort_type, note_type | 搜索笔记 |
| `fetch_xhs_note_detail` | `fetch_feed_notes_v2` | note_id(必填) | 获取笔记详情 |
| `fetch_xhs_user_info` | `fetch_user_info_app` | user_id(必填) | 获取用户信息 |
| `search_xhs_users` | `fetch_search_users` | keywords(必填), page | 搜索用户 |
| `fetch_xhs_user_notes` | `fetch_home_notes_app` | user_id(必填), cursor | 获取用户笔记列表 |
| `fetch_xhs_note_comments` | `fetch_sub_comments` | note_id(必填), cursor | 获取笔记评论 |

## 工具函数详情

### `fetch_xhs_hot_list() -> str`

返回 JSON 数组，每项含 `rank`、`title`、`score`、`word_type`。

### `search_xhs_notes(keywords, page=1, sort_type="general", note_type=0) -> str`

返回 JSON 数组，每项含 `note_id`、`title`、`desc`、`type`、`liked_count`、`user`、`user_id`。

sort_type 可选值：`general`（综合）、`time_descending`（最新）、`popularity_descending`（最热）。
note_type 可选值：`0`（全部）、`1`（视频）、`2`（图文）。

### `fetch_xhs_note_detail(note_id) -> str`

返回 JSON 对象，含 `note_id`、`title`、`desc`、`type`、互动数据（liked/collected/comment/share_count）、`user`、`tag_list`、`images`、`video_url`。

### `fetch_xhs_user_info(user_id) -> str`

返回 JSON 对象，含 `user_id`、`nickname`、`desc`、`gender`、`ip_location`、`follows`、`fans`、`liked_and_collected`。

### `search_xhs_users(keywords, page=1) -> str`

返回 JSON 数组，每项含 `user_id`、`nickname`、`desc`、`fans`、`note_count`。

### `fetch_xhs_user_notes(user_id, cursor="") -> str`

返回 JSON 对象，含 `cursor`（翻页游标）和 `notes` 数组（每项含 `note_id`、`title`、`type`、`liked_count`）。

### `fetch_xhs_note_comments(note_id, cursor="") -> str`

返回 JSON 对象，含 `cursor` 和 `comments` 数组（每项含 `comment_id`、`content`、`user`、`liked_count`、`sub_comment_count`、`create_time`）。

## 工具注册表（TOOL_FUNCTIONS）

```python
TOOL_FUNCTIONS = {
    "fetch_xhs_hot_list": fetch_xhs_hot_list,
    "search_xhs_notes": search_xhs_notes,
    "fetch_xhs_note_detail": fetch_xhs_note_detail,
    "fetch_xhs_user_info": fetch_xhs_user_info,
    "search_xhs_users": search_xhs_users,
    "fetch_xhs_user_notes": fetch_xhs_user_notes,
    "fetch_xhs_note_comments": fetch_xhs_note_comments,
}
```

Agent 通过函数名查找此字典来执行工具。`agent.py` 会自动解析 `tool_call.function.arguments` 并以 `**kwargs` 传入。

## 新增工具模板

```python
# 1. 添加工具 schema 到 XHS_TOOLS
XHS_TOOLS.append({
    "type": "function",
    "function": {
        "name": "your_tool_name",
        "description": "工具描述，告诉模型何时调用",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数说明"},
            },
            "required": ["param1"],
        },
    },
})

# 2. 实现异步工具函数（可复用 _tikhub_get 辅助函数）
async def your_tool_name(param1: str) -> str:
    data = await _tikhub_get("api_endpoint", {"param1": param1})
    # 解析 data...
    return json.dumps(result, ensure_ascii=False)

# 3. 注册到字典
TOOL_FUNCTIONS["your_tool_name"] = your_tool_name
```

## 相关模块

- Agent 调用逻辑 → [backend-agent](../backend-agent/SKILL.md)
- API 文档 → `api.md`（TikHub 响应示例）
