# pyrefly: ignore [missing-import]
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from bot.config import settings
from bot.db.models import Notification
from bot.core.logger import logger


def format_currency(amount: float) -> str:
    return f"{amount:,.0f} {settings.CURRENCY_SYMBOL}".replace(",", "،")


class NotificationService:
    @staticmethod
    async def send_group_notification(bot: Bot, session: AsyncSession, text: str):
        """
        Sends an automatic broadcast message to all configured Telegram Groups.
        """
        group_ids = settings.get_notification_group_ids()
        if not group_ids:
            logger.info("No notification group IDs configured. Skipping broadcast.")
            return

        for group_id in group_ids:
            status = "SENT"
            try:
                await bot.send_message(
                    chat_id=group_id,
                    text=text,
                    parse_mode="HTML"
                )
                logger.info(f"Notification sent successfully to group {group_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to group {group_id}: {e}")
                status = f"FAILED: {e}"

            notification = Notification(
                group_id=group_id,
                message_text=text,
                status=status
            )
            session.add(notification)
        
        await session.flush()

    @staticmethod
    def format_income_notification(
        category_name: str,
        source_name: str,
        amount: float,
        current_balance: float
    ) -> str:
        return (
            f"💰 <b>تم استلام إيراد جديد</b>\n\n"
            f"<b>النوع:</b> {category_name}\n"
            f"<b>المصدر / الطالب:</b> {source_name}\n"
            f"<b>المبلغ:</b> {format_currency(amount)}\n"
            f"<b>الرصيد الحالي للدفعة:</b> {format_currency(current_balance)}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ"
        )

    @staticmethod
    def format_expense_notification(
        reason: str,
        beneficiary: str,
        amount: float,
        current_balance: float
    ) -> str:
        return (
            f"💸 <b>تم تسجيل مصروف جديد</b>\n\n"
            f"<b>السبب:</b> {reason}\n"
            f"<b>المستفيد:</b> {beneficiary}\n"
            f"<b>المبلغ:</b> {format_currency(amount)}\n"
            f"<b>الرصيد الحالي للدفعة:</b> {format_currency(current_balance)}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ"
        )

    @staticmethod
    def format_sponsor_notification(
        company_name: str,
        amount: float,
        sponsorship_type: str,
        current_balance: float
    ) -> str:
        return (
            f"🏢 <b>تمت إضافة راعٍ جديد للدفعة</b>\n\n"
            f"<b>اسم الجهة / الشركة:</b> {company_name}\n"
            f"<b>نوع الرعاية:</b> {sponsorship_type}\n"
            f"<b>قيمة الدعم:</b> {format_currency(amount)}\n"
            f"<b>الرصيد الحالي للدفعة:</b> {format_currency(current_balance)}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ"
        )
