---
name: backend-db
description: >-
  异步数据库配置模块，包含 SQLAlchemy 引擎、会话工厂和建表逻辑。
  当需要修改数据库连接、切换数据库类型、调整会话管理或理解数据库初始化时使用。
---

# 后端 Database 模块

文件：`backend/database.py`

## 配置

| 配置项 | 值 |
|--------|-----|
| 数据库 | SQLite |
| 连接字符串 | `sqlite+aiosqlite:///./xhs_agent.db` |
| 异步驱动 | aiosqlite |
| 引擎 | `create_async_engine(echo=False)` |
| 会话工厂 | `async_sessionmaker(expire_on_commit=False)` |

## 核心组件

### Base

```python
class Base(DeclarativeBase):
    pass
```

所有 ORM 模型的基类，`models.py` 从此导入。

### init_db()

```python
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

在 FastAPI `lifespan` 中调用，自动创建所有表（若不存在）。

### get_db()

```python
async def get_db():
    async with async_session() as session:
        yield session
```

FastAPI 依赖注入生成器，每个请求获取独立的异步会话。

## 数据库文件

- 路径：`backend/xhs_agent.db`（运行时自动创建）
- 清空数据：删除此文件，重启后自动重建

## 切换数据库指南

若需切换到 MySQL/PostgreSQL：
1. 修改 `DATABASE_URL`（如 `mysql+aiomysql://...`）
2. 更新 `requirements.txt` 添加对应异步驱动
3. 注意 SQLite 特有语法在其他数据库中可能不兼容

## 相关模块

- ORM 模型 → [backend-models](../backend-models/SKILL.md)
- API 路由（依赖注入使用者） → [backend-api](../backend-api/SKILL.md)
