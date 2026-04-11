from datetime import datetime

from sqlalchemy import BigInteger, delete as sqlalchemy_delete, DateTime, update as sqlalchemy_update, func, select, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncAttrs
from sqlalchemy.orm import declared_attr, sessionmaker, DeclarativeBase, Mapped, mapped_column, selectinload

from config import conf


class Base(AsyncAttrs, DeclarativeBase):

    @declared_attr
    def __tablename__(self) -> str:
        __name = self.__name__[:1]
        for i in self.__name__[1:]:
            if i.isupper():
                __name += '_'
            __name += i
        __name = __name.lower()

        if __name.endswith('y'):
            __name = __name[:-1] + 'ie'
        return __name + 's'


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    def init(self):
        self._engine = create_async_engine(conf.db.db_url)
        self._session = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)()

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self._ensure_compat_columns(conn)

    async def _ensure_compat_columns(self, conn) -> None:
        """Add missing columns for already existing tables without migrations."""
        def _missing_columns(sync_conn) -> list[tuple[str, str, str]]:
            inspector = inspect(sync_conn)
            existing: dict[str, set[str]] = {}
            for table_name in inspector.get_table_names():
                existing[table_name] = {column["name"] for column in inspector.get_columns(table_name)}

            required = [
                ("bot_users", "locale", "VARCHAR(8)"),
                ("vacancies", "title_ru", "VARCHAR(255)"),
                ("vacancies", "title_uz", "VARCHAR(255)"),
                ("vacancies", "description_ru", "TEXT"),
                ("vacancies", "description_uz", "TEXT"),
            ]
            missing: list[tuple[str, str, str]] = []
            for table_name, column_name, ddl_type in required:
                if table_name not in existing:
                    continue
                if column_name not in existing[table_name]:
                    missing.append((table_name, column_name, ddl_type))
            return missing

        for table_name, column_name, ddl_type in await conn.run_sync(_missing_columns):
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"))

    # async def drop_all(self):
    #     async with self._engine.begin() as conn:
    #         await conn.run_sync(Base.metadata.drop_all)


db = AsyncDatabaseSession()
db.init()


# ----------------------------- ABSTRACTS ----------------------------------
class AbstractClass:
    @staticmethod
    async def commit():
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def create(cls, **kwargs):
        obj = cls(**kwargs)
        db.add(obj)
        await cls.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def update(cls, id_, **kwargs):
        query = (
            sqlalchemy_update(cls)
            .where(cls.id == id_)
            .values(**kwargs)
            .returning(cls)
        )
        result = await db.execute(query)
        await cls.commit()
        return result.scalar_one_or_none()

    @classmethod
    async def get_or_none(cls, _id: int, *, relationship=None):
        query = select(cls).where(cls.id == _id)

        if relationship is not None:
            # relationship может быть одним relationship или списком
            if isinstance(relationship, (list, tuple)):
                query = query.options(*(selectinload(r) for r in relationship))
            else:
                query = query.options(selectinload(relationship))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get(cls, _id, *, relationship=None):
        query = select(cls).where(cls.id == _id)
        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalar()

    @classmethod
    async def count(cls):
        query = select(func.count()).select_from(cls)
        return (await db.execute(query)).scalar()

    @classmethod
    async def delete(cls, id_):
        query = sqlalchemy_delete(cls).where(cls.id == id_)
        await db.execute(query)
        await cls.commit()

    @classmethod
    async def filters(cls, criteria, *, relationship=None, columns=None):
        if columns:
            query = select(*columns)
        else:
            query = select(cls)

        query = query.where(criteria)

        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalars()

    @classmethod
    async def filter(cls, criteria, *, relationship=None, columns=None):
        if columns:
            query = select(*columns)
        else:
            query = select(cls)

        query = query.where(criteria)

        if relationship:
            query = query.options(selectinload(relationship))
        return (await db.execute(query)).scalar()

    @classmethod
    async def all(cls):
        return (await db.execute(select(cls))).scalars().all()


# def run_async(self, func, *args, **kwargs):
#     return asyncio.run(func(*args, **kwargs))

# def convert_uzs(self, amount: int):
#     return amount * current_price
#
# def convert_usd(self, amount: int):
#     return amount // current_price


class BaseModel(Base, AbstractClass):
    __abstract__ = True
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    def __str__(self):
        return f"{self.id}"


class CreatedBaseModel(BaseModel):
    __abstract__ = True
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())