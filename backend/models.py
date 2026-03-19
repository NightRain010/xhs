import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / tool
    content: Mapped[str] = mapped_column(Text, default="")
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class EmailSchedule(Base):
    __tablename__ = "email_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_email: Mapped[str] = mapped_column(String(200))
    email_subject: Mapped[str] = mapped_column(
        String(300), default="小红书热点日报 - {date}"
    )
    prompt: Mapped[str] = mapped_column(Text, default="获取小红书今日热搜榜单，并做简要分析")
    cron_hour: Mapped[int] = mapped_column(default=9)
    cron_minute: Mapped[int] = mapped_column(default=0)
    cron_day_of_week: Mapped[str] = mapped_column(String(50), default="*")
    enabled: Mapped[bool] = mapped_column(default=True)
    last_sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    last_send_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
