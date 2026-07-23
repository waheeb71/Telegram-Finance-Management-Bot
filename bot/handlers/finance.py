from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserRole, IncomeCategory
from bot.services.finance_service import FinanceService
from bot.services.notification_service import NotificationService, format_currency
from bot.core.image_storage import ImageStorageManager
from bot.keyboards.inline_keyboards import get_back_keyboard

finance_router = Router()


class AddIncomeFSM(StatesGroup):
    category = State()
    amount = State()
    recipient_name = State()
    notes = State()
    photo = State()


class AddExpenseFSM(StatesGroup):
    amount = State()
    reason = State()
    beneficiary_name = State()
    notes = State()
    photo = State()


# --- ADD INCOME HANDLERS ---

@finance_router.callback_query(F.data == "add_income")
async def start_add_income(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="رسوم طالب", callback_data="inc_cat_STUDENT_FEE")],
        [InlineKeyboardButton(text="راعٍ", callback_data="inc_cat_SPONSOR")],
        [InlineKeyboardButton(text="تبرع", callback_data="inc_cat_DONATION")],
        [InlineKeyboardButton(text="دعم شركة", callback_data="inc_cat_CORPORATE_SUPPORT")],
        [InlineKeyboardButton(text="دعم مؤسسة", callback_data="inc_cat_INSTITUTION_SUPPORT")],
        [InlineKeyboardButton(text="أخرى", callback_data="inc_cat_OTHER")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="main_menu")]
    ])
    await state.set_state(AddIncomeFSM.category)
    await callback.message.edit_text("💰 <b>إضافة إيراد جديد</b>\n\nاختر نوع الإيراد:", reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@finance_router.callback_query(AddIncomeFSM.category, F.data.startswith("inc_cat_"))
async def process_income_category(callback: CallbackQuery, state: FSMContext):
    cat_str = callback.data.replace("inc_cat_", "")
    
    if cat_str == "STUDENT_FEE":
        from bot.handlers.students import RecordStudentFeeFSM
        await state.set_state(RecordStudentFeeFSM.student_search)
        await callback.message.edit_text(
            "🔍 <b>تسجيل رسوم طالب</b>\n\nاكتب <b>اسم الطالب</b> أو <b>رقمه الأكاديمي</b> للبحث عنه لخصم المبلغ من حسابه الفردي وتحديث المتبقي عليه:",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await state.update_data(category=IncomeCategory[cat_str])
    await state.set_state(AddIncomeFSM.amount)
    await callback.message.edit_text("💵 أدخل <b>مبلغ الإيراد</b> بالريال (مثال: 50000):", reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@finance_router.message(AddIncomeFSM.amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم صحيح وموجب للمبلغ.")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddIncomeFSM.recipient_name)
    await message.answer("👤 أدخل <b>اسم المستلم</b> (الشخص الذي استلم المبلغ):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddIncomeFSM.recipient_name)
async def process_income_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient_name=message.text.strip())
    await state.set_state(AddIncomeFSM.notes)
    await message.answer("📝 أدخل أي <b>ملاحظات إضافية</b> (أو أرسل كلمة 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddIncomeFSM.notes)
async def process_income_notes(message: Message, state: FSMContext):
    notes = message.text.strip()
    if notes == "لا يوجد":
        notes = None
    await state.update_data(notes=notes)
    await state.set_state(AddIncomeFSM.photo)
    await message.answer("📷 أرسل <b>صورة السند</b> (أو أرسل كلمة 'تخطي' لإكمال العملية بدون صورة):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddIncomeFSM.photo)
async def process_income_photo(message: Message, state: FSMContext, bot: Bot, db_user: User, db_session: AsyncSession):
    data = await state.get_data()
    photo_file_id = None
    photo_msg_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        upload_res = await ImageStorageManager.upload_photo(
            bot=bot,
            photo_file_id=photo_file_id,
            caption=f"سند إيراد: {data['amount']} ريال - مستلم: {data['recipient_name']}"
        )
        photo_file_id = upload_res["file_id"]
        photo_msg_id = upload_res["message_id"]

    income = await FinanceService.add_income(
        session=db_session,
        category=data["category"],
        amount=data["amount"],
        recipient_name=data["recipient_name"],
        recorded_by_user_id=db_user.id,
        notes=data.get("notes"),
        receipt_photo_file_id=photo_file_id,
        receipt_photo_message_id=photo_msg_id
    )

    await db_session.commit()
    await state.clear()

    fin_summary = await FinanceService.get_financial_summary(db_session)

    notif_text = NotificationService.format_income_notification(
        category_name=income.category.value,
        source_name=data["recipient_name"],
        amount=income.amount,
        current_balance=fin_summary["current_balance"]
    )
    await NotificationService.send_group_notification(bot, db_session, notif_text)
    await db_session.commit()

    success_msg = (
        f"✅ <b>تم تسجيل الإيراد بنجاح!</b>\n\n"
        f"🔢 <b>رقم العملية:</b> <code>{income.op_number}</code>\n"
        f"💰 <b>المبلغ:</b> {format_currency(income.amount)}\n"
        f"💵 <b>الرصيد الحالي للدفعة:</b> {format_currency(fin_summary['current_balance'])}\n"
    )
    await message.answer(success_msg, reply_markup=get_back_keyboard(), parse_mode="HTML")


# --- ADD EXPENSE HANDLERS ---

@finance_router.callback_query(F.data == "add_expense")
async def start_add_expense(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.set_state(AddExpenseFSM.amount)
    await callback.message.edit_text("💸 <b>إضافة مصروف جديد</b>\n\nأدخل <b>مبلغ المصروف</b> بالريال:", reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@finance_router.message(AddExpenseFSM.amount)
async def process_expense_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم صحيح وموجب للمبلغ.")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpenseFSM.reason)
    await message.answer("📝 أدخل <b>سبب الصرف</b> (البند / الغرض):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddExpenseFSM.reason)
async def process_expense_reason(message: Message, state: FSMContext):
    await state.update_data(reason=message.text.strip())
    await state.set_state(AddExpenseFSM.beneficiary_name)
    await message.answer("👤 أدخل <b>اسم المستفيد / جهة الصرف</b>:", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddExpenseFSM.beneficiary_name)
async def process_expense_beneficiary(message: Message, state: FSMContext):
    await state.update_data(beneficiary_name=message.text.strip())
    await state.set_state(AddExpenseFSM.notes)
    await message.answer("📝 أدخل أي <b>ملاحظات إضافية</b> (أو أرسل كلمة 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddExpenseFSM.notes)
async def process_expense_notes(message: Message, state: FSMContext):
    notes = message.text.strip()
    if notes == "لا يوجد":
        notes = None
    await state.update_data(notes=notes)
    await state.set_state(AddExpenseFSM.photo)
    await message.answer("📷 أرسل <b>صورة الفاتورة</b> (أو أرسل كلمة 'تخطي' لإكمال العملية بدون صورة):", reply_markup=get_back_keyboard(), parse_mode="HTML")


@finance_router.message(AddExpenseFSM.photo)
async def process_expense_photo(message: Message, state: FSMContext, bot: Bot, db_user: User, db_session: AsyncSession):
    data = await state.get_data()
    photo_file_id = None
    photo_msg_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        upload_res = await ImageStorageManager.upload_photo(
            bot=bot,
            photo_file_id=photo_file_id,
            caption=f"فاتورة مصروف: {data['amount']} ريال - سبب: {data['reason']}"
        )
        photo_file_id = upload_res["file_id"]
        photo_msg_id = upload_res["message_id"]

    expense = await FinanceService.add_expense(
        session=db_session,
        amount=data["amount"],
        reason=data["reason"],
        beneficiary_name=data["beneficiary_name"],
        processed_by_user_id=db_user.id,
        notes=data.get("notes"),
        invoice_photo_file_id=photo_file_id,
        invoice_photo_message_id=photo_msg_id
    )

    await db_session.commit()
    await state.clear()

    fin_summary = await FinanceService.get_financial_summary(db_session)

    notif_text = NotificationService.format_expense_notification(
        reason=expense.reason,
        beneficiary=expense.beneficiary_name,
        amount=expense.amount,
        current_balance=fin_summary["current_balance"]
    )
    await NotificationService.send_group_notification(bot, db_session, notif_text)
    await db_session.commit()

    success_msg = (
        f"✅ <b>تم تسجيل المصروف بنجاح!</b>\n\n"
        f"🔢 <b>رقم العملية:</b> <code>{expense.op_number}</code>\n"
        f"💸 <b>المبلغ:</b> {format_currency(expense.amount)}\n"
        f"💵 <b>الرصيد الحالي للدفعة:</b> {format_currency(fin_summary['current_balance'])}\n"
    )
    await message.answer(success_msg, reply_markup=get_back_keyboard(), parse_mode="HTML")


# --- LISTING OPERATIONS ---

@finance_router.callback_query(F.data == "list_incomes")
async def cb_list_incomes(callback: CallbackQuery, db_session: AsyncSession):
    incomes = await FinanceService.get_latest_incomes(db_session, limit=10)
    if not incomes:
        await callback.message.edit_text("📭 لا توجد إيرادات مسجلة حتى الآن.", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    text = "💰 <b>سجل آخر الإيرادات المسجلة:</b>\n\n"
    for inc in incomes:
        text += (
            f"🔹 <code>{inc.op_number}</code> | <b>{format_currency(inc.amount)}</b>\n"
            f"النوع: {inc.category.value} | المستلم: {inc.recipient_name}\n"
            f"التاريخ: {inc.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
        )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()


@finance_router.callback_query(F.data == "list_expenses")
async def cb_list_expenses(callback: CallbackQuery, db_session: AsyncSession):
    expenses = await FinanceService.get_latest_expenses(db_session, limit=10)
    if not expenses:
        await callback.message.edit_text("📭 لا توجد مصروفات مسجلة حتى الآن.", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    text = "💸 <b>سجل آخر المصروفات المسجلة:</b>\n\n"
    for exp in expenses:
        text += (
            f"🔸 <code>{exp.op_number}</code> | <b>{format_currency(exp.amount)}</b>\n"
            f"السبب: {exp.reason} | المستفيد: {exp.beneficiary_name}\n"
            f"التاريخ: {exp.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
        )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()
