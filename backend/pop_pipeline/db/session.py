"""
db/session.py — async SQLAlchemy session factory.
"""
import os
import ssl
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.example")

# Strip sslmode param — asyncpg uses connect_args ssl instead
_raw_url = os.getenv("DATABASE_URL", "")
DATABASE_URL = _raw_url.replace("?sslmode=require", "").replace("?ssl=true", "")

_ssl_ctx = ssl.create_default_context()

print(f"DATABASE_URL: '{DATABASE_URL}'")
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"ssl": _ssl_ctx},
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
