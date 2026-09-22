from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import event
from app.core.config import settings

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

if _is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if _is_sqlite:
            def _migrate_columns(sync_conn):
                try:
                    res = sync_conn.exec_driver_sql("PRAGMA table_info(organizations)")
                    cols = [row[1] for row in res.fetchall()]
                    if "public_id" not in cols:
                        sync_conn.exec_driver_sql("ALTER TABLE organizations ADD COLUMN public_id TEXT")
                    if "ingestion_secret_hash" not in cols:
                        sync_conn.exec_driver_sql("ALTER TABLE organizations ADD COLUMN ingestion_secret_hash TEXT")

                    mres = sync_conn.exec_driver_sql("PRAGMA table_info(missions)")
                    mcols = [row[1] for row in mres.fetchall()]
                    if "org_id" not in mcols:
                        sync_conn.exec_driver_sql("ALTER TABLE missions ADD COLUMN org_id TEXT")
                except Exception as e:
                    print(f"[init_db] migration note: {e}")
            await conn.run_sync(_migrate_columns)
