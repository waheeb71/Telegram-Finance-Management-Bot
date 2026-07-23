from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from bot.config import settings
from bot.core.database import AsyncSessionFactory
from bot.db.models import User, UserRole
from bot.core.logger import logger


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        telegram_user = None
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user

        if not telegram_user:
            return await handler(event, data)

        async with AsyncSessionFactory() as session:
            # Check if user exists
            res = await session.execute(
                select(User).where(User.telegram_id == telegram_user.id)
            )
            user = res.scalar_one_or_none()

            # Auto register Super Admin if matching SUPER_ADMIN_ID in .env
            if not user:
                role = UserRole.SUPER_ADMIN if telegram_user.id == settings.SUPER_ADMIN_ID else UserRole.MEMBER
                user = User(
                    telegram_id=telegram_user.id,
                    full_name=telegram_user.full_name or "المستخدم",
                    username=telegram_user.username,
                    role=role,
                    is_active=True
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"New user registered: {user.full_name} ({user.telegram_id}) with role: {user.role}")
            else:
                # Update super admin role if set in .env
                if telegram_user.id == settings.SUPER_ADMIN_ID and user.role != UserRole.SUPER_ADMIN:
                    user.role = UserRole.SUPER_ADMIN
                    await session.commit()

            data["db_user"] = user
            data["user_role"] = user.role
            data["db_session"] = session

            return await handler(event, data)


def check_role_permission(user_role: UserRole, allowed_roles: list[UserRole]) -> bool:
    """Checks if a user role is within allowed roles."""
    if user_role == UserRole.SUPER_ADMIN:
        return True
    return user_role in allowed_roles
