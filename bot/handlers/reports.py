from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.report_service import ReportService
from bot.services.finance_service import FinanceService
from bot.services.notification_service import format_currency
from bot.keyboards.inline_keyboards import get_back_keyboard

reports_router = Router()


@reports_router.callback_query(F.data == "report_balance")
async def cb_report_balance(callback: CallbackQuery, db_session: AsyncSession):
    fin = await FinanceService.get_financial_summary(db_session)
    text = (
        f"💵 **الرصيد المالي الحالي للدفعة:**\n\n"
        f"💰 **إجمالي الإيرادات:** {format_currency(fin['total_income'])}\n"
        f"💸 **إجمالي المصروفات:** {format_currency(fin['total_expenses'])}\n"
        f"📊 **المتبقي (الرصيد الصافي):** {format_currency(fin['current_balance'])}\n"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@reports_router.callback_query(F.data == "report_summary")
async def cb_report_summary(callback: CallbackQuery, db_session: AsyncSession):
    stats = await ReportService.get_dashboard_stats(db_session)

    text = (
        f"📊 **تقرير الشؤون المالية والإحصائيات الفورية:**\n\n"
        f"💰 **إجمالي الإيرادات:** {format_currency(stats['total_income'])}\n"
        f"💸 **إجمالي المصروفات:** {format_currency(stats['total_expenses'])}\n"
        f"💵 **الرصيد الحالي:** {format_currency(stats['current_balance'])}\n\n"
        f"👨‍🎓 **عدد الطلاب المسددين:** {stats['paid_students']} / {stats['total_students']}\n"
        f"🔴 **عدد الطلاب المتبقين:** {stats['unpaid_students']}\n"
        f"💰 **إجمالي المتبقي على الطلاب:** {format_currency(stats['total_student_remaining'])}\n\n"
        f"🏆 **أكبر داعم:** {stats['top_sponsor']} ({format_currency(stats['top_sponsor_amount'])})\n\n"
        f"📅 **إيرادات اليوم:** {format_currency(stats['today_income'])}\n"
        f"📉 **مصروفات اليوم:** {format_currency(stats['today_expenses'])}\n"
        f"🗓️ **إيرادات الشهر الحالي:** {format_currency(stats['monthly_income'])}\n"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()
