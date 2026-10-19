import os

from tortoise import Tortoise
from settings import TORTOISE_ORM
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import ClientSession
from tasks.sessions import compare_active_sessions, SessionManager
import asyncio
from sse.sse import setup_sse
from tasks.relationships import RelationshipManager, recency_checks
from loguru import logger


async def initialize():
    logger.add("main.log", format="{time} {level} {message}", rotation="10 MB")
    logger.info(f"Connecting to database with URL: {os.getenv('DATABASE_URL')}")
    await Tortoise.init(TORTOISE_ORM)
    session = ClientSession()
    scheduler = AsyncIOScheduler()
    session_manager = SessionManager()
    relationship_manager = RelationshipManager()

    logger.info("Adding jobs to scheduler")
    scheduler.add_job(compare_active_sessions, "interval", seconds=10, args=[session, session_manager, relationship_manager])
    scheduler.add_job(recency_checks, "interval", seconds=15, args=[session, relationship_manager])

    logger.info("Starting scheduler")
    scheduler.start()

    try:
        logger.info("Starting SSE")
        await setup_sse(session)
    finally:
        logger.info("Shutting down scheduler")
        scheduler.shutdown()
        await session.close()

asyncio.run(initialize())