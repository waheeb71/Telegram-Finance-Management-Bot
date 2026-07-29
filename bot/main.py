import os
import sys
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

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


from aiogram.types import BotCommand, BotCommandScopeDefault


async def health_handler(request):
    return web.Response(text="OK -  ابداع مهندس is active")


async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 القائمة الرئيسية والترحيب"),
        BotCommand(command="help", description="📖 دليل استخدام البوت والتعليمات"),
        BotCommand(command="admin", description="⚙️ لوحة الإدارة والتحكم"),
    ]
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        logger.info("Bot commands registered successfully with Telegram.")
    except Exception as e:
        logger.warning(f"Could not register bot commands: {e}")


async def on_startup(bot: Bot):
    await setup_bot_commands(bot)
    if settings.WEBHOOK_URL and settings.WEBHOOK_URL.strip():
        webhook_path = "/webhook"
        full_url = f"{settings.WEBHOOK_URL.rstrip('/')}{webhook_path}"
        await bot.set_webhook(url=full_url, drop_pending_updates=True)
        logger.info(f"Webhook set successfully to: {full_url}")


async def main():
    logger.info("Initializing  ابداع مهندس...")

    # 1. Initialize Database Tables inside the current main event loop
    try:
        await init_models()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        sys.exit(1)

    # 2. Setup Bot & Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = get_fsm_storage()
    dp = Dispatcher(storage=storage)

    # 3. Register Auth & RBAC Middleware
    dp.message.outer_middleware(AuthMiddleware())
    dp.callback_query.outer_middleware(AuthMiddleware())

    # 4. Include Handler Routers
    dp.include_router(common_router)
    dp.include_router(finance_router)
    dp.include_router(students_router)
    dp.include_router(sponsors_router)
    dp.include_router(reports_router)
    dp.include_router(exports_router)
    dp.include_router(super_admin_router)

    port = int(os.getenv("PORT", 8000))

    # 5. Check Webhook mode vs Long Polling mode
    if settings.WEBHOOK_URL and settings.WEBHOOK_URL.strip():
        logger.info("Configuring Webhook mode with aiohttp web server...")
        dp.startup.register(on_startup)

        app = web.Application()
        app.router.add_get("/", health_handler)
        app.router.add_get("/health", health_handler)

        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot
        )
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Webhook HTTP server started on 0.0.0.0:{port}")

        await asyncio.Event().wait()
    else:
        # Long Polling Mode
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Deleted old webhook. Starting Long Polling mode...")
            
            app = web.Application()
            app.router.add_get("/", health_handler)
            app.router.add_get("/health", health_handler)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()

            await setup_bot_commands(bot)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
