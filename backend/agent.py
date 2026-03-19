import os
import json
from typing import AsyncGenerator
from openai import AsyncOpenAI
from tools import XHS_TOOLS, TOOL_FUNCTIONS

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

SYSTEM_PROMPT = """你是一个智能助手，专门帮助用户了解小红书平台的热门内容和趋势。

你拥有以下能力：
1. 查询小红书实时热搜榜单
2. 按关键词搜索笔记（支持按综合/最新/最热排序，筛选图文或视频）
3. 查看某条笔记的详细内容（标题、正文、互动数据、图片/视频等）
4. 查询某个用户的个人资料（昵称、简介、粉丝数等）
5. 按关键词搜索用户/博主
6. 查看某个用户发布的笔记列表
7. 查看某条笔记下的评论

当用户提出需求时，请主动选择合适的工具获取最新数据，然后以友好、有条理的方式呈现给用户。
回答时请注意：
1. 用简洁清晰的格式展示内容
2. 如果有互动数据（点赞、收藏、评论数），一并展示
3. 可以对数据做简短的分析或总结
4. 如果需要多步操作（如先搜索再查看详情），可以连续调用多个工具
"""


async def chat_with_agent_stream(messages: list[dict]) -> AsyncGenerator[dict, None]:
    """
    与 DeepSeek Agent 流式对话，支持 function calling。
    yield SSE 事件字典: {"event": "delta"/"tool_call"/"done", ...}
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    while True:
        stream = await client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            tools=XHS_TOOLS,
            tool_choice="auto",
            stream=True,
        )

        collected_content = ""
        collected_tool_calls = {}

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if delta.content:
                collected_content += delta.content
                yield {"event": "delta", "content": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in collected_tool_calls:
                        collected_tool_calls[idx] = {
                            "id": tc.id or "",
                            "name": (tc.function.name or "") if tc.function else "",
                            "arguments": (tc.function.arguments or "") if tc.function else "",
                        }
                    else:
                        if tc.id:
                            collected_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                collected_tool_calls[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                collected_tool_calls[idx]["arguments"] += tc.function.arguments

        if not collected_tool_calls:
            break

        tool_calls_list = []
        for idx in sorted(collected_tool_calls.keys()):
            tc = collected_tool_calls[idx]
            tool_calls_list.append({
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            })

        full_messages.append({
            "role": "assistant",
            "content": collected_content or None,
            "tool_calls": tool_calls_list,
        })

        for tc in tool_calls_list:
            fn_name = tc["function"]["name"]
            fn = TOOL_FUNCTIONS.get(fn_name)

            yield {"event": "tool_call", "name": fn_name}

            if fn:
                args = json.loads(tc["function"]["arguments"] or "{}")
                result = await fn(**args)
            else:
                result = json.dumps({"error": f"未知工具: {fn_name}"}, ensure_ascii=False)

            full_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    yield {"event": "done"}
