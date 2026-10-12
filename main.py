from tortoise import Tortoise
from settings import TORTOISE_ORM
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import ClientSession
from requester import post_request
from tasks.sessions import compare_active_sessions, SessionManager
import asyncio

from tasks.town_updates import RelationshipManager, check_relationships


async def initialize():
    await Tortoise.init(TORTOISE_ORM)
    session = ClientSession()
    scheduler = AsyncIOScheduler()
    session_manager = SessionManager()
    relationship_manager = RelationshipManager()

    scheduler.add_job(compare_active_sessions, "interval", seconds=5, args=[session, session_manager, relationship_manager])
    scheduler.add_job(check_relationships, "interval", seconds=7, args=[session, relationship_manager.queue])

    scheduler.start()

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await session.close()

asyncio.run(initialize())