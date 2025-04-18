from contextlib import asynccontextmanager
import asyncpg
from app.config import get_settings

settings = get_settings()

async def get_connection():
    """Get a database connection from the pool."""
    return await asyncpg.connect(settings.DATABASE_URL)

@asynccontextmanager
async def get_db():
    """Async context manager for database connections."""
    conn = await get_connection()
    try:
        yield conn
    finally:
        await conn.close()

async def init_db():
    """Initialize database connection and verify it's working."""
    try:
        async with get_db() as conn:
            version = await conn.fetchval('SELECT version()')
            print(f"Connected to database: {version}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise 