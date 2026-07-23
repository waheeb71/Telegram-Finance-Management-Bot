import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.core.logger import logger
from bot.core.redis import get_fsm_storage
from bot.db.base import init_models
from bot.middlewares.auth import AuthMiddleware

from bot.handlers.common import common_router
from bot.handlers.finance import finance_router
from bot.handlers.students import students_router
from bot.handlers.sponsors import sponsors_router
from bot.handlers.reports import reports_router
from bot.handlers.exports import exports_router
from bot.handlers.super_admin import super_admin_router


import os
from aiohttp import web


async def health_handler(request):
    return web.Response(text="OK - Yemen Cyber Finance Bot is active")


async def start_health_server():
    try:
        port = int(os.getenv("PORT", 8000))
        app = web.Application()
        app.router.add_get("/", health_handler)
        app.router.add_get("/health", health_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Health check HTTP server listening on 0.0.0.0:{port}")
    except Exception as e:
        logger.warning(f"Could not start health check server: {e}")


async def main():
    logger.info("Initializing Yemen Cyber Finance Bot...")

    # 1. Initialize Database Tables
    try:
        await init_models()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        sys.exit(1)

    # 2. Start Health Check Server for Web Services (Render / Railway)
    await start_health_server()

    # 3. Setup Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = get_fsm_storage()
    dp = Dispatcher(storage=storage)

    # 4. Register Auth & RBAC Middleware
    dp.message.outer_middleware(AuthMiddleware())
    dp.callback_query.outer_middleware(AuthMiddleware())

    # 5. Include Handler Routers
    dp.include_router(common_router)
    dp.include_router(finance_router)
    dp.include_router(students_router)
    dp.include_router(sponsors_router)
    dp.include_router(reports_router)
    dp.include_router(exports_router)
    dp.include_router(super_admin_router)

    # 6. Clear old webhook & start Long Polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Deleted old webhook successfully.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
