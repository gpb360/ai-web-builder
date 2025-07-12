from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
from config import settings, DATABASE_URL
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    poolclass=NullPool if settings.environment == "testing" else None,
    pool_pre_ping=True,
    pool_recycle=300,
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Redis setup
redis_client = None

async def get_redis():
    """Get Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return redis_client

async def get_db():
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database with all tables"""
    async with engine.begin() as conn:
        # Import all models to register them
        from database import models
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

async def close_db():
    """Close database connections"""
    await engine.dispose()
    if redis_client:
        await redis_client.aclose()
    logger.info("Database connections closed")