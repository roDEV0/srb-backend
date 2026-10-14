import os

from tortoise import Tortoise
from settings import TORTOISE_ORM
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import ClientSession
from tasks.sessions import compare_active_sessions, SessionManager
import asyncio
from sse.sse import setup_sse
from tasks.relationships import RelationshipManager, recency_checks


async def initialize():
    print(os.getenv("DATABASE_URL"))
    await Tortoise.init(TORTOISE_ORM)
    session = ClientSession()
    scheduler = AsyncIOScheduler()
    session_manager = SessionManager()
    relationship_manager = RelationshipManager()

    scheduler.add_job(compare_active_sessions, "interval", seconds=10, args=[session, session_manager, relationship_manager])
    scheduler.add_job(recency_checks, "interval", seconds=15, args=[session, relationship_manager])

    scheduler.start()

    try:
        await setup_sse(session)
    finally:
        scheduler.shutdown()
        await session.close()

asyncio.run(initialize())