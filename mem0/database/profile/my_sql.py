import ssl
from typing import Optional, Union

from sqlmodel import select, col, asc
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from mem0.database.history.base import HistoryDBBase
from mem0.database.profile.po import UserProfile


class Mysql(HistoryDBBase):
    def __init__(
        self,
        url: Optional[str] = None,
        host: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        port: Optional[int] = 3306,
        pool_size: Optional[int] = 100,
        max_overflow: Optional[int] = 50,
        pool_recycle: Optional[int] = 240,
    ):
        super().__init__()
        if url:
            config = {
                "url": url,
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_recycle": pool_recycle,
                "ssl": ssl.create_default_context()
            }
        else:
            config = {
                "user": user,
                "password": password,
                "host": host,
                "database": database,
                "port": port,
                "raise_on_warnings": True,
            }

        self.async_engine = create_async_engine(**config)

    async def get_profile(self, profile_id: int):
        async with AsyncSession(self.async_engine) as session:
            statement = select(UserProfile).where(UserProfile.user_id == profile_id)
            return (await session.exec(statement)).first()
    
    async def insert_profile(self, profile_id: int, profile):
        profile_po = UserProfile(user_id=profile_id)
        profile_po.profile = profile.dump_json(exclude_none=True)

        async with AsyncSession(self.async_engine) as session:
            session.add(profile_po)
            await session.commit()
            await session.refresh(profile_po)
            return profile_po

    async def update_profile(self, profile_id: int, profile):
        async with AsyncSession(self.async_engine) as session:
            statement = select(UserProfile).where(
                UserProfile.user_id == profile_id
            )
            profile_po = (await session.exec(statement)).first()
            profile_po.profile = profile.dump_json(exclude_none=True)
            session.add(profile_po)
            await session.commit()
