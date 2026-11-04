import os
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import AsyncAdaptedQueuePool

DATABASE_URL = "sqlite+aiosqlite:///./sirens.db"

# create_async_engine translates pool arguments to the underlying pool class
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"timeout": 15},
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,
    max_overflow=40
)

# For aiosqlite, we must listen to the underlying sync engine's connect event
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.close()

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    attributes = Column(String)
    response = Column(String)
    sales_framework = Column(String, default="Unknown")
    is_lead = Column(Boolean, default=False)
    follow_up_notes = Column(String, default="")
    tts_latency_ms = Column(Integer, default=0)
    feedback_score = Column(Integer, default=0)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
