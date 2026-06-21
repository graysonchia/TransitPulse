import os
from collections.abc import AsyncGenerator
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

required_variables = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
missing_variables = [name for name in required_variables if not os.getenv(name)]
if missing_variables:
    raise RuntimeError(
        f"Missing required database environment variables: {', '.join(missing_variables)}"
    )

db_user = quote_plus(os.environ["DB_USER"])
db_password = quote_plus(os.environ["DB_PASSWORD"])
database_url = (
    f"postgresql+asyncpg://{db_user}:{db_password}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

engine = create_async_engine(database_url, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
