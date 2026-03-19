import os
import json
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

TIKHUB_TOKEN = os.getenv("TIKHUB_API_TOKEN", "")

TIKHUB_BASE = "https://api.tikhub.io/api/v1/xiaohongshu"

MAX_RETRIES = 2
RETRY_DELAY = 1.5


async def _tikhub_get(path: str, params: dict | None = None) -> dict:
    """统一的 TikHub GET 请求，内置重试和错误处理。
    path 格式示例: "web_v2/fetch_hot_list" 或 "app/search_notes"
    """
    headers = {"Authorization": f"Bearer {TIKHUB_TOKEN}"}
    url = f"{TIKHUB_BASE}/{path}"

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=headers, params=params)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 400 and attempt <= MAX_RETRIES:
                logger.warning("TikHub %s 返回 400, 第 %d/%d 次重试...", path, attempt, MAX_RETRIES)
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue

            body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
            detail = body.get("detail", {})
            msg = detail.get("message_zh", detail.get("message", "")) if isinstance(detail, dict) else str(detail)
            return {"_error": True, "status": resp.status_code, "message": msg or f"HTTP {resp.status_code}"}

        except httpx.TimeoutException:
            if attempt <= MAX_RETRIES:
                logger.warning("TikHub %s 超时, 第 %d/%d 次重试...", path, attempt, MAX_RETRIES)
                await asyncio.sleep(RETRY_DELAY * attempt)
                continue
            return {"_error": True, "status": 0, "message": "请求超时，TikHub API 无响应"}
        except Exception as e:
            return {"_error": True, "status": 0, "message": f"请求异常: {e}"}

    return {"_error": True, "status": 0, "message": "重试次数已用完"}


def _err(data: dict) -> str | None:
    if data.get("_error"):
        return json.dumps({"error": data.get("message", "未知错误")}, ensure_ascii=False)
    return None


# ---------------------------------------------------------------------------
# OpenAI function-calling 工具定义
# ---------------------------------------------------------------------------

