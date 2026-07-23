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
        f"💵 <b>الرصيد المالي الحالي للدفعة:</b>\n\n"
        f"💰 <b>إجمالي الإيرادات:</b> {format_currency(fin['total_income'])}\n"
        f"💸 <b>إجمالي المصروفات:</b> {format_currency(fin['total_expenses'])}\n"
        f"📊 <b>المتبقي (الرصيد الصافي):</b> {format_currency(fin['current_balance'])}\n"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@reports_router.callback_query(F.data == "report_summary")
async def cb_report_summary(callback: CallbackQuery, db_session: AsyncSession):
    stats = await ReportService.get_dashboard_stats(db_session)

    text = (
        f"📊 <b>تقرير الشؤون المالية والإحصائيات الفورية:</b>\n\n"
        f"💰 <b>إجمالي الإيرادات:</b> {format_currency(stats['total_income'])}\n"
        f"💸 <b>إجمالي المصروفات:</b> {format_currency(stats['total_expenses'])}\n"
        f"💵 <b>الرصيد الحالي:</b> {format_currency(stats['current_balance'])}\n\n"
        f"👨‍🎓 <b>عدد الطلاب المسددين:</b> {stats['paid_students']} / {stats['total_students']}\n"
        f"🔴 <b>عدد الطلاب المتبقين:</b> {stats['unpaid_students']}\n"
        f"💰 <b>إجمالي المتبقي على الطلاب:</b> {format_currency(stats['total_student_remaining'])}\n\n"
        f"🏆 <b>أكبر داعم:</b> {stats['top_sponsor']} ({format_currency(stats['top_sponsor_amount'])})\n\n"
        f"📅 <b>إيرادات اليوم:</b> {format_currency(stats['today_income'])}\n"
        f"📉 <b>مصروفات اليوم:</b> {format_currency(stats['today_expenses'])}\n"
        f"🗓️ <b>إيرادات الشهر الحالي:</b> {format_currency(stats['monthly_income'])}\n"
    )
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()
