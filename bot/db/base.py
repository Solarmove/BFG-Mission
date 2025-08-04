import logging

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from configreader import config

engine = create_async_engine(str(config.db_config.postgres_dsn))
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


logger = logging.get_logger(__name__)


class Base(DeclarativeBase):
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            # if col in self.repr_cols or idx < self.repr_cols_num:
            cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


@event.listens_for(engine.sync_engine, "connect")
def set_timezone(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET TIME ZONE 'Europe/Kyiv'")
    except Exception:
        cursor.execute("SET TIME ZONE 'Europe/Kiev'")
    logger.info(
        "🟢 New physical DB connection established; timezone set to Europe/Kyiv"
    )
    cursor.close()


@event.listens_for(engine.sync_engine, "checkout")
def on_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("🔁 Connection checked out from pool")


async def get_async_session():
    async with async_session_maker() as session:
        yield session


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
