from bot.keyboards.inline_keyboards import get_operations_menu_keyboard
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from bot.db.models import User, UserRole
from bot.keyboards.inline_keyboards import (
    get_main_menu_keyboard,
    get_income_menu_keyboard,
    get_expense_menu_keyboard,
    get_student_menu_keyboard,
    get_sponsor_menu_keyboard,
    get_reports_menu_keyboard,
    get_admin_menu_keyboard
)

common_router = Router()

UNAUTHORIZED_TEXT = "🚫 ليس لديك صلاحية لاستخدام هذا الأمر."


@common_router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, user_role: UserRole):
    welcome_text = (
        f"👋 <b>مرحباً بك في بوت Yemen Cyber Finance Bot</b>\n\n"
        f"النظام المالي الموحد لإدارة إيرادات ومصروفات دفعة تخرج <b>«يمن سايبر»</b>.\n\n"
        f"👤 <b>اسمك:</b> {db_user.full_name}\n"
        f"🔰 <b>صلاحيتك:</b> {db_user.role.value}\n\n"
         f"ملاحظة: البوت قد يتاخر بالرد بسبب السرفر"
        f"الرجاء اختيار القسم المطلوب من القائمة أدناه:"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=get_main_menu_keyboard(user_role),
        parse_mode="HTML"
    )


@common_router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, db_user: User, user_role: UserRole):
    text = f"🏠 <b>القائمة الرئيسية - Yemen Cyber Finance Bot</b>"
    await callback.message.edit_text(
        text=text,
        reply_markup=get_main_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_income")
async def cb_income_menu(callback: CallbackQuery, user_role: UserRole):
    await callback.message.edit_text(
        text="💰 <b>قسم الإيرادات</b>\n\nاختر الإجراء المطلوب:",
        reply_markup=get_income_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_expenses")
async def cb_expense_menu(callback: CallbackQuery, user_role: UserRole):
    await callback.message.edit_text(
        text="💸 <b>قسم المصروفات</b>\n\nاختر الإجراء المطلوب:",
        reply_markup=get_expense_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_students")
async def cb_students_menu(callback: CallbackQuery, user_role: UserRole):
    await callback.message.edit_text(
        text="👨‍🎓 <b>شؤون ومستحقات الطلاب</b>\n\nاختر الإجراء المطلوب:",
        reply_markup=get_student_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_sponsors")
async def cb_sponsors_menu(callback: CallbackQuery, user_role: UserRole):
    await callback.message.edit_text(
        text="🏢 <b>إدارة الرعاة والداعمين</b>\n\nاختر الإجراء المطلوب:",
        reply_markup=get_sponsor_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_operations")
async def cb_operations_menu(callback: CallbackQuery, user_role: UserRole):
    await callback.message.edit_text(
        text="📂 <b>سجل وقائمة العمليات</b>\n\nاختر الخيار المطلوب:",
        reply_markup=get_operations_menu_keyboard(user_role),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_reports")
async def cb_reports_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        text="📊 <b>التقارير والإحصائيات</b>\n\nاختر التقرير المطلوب:",
        reply_markup=get_reports_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "menu_admin")
async def cb_admin_menu(callback: CallbackQuery, user_role: UserRole):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer(UNAUTHORIZED_TEXT, show_alert=True)
        return

    await callback.message.edit_text(
        text="⚙️ <b>لوحة الإدارة والصلاحيات والنسخ الاحتياطي</b>\n\nاختر الإجراء المطلوب:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
