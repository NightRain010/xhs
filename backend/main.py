import os
import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import init_db, get_db, async_session
from models import Conversation, Message, EmailSchedule
from agent import chat_with_agent_stream
from scheduler import (
    start_scheduler, shutdown_scheduler, load_all_jobs,
    add_email_job, remove_email_job,
)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    await load_all_jobs()
    yield
    shutdown_scheduler()


app = FastAPI(title="小红书热点 Agent", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500)  # 流量节省：>500B 启用 gzip
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"

# ---------- Schemas ----------

class ChatRequest(BaseModel):
    conversation_id: int | None = None
    message: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tool_name: str | None = None

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    messages: list[MessageOut] = []

    class Config:
        from_attributes = True


# ---------- Routes ----------

@app.post("/api/chat")
async def chat(req: ChatRequest):
    async def event_stream():
        async with async_session() as db:
            try:
                if req.conversation_id:
                    conv = await db.get(Conversation, req.conversation_id)
                    if not conv:
                        conv = Conversation(title=req.message[:30])
                        db.add(conv)
                        await db.flush()
                else:
                    conv = Conversation(title=req.message[:30])
                    db.add(conv)
                    await db.flush()

                user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
                db.add(user_msg)
                await db.flush()

                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                    .order_by(Message.created_at)
                )
                history_msgs = result.scalars().all()

                openai_messages = []
                for m in history_msgs:
                    if m.role in ("user", "assistant"):
                        openai_messages.append({"role": m.role, "content": m.content})

                yield sse_event({"event": "start", "conversation_id": conv.id})

                full_reply = ""
                async for chunk in chat_with_agent_stream(openai_messages):
                    if chunk["event"] == "delta":
                        full_reply += chunk["content"]
                        yield sse_event(chunk)
                    elif chunk["event"] == "tool_call":
                        yield sse_event(chunk)
                    elif chunk["event"] == "done":
                        yield sse_event(chunk)

                assistant_msg = Message(
                    conversation_id=conv.id, role="assistant", content=full_reply
                )
                db.add(assistant_msg)
                await db.commit()

            except Exception as e:
                yield sse_event({"event": "error", "message": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/api/conversations", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


@app.get("/api/conversations/{conv_id}", response_model=ConversationOut)
async def get_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conv


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: AsyncSession = Depends(get_db)):
    conv = await db.get(Conversation, conv_id)
    if conv:
        await db.delete(conv)
        await db.commit()
    return {"ok": True}


# ---------- Email Schedule Schemas ----------

class EmailScheduleCreate(BaseModel):
    recipient_email: EmailStr
    email_subject: str = "小红书热点日报 - {date}"
    prompt: str = "获取小红书今日热搜榜单，并做简要分析"
    cron_hour: int = 9
    cron_minute: int = 0
    cron_day_of_week: str = "*"


class EmailScheduleUpdate(BaseModel):
    recipient_email: EmailStr | None = None
    email_subject: str | None = None
    prompt: str | None = None
    cron_hour: int | None = None
    cron_minute: int | None = None
    cron_day_of_week: str | None = None
    enabled: bool | None = None


class EmailScheduleOut(BaseModel):
    id: int
    recipient_email: str
    email_subject: str
    prompt: str
    cron_hour: int
    cron_minute: int
    cron_day_of_week: str
    enabled: bool
    last_sent_at: str | None = None
    last_send_status: str | None = None

    class Config:
        from_attributes = True


# ---------- Email Schedule Routes ----------

@app.post("/api/email-schedules", response_model=EmailScheduleOut)
async def create_email_schedule(
    req: EmailScheduleCreate, db: AsyncSession = Depends(get_db)
):
    sched = EmailSchedule(
        recipient_email=req.recipient_email,
        email_subject=req.email_subject,
        prompt=req.prompt,
        cron_hour=req.cron_hour,
        cron_minute=req.cron_minute,
        cron_day_of_week=req.cron_day_of_week,
    )
    db.add(sched)
    await db.commit()
    await db.refresh(sched)
    add_email_job(sched)
    return sched


@app.get("/api/email-schedules", response_model=list[EmailScheduleOut])
async def list_email_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailSchedule).order_by(EmailSchedule.created_at.desc())
    )
    return result.scalars().all()


@app.put("/api/email-schedules/{sched_id}", response_model=EmailScheduleOut)
async def update_email_schedule(
    sched_id: int, req: EmailScheduleUpdate, db: AsyncSession = Depends(get_db)
):
    sched = await db.get(EmailSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    update_data = req.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(sched, k, v)
    await db.commit()
    await db.refresh(sched)

    if sched.enabled:
        add_email_job(sched)
    else:
        remove_email_job(sched.id)
    return sched


@app.delete("/api/email-schedules/{sched_id}")
async def delete_email_schedule(
    sched_id: int, db: AsyncSession = Depends(get_db)
):
    sched = await db.get(EmailSchedule, sched_id)
    if sched:
        remove_email_job(sched.id)
        await db.delete(sched)
        await db.commit()
    return {"ok": True}


@app.post("/api/email-schedules/{sched_id}/test")
async def test_email_schedule(
    sched_id: int, db: AsyncSession = Depends(get_db)
):
    """手动触发一次定时任务，用于测试邮件是否正常发送。"""
    sched = await db.get(EmailSchedule, sched_id)
    if not sched:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    from scheduler import _run_agent_and_send
    await _run_agent_and_send(sched.id)
    return {"ok": True, "message": f"已发送测试邮件至 {sched.recipient_email}"}


# 生产环境：托管前端静态文件（前后端同域，节省流量）
# 必须放在所有 API 路由之后，作为兜底
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """SPA 回退：非 API 请求返回 index.html"""
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