XHS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_xhs_hot_list",
            "description": "获取小红书当前的热搜榜单/热点话题列表，返回热门话题标题和热度分数。当用户询问今天的热点、热搜、流行趋势或小红书相关内容时使用此工具。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_xhs_notes",
            "description": "按关键词搜索小红书笔记。当用户想查找某个话题、产品、地点等相关笔记时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "搜索关键词"},
                    "page": {"type": "integer", "description": "页码，默认 1"},
                    "sort_type": {
                        "type": "string",
                        "enum": ["general", "time_descending", "popularity_descending"],
                        "description": "排序方式：general=综合, time_descending=最新, popularity_descending=最热",
                    },
                    "note_type": {
                        "type": "string",
                        "enum": ["0", "1", "2"],
                        "description": "笔记类型：0=全部, 1=视频, 2=图文",
                    },
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_xhs_note_detail",
            "description": "根据笔记 ID 获取小红书单条笔记的详细内容（标题、正文、点赞收藏等互动数据、图片/视频链接）。",
            "parameters": {
                "type": "object",
                "properties": {"note_id": {"type": "string", "description": "小红书笔记 ID"}},
                "required": ["note_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_xhs_user_info",
            "description": "根据用户 ID 获取小红书用户的个人资料（昵称、简介、粉丝数、关注数、获赞与收藏数等）。",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string", "description": "小红书用户 ID"}},
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_xhs_users",
            "description": "按关键词搜索小红书用户/博主。当用户想找某个领域的博主时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "搜索关键词"},
                    "page": {"type": "integer", "description": "页码，默认 1"},
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_xhs_user_notes",
            "description": "获取某个用户主页发布的笔记列表。当用户想看某个博主发了哪些内容时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "小红书用户 ID"},
                    "cursor": {"type": "string", "description": "分页游标，首次请求不传"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_xhs_note_comments",
            "description": "获取某条笔记下的评论列表。当用户想了解某条笔记的评论/讨论时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "小红书笔记 ID"},
                    "cursor": {"type": "string", "description": "分页游标，首次请求不传"},
                },
                "required": ["note_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# 工具实现 — 每个功能按稳定性优先选择端点
# ---------------------------------------------------------------------------

# ---- 1. 热搜 (web_v2 稳定) ----
async def fetch_xhs_hot_list() -> str:
    data = await _tikhub_get("web_v2/fetch_hot_list")
    if err := _err(data):
        return err
    items = data.get("data", {}).get("data", {}).get("items", [])
    if not items:
        return json.dumps({"error": "未获取到热搜数据"}, ensure_ascii=False)
    return json.dumps([
        {"rank": i, "title": it.get("title", ""), "score": it.get("score", ""), "word_type": it.get("word_type", "")}
        for i, it in enumerate(items, 1)
    ], ensure_ascii=False)


# ---- 2. 搜索笔记 (主: app/search_notes, 备: web_v2) ----
NOTE_TYPE_MAP = {"0": "不限", "1": "视频笔记", "2": "普通笔记"}

async def search_xhs_notes(keywords: str, page: int = 1, sort_type: str = "general", note_type: str = "0") -> str:
    # 主端点: app/search_notes (keyword, page*, sort_type, filter_note_type)
    app_params = {
        "keyword": keywords,
        "page": page,
        "sort_type": sort_type,
        "filter_note_type": NOTE_TYPE_MAP.get(note_type, "不限"),
    }
    data = await _tikhub_get("app/search_notes", app_params)
    if not data.get("_error"):
        inner = data.get("data", {})
        items_container = inner.get("data", inner)
        items = items_container.get("items", []) if isinstance(items_container, dict) else []
        if items:
            return _format_search_notes_app(items)

    # 备用: web_v2/fetch_search_notes (keywords, page, sort_type, note_type)
    web_params = {"keywords": keywords, "page": page, "sort_type": sort_type, "note_type": note_type}
    data = await _tikhub_get("web_v2/fetch_search_notes", web_params)
    if err := _err(data):
        return err
    inner = data.get("data", {})
    items = inner.get("data", {}).get("items", inner.get("items", []))
    if not items:
        return json.dumps({"error": "未搜索到相关笔记"}, ensure_ascii=False)
    return _format_search_notes_web(items)


def _format_search_notes_app(items: list) -> str:
    """解析 app/search_notes 格式: items[].note.{...}"""
    result = []
    for item in items:
        note = item.get("note") or item
        user = note.get("user", {})
        result.append({
            "note_id": note.get("note_id", note.get("id", "")),
            "title": note.get("title", note.get("display_title", "")),
            "desc": note.get("desc", ""),
            "type": note.get("type", ""),
            "liked_count": note.get("liked_count", ""),
            "user": user.get("nickname", user.get("nick_name", "")),
            "user_id": user.get("user_id", user.get("userid", "")),
        })
    return json.dumps(result, ensure_ascii=False)


def _format_search_notes_web(items: list) -> str:
    """解析 web_v2/fetch_search_notes 格式: items[].note_card.{...}"""
    result = []
    for item in items:
        nc = item.get("note_card") or item
        result.append({
            "note_id": item.get("id", nc.get("note_id", "")),
            "title": nc.get("display_title", nc.get("title", "")),
            "desc": nc.get("desc", ""),
            "type": nc.get("type", ""),
            "liked_count": nc.get("interact_info", {}).get("liked_count", ""),
            "user": nc.get("user", {}).get("nickname", ""),
            "user_id": nc.get("user", {}).get("user_id", ""),
        })
    return json.dumps(result, ensure_ascii=False)


# ---- 3. 笔记详情 (主: app_v2/get_mixed_note_detail, 备: web_v2) ----
async def fetch_xhs_note_detail(note_id: str) -> str:
    # 主端点: app_v2/get_mixed_note_detail
    data = await _tikhub_get("app_v2/get_mixed_note_detail", {"note_id": note_id})
    if not data.get("_error"):
        return _format_note_detail(data, note_id)

    # 备用端点
    for ep in ["web_v2/fetch_feed_notes_v2", "web_v2/fetch_feed_notes"]:
        data = await _tikhub_get(ep, {"note_id": note_id})
        if not data.get("_error"):
            inner = data.get("data", {})
            items = inner.get("data", {}).get("items", inner.get("items", []))
            if items and isinstance(items[0], dict):
                nc = items[0].get("note_card", items[0])
                return _format_note_card(nc, items[0], note_id)

    return json.dumps({"error": "未获取到笔记详情，TikHub 服务暂时不可用"}, ensure_ascii=False)


def _format_note_detail(data: dict, note_id: str) -> str:
    """解析 app_v2/get_mixed_note_detail 响应。"""
    inner = data.get("data", {})
    # app_v2 格式: data 直接是笔记对象
    note = inner if "title" in inner or "desc" in inner else inner.get("data", inner)
    nc = note.get("note_card", note)
    return _format_note_card(nc, note, note_id)


def _format_note_card(nc: dict, note: dict, note_id: str) -> str:
    interact = nc.get("interact_info", {})
    result = {
        "note_id": note.get("id", nc.get("note_id", note_id)),
        "title": nc.get("title", nc.get("display_title", "")),
        "desc": nc.get("desc", ""),
        "type": nc.get("type", ""),
        "liked_count": interact.get("liked_count", ""),
        "collected_count": interact.get("collected_count", ""),
        "comment_count": interact.get("comment_count", ""),
        "share_count": interact.get("share_count", ""),
        "user": nc.get("user", {}).get("nickname", ""),
        "user_id": nc.get("user", {}).get("user_id", ""),
        "time": nc.get("time", ""),
        "tag_list": [t.get("name", "") for t in nc.get("tag_list", [])],
    }
    images = nc.get("image_list", [])
    if images:
        result["images"] = [img.get("url_default", img.get("url", "")) for img in images[:5]]
    video = nc.get("video", {})
    if video:
        url = video.get("media", {}).get("stream", {}).get("h264", [{}])[0].get("master_url", "")
        if not url:
            url = video.get("url", "")
        if url:
            result["video_url"] = url
    return json.dumps(result, ensure_ascii=False)


# ---- 4. 用户信息 (主: web_v2/fetch_user_info_app, 备: app_v2) ----
async def fetch_xhs_user_info(user_id: str) -> str:
    for ep, params in [
        ("web_v2/fetch_user_info_app", {"user_id": user_id}),
        ("app_v2/get_user_info",       {"user_id": user_id}),
        ("web_v2/fetch_user_info",     {"user_id": user_id}),
    ]:
        data = await _tikhub_get(ep, params)
        if data.get("_error"):
            continue
        inner = data.get("data", {})
        user = inner.get("data", inner)
        if not user or ("nickname" not in user and "basic_info" not in user):
            continue
        basic = user.get("basic_info", user)
        interactions = user.get("interactions", [])
        imap = {it.get("name", ""): it.get("count", "") for it in interactions}
        return json.dumps({
            "user_id": user.get("user_id", user_id),
            "nickname": basic.get("nickname", user.get("nickname", "")),
            "desc": basic.get("desc", user.get("desc", "")),
            "gender": basic.get("gender", user.get("gender", "")),
            "ip_location": basic.get("ip_location", user.get("ip_location", "")),
            "follows": imap.get("关注", user.get("follows", "")),
            "fans": imap.get("粉丝", user.get("fans", "")),
            "liked_and_collected": imap.get("获赞与收藏", user.get("interaction", "")),
        }, ensure_ascii=False)

    return json.dumps({"error": "未获取到用户信息"}, ensure_ascii=False)


# ---- 5. 搜索用户 (主: app_v2/search_users, 备: web) ----
async def search_xhs_users(keywords: str, page: int = 1) -> str:
    for ep, params in [
        ("app_v2/search_users",       {"keyword": keywords, "page": page}),
        ("web/search_users",          {"keyword": keywords, "page": page}),
        ("web_v2/fetch_search_users", {"keywords": keywords, "page": page}),
    ]:
        data = await _tikhub_get(ep, params)
        if data.get("_error"):
            continue
        inner = data.get("data", {})
        users_container = inner.get("data", inner)
        users = users_container.get("users", []) if isinstance(users_container, dict) else []
        if not users:
            continue
        result = []
        for u in users:
            fans = u.get("fans", u.get("fansCount", ""))
            if not fans:
                sub = u.get("sub_title", "")
                if sub:
                    fans = sub
            result.append({
                "user_id": u.get("user_id", u.get("id", u.get("red_id", ""))),
                "nickname": u.get("nickname", u.get("name", "")),
                "desc": u.get("desc", ""),
                "fans": fans,
                "note_count": u.get("notes", u.get("noteCount", "")),
            })
        return json.dumps(result, ensure_ascii=False)

    return json.dumps({"error": "未搜索到相关用户"}, ensure_ascii=False)


# ---- 6. 用户笔记 (主: web_v2 app, 备: app, app_v2) ----
async def fetch_xhs_user_notes(user_id: str, cursor: str = "") -> str:
    for ep, p_fn in [
        ("web_v2/fetch_home_notes_app", lambda: {"user_id": user_id, **({"cursor": cursor} if cursor else {})}),
        ("app/get_user_notes",          lambda: {"user_id": user_id, **({"cursor": cursor} if cursor else {})}),
        ("app_v2/get_user_posted_notes", lambda: {"user_id": user_id, **({"cursor": cursor} if cursor else {})}),
        ("web_v2/fetch_home_notes",     lambda: {"user_id": user_id, **({"cursor": cursor} if cursor else {})}),
    ]:
        data = await _tikhub_get(ep, p_fn())
        if data.get("_error"):
            continue
        inner = data.get("data", {})
        notes_container = inner.get("data", inner)
        notes = notes_container.get("notes", []) if isinstance(notes_container, dict) else []
        if not notes:
            continue
        next_cursor = notes_container.get("cursor", inner.get("cursor", "")) if isinstance(notes_container, dict) else ""
        return json.dumps({
            "cursor": next_cursor,
            "notes": [{
                "note_id": n.get("note_id", ""),
                "title": n.get("display_title", n.get("title", "")),
                "type": n.get("type", ""),
                "liked_count": n.get("interact_info", {}).get("liked_count", n.get("liked_count", "")),
            } for n in notes],
        }, ensure_ascii=False)

    return json.dumps({"error": "未获取到用户笔记"}, ensure_ascii=False)


# ---- 7. 笔记评论 (主: web_v2, 备: app_v2, app, web) ----
async def fetch_xhs_note_comments(note_id: str, cursor: str = "") -> str:
    endpoints = [
        ("web_v2/fetch_note_comments", {"note_id": note_id, **({"cursor": cursor} if cursor else {})}),
        ("app_v2/get_note_comments",   {"note_id": note_id, **({"cursor": cursor} if cursor else {})}),
        ("app/get_note_comments",      {"note_id": note_id, **({"start": cursor} if cursor else {})}),
        ("web/get_note_comments",      {"note_id": note_id, **({"lastCursor": cursor} if cursor else {})}),
    ]
    for ep, params in endpoints:
        data = await _tikhub_get(ep, params)
        if data.get("_error"):
            continue
        inner = data.get("data", {})
        comments_container = inner.get("data", inner)
        comments = comments_container.get("comments", []) if isinstance(comments_container, dict) else []
        if not comments:
            continue
        next_cursor = comments_container.get("cursor", inner.get("cursor", "")) if isinstance(comments_container, dict) else ""
        return json.dumps({
            "cursor": next_cursor,
            "comments": [{
                "comment_id": c.get("id", ""),
                "content": c.get("content", ""),
                "user": c.get("user_info", {}).get("nickname", c.get("nickname", "")),
                "liked_count": c.get("like_count", c.get("liked_count", "")),
                "sub_comment_count": c.get("sub_comment_count", ""),
                "create_time": c.get("create_time", ""),
            } for c in comments],
        }, ensure_ascii=False)

    return json.dumps({"error": "未获取到评论数据"}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 工具注册表
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "fetch_xhs_hot_list": fetch_xhs_hot_list,
    "search_xhs_notes": search_xhs_notes,
    "fetch_xhs_note_detail": fetch_xhs_note_detail,
    "fetch_xhs_user_info": fetch_xhs_user_info,
    "search_xhs_users": search_xhs_users,
    "fetch_xhs_user_notes": fetch_xhs_user_notes,
    "fetch_xhs_note_comments": fetch_xhs_note_comments,
}
