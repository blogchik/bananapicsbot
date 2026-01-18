"""
Banana Pics Bot - Entry Point

Professional Telegram bot for image generation.
Supports both polling and webhook modes.
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from core.config import get_settings
from core.logging import setup_logging, get_logger
from core.container import Container, get_container
from infrastructure.storage import create_fsm_storage
from handlers import setup_handlers
from middlewares import (
    LoggingMiddleware,
    ErrorHandlerMiddleware,
    I18nMiddleware,
    ThrottlingMiddleware,
    UserContextMiddleware,
)
from locales import TranslationKey, get_translator, LocaleManager


logger = get_logger(__name__)


async def setup_middlewares(dp: Dispatcher) -> None:
    """Register all middlewares."""
    settings = get_settings()
    
    # Order matters: outer middlewares run first
    dp.message.outer_middleware(LoggingMiddleware())
    dp.callback_query.outer_middleware(LoggingMiddleware())
    
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())
    
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    
    # Throttling middleware
    dp.message.middleware(ThrottlingMiddleware(
        message_limit=settings.rate_limit_messages,
        callback_limit=settings.rate_limit_callbacks,
        window_seconds=settings.rate_limit_period,
    ))
    dp.callback_query.middleware(ThrottlingMiddleware(
        message_limit=settings.rate_limit_messages,
        callback_limit=settings.rate_limit_callbacks,
        window_seconds=settings.rate_limit_period,
    ))
    
    # User context injection
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())


async def on_startup(bot: Bot) -> None:
    """Startup callback."""
    settings = get_settings()

    manager = LocaleManager.get_instance()
    for lang_code in manager.available_languages:
        _ = get_translator(lang_code)
        commands = [
            BotCommand(command="start", description=_(TranslationKey.CMD_HOME, None)),
            BotCommand(command="profile", description=_(TranslationKey.CMD_PROFILE, None)),
            BotCommand(command="topup", description=_(TranslationKey.CMD_TOPUP, None)),
            BotCommand(command="referral", description=_(TranslationKey.CMD_REFERRAL, None)),
        ]
        await bot.set_my_commands(
            commands, language_code=lang_code, scope=BotCommandScopeDefault()
        )
        await bot.set_my_commands(
            commands, language_code=lang_code, scope=BotCommandScopeAllPrivateChats()
        )
    default_lang = settings.default_language or "uz"
    if default_lang in manager.available_languages:
        _ = get_translator(default_lang)
        commands = [
            BotCommand(command="start", description=_(TranslationKey.CMD_HOME, None)),
            BotCommand(command="profile", description=_(TranslationKey.CMD_PROFILE, None)),
            BotCommand(command="topup", description=_(TranslationKey.CMD_TOPUP, None)),
            BotCommand(command="referral", description=_(TranslationKey.CMD_REFERRAL, None)),
        ]
        await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    
    if settings.use_webhook:
        webhook_url = f"{settings.webhook_base_url}{settings.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret,
            drop_pending_updates=True,
        )
        logger.info("Webhook set", url=webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, using polling")
    
    me = await bot.get_me()
    logger.info("Bot started", username=me.username, id=me.id)


async def on_shutdown(bot: Bot) -> None:
    """Shutdown callback."""
    logger.info("Bot shutting down...")
    
    # Close container resources
    from core.container import get_container
    container = get_container()
    await container.close()
    
    logger.info("Bot stopped")


@asynccontextmanager
async def lifespan(app: web.Application) -> AsyncIterator[None]:
    """Aiohttp application lifespan."""
    yield


async def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Create and configure bot and dispatcher."""
    settings = get_settings()
    
    # Create bot with default properties
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=False,
        ),
    )
    
    # Create FSM storage
    storage = await create_fsm_storage(settings)
    
    # Create dispatcher
    dp = Dispatcher(storage=storage)
    
    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Initialize container with singleton pattern
    container = Container.get_instance()
    container.set_bot(bot)
    container.set_dispatcher(dp)
    container.set_storage(storage)
    
    # Setup middlewares
    await setup_middlewares(dp)
    
    # Setup handlers
    main_router = setup_handlers()
    dp.include_router(main_router)
    
    return bot, dp


async def run_polling() -> None:
    """Run bot in polling mode."""
    bot, dp = await create_bot_and_dispatcher()
    
    try:
        logger.info("Starting polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


async def run_webhook() -> None:
    """Run bot in webhook mode with aiohttp."""
    settings = get_settings()
    bot, dp = await create_bot_and_dispatcher()
    
    # Create aiohttp app
    app = web.Application()
    
    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    )
    webhook_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    
    # Run server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(
        runner,
        host=settings.webhook_host,
        port=settings.webhook_port,
    )
    
    try:
        logger.info(
            "Starting webhook server",
            host=settings.webhook_host,
            port=settings.webhook_port,
        )
        await site.start()
        
        # Keep running
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()


def main() -> None:
    """Main entry point."""
    # Setup logging first
    setup_logging()
    
    settings = get_settings()
    
    try:
        if settings.use_webhook:
            asyncio.run(run_webhook())
        else:
            asyncio.run(run_polling())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
