from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create sync engine for migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create sync session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)

# Create declarative base
Base = declarative_base()


async def init_db():
    """Initialize database"""
    try:
        async with async_engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import user, client, product, order, conversation, message
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() 