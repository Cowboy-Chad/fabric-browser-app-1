import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    async_url = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)
else:
    async_url = DATABASE_URL

engine = create_async_engine(async_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    from models import AnalysisResult, RumbleTranscript, YouTubeTranscript
    os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "", 1)) or ".", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if DATABASE_URL.startswith("sqlite"):
            from sqlalchemy import text
            result = await conn.execute(text("PRAGMA table_info(analysis_results)"))
            cols = {row[1] for row in result.fetchall()}
            if col_missing := {"progress"}.difference(cols):
                for col in col_missing:
                    await conn.execute(text(f"ALTER TABLE analysis_results ADD COLUMN {col} TEXT"))


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session