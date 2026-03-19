import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from database import async_session
from models import EmailSchedule
from agent import chat_with_agent_stream
from email_service import send_email, markdown_to_html

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

JOB_PREFIX = "email_schedule_"


async def _run_agent_and_send(schedule_id: int) -> None:
    """执行一次 Agent 查询并将结果邮件发送给收件人。"""
    async with async_session() as db:
        sched = await db.get(EmailSchedule, schedule_id)
        if not sched or not sched.enabled:
            return

        logger.info("开始执行定时任务 #%d -> %s", schedule_id, sched.recipient_email)

        messages = [{"role": "user", "content": sched.prompt}]
        full_reply = ""
        async for chunk in chat_with_agent_stream(messages):
            if chunk["event"] == "delta":
                full_reply += chunk["content"]

        if not full_reply:
            logger.warning("Agent 未返回内容，跳过发送")
            sched.last_sent_at = datetime.now(timezone.utc)
            sched.last_send_status = "empty"
            await db.commit()
            return

        subject_tpl = sched.email_subject or "小红书热点日报 - {date}"
        subject = subject_tpl.replace("{date}", datetime.now().strftime("%Y-%m-%d"))
        html = markdown_to_html(full_reply)
        ok = await send_email(sched.recipient_email, subject, html)

        sched.last_sent_at = datetime.now(timezone.utc)
        sched.last_send_status = "success" if ok else "failed"
        await db.commit()
        logger.info("定时任务 #%d 完成，状态: %s", schedule_id, sched.last_send_status)


def _job_id(schedule_id: int) -> str:
    return f"{JOB_PREFIX}{schedule_id}"


def add_email_job(sched: EmailSchedule) -> None:
    """根据 EmailSchedule 记录添加/替换一个 cron 任务。"""
    job_id = _job_id(sched.id)
    dow = sched.cron_day_of_week if sched.cron_day_of_week else "*"
    trigger = CronTrigger(
        day_of_week=dow,
        hour=sched.cron_hour,
        minute=sched.cron_minute,
    )

    if scheduler.get_job(job_id):
        scheduler.reschedule_job(job_id, trigger=trigger)
    else:
        scheduler.add_job(
            _run_agent_and_send,
            trigger=trigger,
            args=[sched.id],
            id=job_id,
            replace_existing=True,
        )
    logger.info(
        "已注册定时任务 %s (星期 %s %02d:%02d)",
        job_id, dow, sched.cron_hour, sched.cron_minute,
    )


def remove_email_job(schedule_id: int) -> None:
    """移除定时任务。"""
    job_id = _job_id(schedule_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("已移除定时任务 %s", job_id)


async def load_all_jobs() -> None:
    """启动时从数据库加载所有已启用的定时任务。"""
    async with async_session() as db:
        result = await db.execute(
            select(EmailSchedule).where(EmailSchedule.enabled == True)  # noqa: E712
        )
        schedules = result.scalars().all()
        for s in schedules:
            add_email_job(s)
        logger.info("已加载 %d 个邮件定时任务", len(schedules))


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler 已启动")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已停止")
