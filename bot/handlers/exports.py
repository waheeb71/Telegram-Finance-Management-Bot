from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UserRole
from bot.services.export_service import ExportService
from bot.keyboards.inline_keyboards import get_back_keyboard

exports_router = Router()


@exports_router.callback_query(F.data == "menu_export")
async def cb_export_menu(callback: CallbackQuery, user_role: UserRole):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 تصدير شيت Excel كامل", callback_data="export_excel"),
            InlineKeyboardButton(text="📄 تصدير تقرير PDF مالي", callback_data="export_pdf")
        ],
        [InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")]
    ])
    await callback.message.edit_text("📁 **قسم التصديرات**\n\nاختر نوع الملف المراد تصديره:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@exports_router.callback_query(F.data == "export_excel")
async def cb_export_excel(callback: CallbackQuery, db_session: AsyncSession):
    await callback.message.answer("⏳ جاري توليد شيت Excel...")
    excel_io = await ExportService.generate_excel_report(db_session)
    filename = f"Yemen_Cyber_Finance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    input_file = BufferedInputFile(excel_io.getvalue(), filename=filename)
    await callback.message.answer_document(
        document=input_file,
        caption="📊 **تفضل الشيت المالي الكامل بصيغة Excel.**",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@exports_router.callback_query(F.data == "export_pdf")
async def cb_export_pdf(callback: CallbackQuery, db_session: AsyncSession):
    await callback.message.answer("⏳ جاري توليد تقرير PDF...")
    pdf_io = await ExportService.generate_pdf_report(db_session)
    filename = f"Yemen_Cyber_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    input_file = BufferedInputFile(pdf_io.getvalue(), filename=filename)
    await callback.message.answer_document(
        document=input_file,
        caption="📄 **تفضل التقرير المالي الموحد بصيغة PDF.**",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
