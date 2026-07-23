from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserRole
from bot.services.student_service import StudentService
from bot.services.finance_service import FinanceService
from bot.services.notification_service import NotificationService, format_currency
from bot.core.image_storage import ImageStorageManager
from bot.keyboards.inline_keyboards import get_back_keyboard

students_router = Router()


class AddStudentFSM(StatesGroup):
    name = State()
    student_code = State()
    phone = State()
    total_required = State()


class RecordStudentFeeFSM(StatesGroup):
    student_search = State()
    select_student = State()
    amount = State()
    recipient_name = State()
    notes = State()
    photo = State()


# --- ADD STUDENT HANDLERS ---

@students_router.callback_query(F.data == "add_student")
async def start_add_student(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.set_state(AddStudentFSM.name)
    await callback.message.edit_text("👨‍🎓 **إضافة طالب جديد**\n\nأدخل **اسم الطالب الرباعي**:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@students_router.message(AddStudentFSM.name)
async def process_student_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddStudentFSM.student_code)
    await message.answer("🔢 أدخل **الرقم الأكاديمي / الكود الخاص بالطالب**:", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(AddStudentFSM.student_code)
async def process_student_code(message: Message, state: FSMContext):
    await state.update_data(student_code=message.text.strip())
    await state.set_state(AddStudentFSM.phone)
    await message.answer("📱 أدخل **رقم هاتف الطالب** (أو أرسل 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(AddStudentFSM.phone)
async def process_student_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if phone == "لا يوجد":
        phone = None
    await state.update_data(phone=phone)
    await state.set_state(AddStudentFSM.total_required)
    await message.answer("💵 أدخل **المبلغ الإجمالي المطلوب من الطالب** بالريال (مثال: 100000):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(AddStudentFSM.total_required)
async def process_student_total(message: Message, state: FSMContext, db_user: User, db_session: AsyncSession):
    try:
        total_required = float(message.text.strip().replace(",", ""))
        if total_required <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم صحيح وموجب للمبلغ.")
        return

    data = await state.get_data()
    student = await StudentService.add_student(
        session=db_session,
        name=data["name"],
        student_code=data["student_code"],
        phone=data.get("phone"),
        total_required=total_required,
        performed_by_user_id=db_user.id
    )

    await db_session.commit()
    await state.clear()

    success_msg = (
        f"✅ **تمت إضافة الطالب بنجاح!**\n\n"
        f"👤 **الاسم:** {student.name}\n"
        f"🔢 **الرقم:** {student.student_code}\n"
        f"💵 **المبلغ المطلوب:** {format_currency(student.total_required)}\n"
    )
    await message.answer(success_msg, reply_markup=get_back_keyboard(), parse_mode="Markdown")


# --- RECORD STUDENT FEE HANDLERS ---

@students_router.callback_query(F.data == "record_student_fee")
async def start_record_fee(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.set_state(RecordStudentFeeFSM.student_search)
    await callback.message.edit_text("🔍 **تسجيل رسوم طالب**\n\nاكتب **اسم الطالب** أو **رقمه الأكاديمي** للبحث عنه:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@students_router.message(RecordStudentFeeFSM.student_search)
async def process_student_search(message: Message, state: FSMContext, db_session: AsyncSession):
    term = message.text.strip()
    students = await StudentService.find_students(db_session, term)

    if not students:
        await message.answer("⚠️ لم يتم العثور على أي طالب بهذا الاسم أو الرقم. حاول مرة أخرى:", reply_markup=get_back_keyboard())
        return

    buttons = []
    for st in students[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{st.name} ({st.student_code}) - المتبقي: {format_currency(st.remaining_amount)}",
                callback_data=f"sel_stu_{st.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data="main_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(RecordStudentFeeFSM.select_student)
    await message.answer("👇 **اختر الطالب من القائمة التالية:**", reply_markup=kb, parse_mode="Markdown")


@students_router.callback_query(RecordStudentFeeFSM.select_student, F.data.startswith("sel_stu_"))
async def process_select_student(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.replace("sel_stu_", ""))
    await state.update_data(student_id=student_id)
    await state.set_state(RecordStudentFeeFSM.amount)
    await callback.message.edit_text("💵 أدخل **المبلغ المدفوع** بالريال:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@students_router.message(RecordStudentFeeFSM.amount)
async def process_fee_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم صحيح وموجب للمبلغ.")
        return

    await state.update_data(amount=amount)
    await state.set_state(RecordStudentFeeFSM.recipient_name)
    await message.answer("👤 أدخل **اسم المستلم** (المسؤول المالي الذي استلم الدفعة):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(RecordStudentFeeFSM.recipient_name)
async def process_fee_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient_name=message.text.strip())
    await state.set_state(RecordStudentFeeFSM.notes)
    await message.answer("📝 أدخل أي **ملاحظات إضافية** (أو أرسل كلمة 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(RecordStudentFeeFSM.notes)
async def process_fee_notes(message: Message, state: FSMContext):
    notes = message.text.strip()
    if notes == "لا يوجد":
        notes = None
    await state.update_data(notes=notes)
    await state.set_state(RecordStudentFeeFSM.photo)
    await message.answer("📷 أرسل **صورة السند** (أو 'تخطي'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@students_router.message(RecordStudentFeeFSM.photo)
async def process_fee_photo(message: Message, state: FSMContext, bot: Bot, db_user: User, db_session: AsyncSession):
    data = await state.get_data()
    photo_file_id = None
    photo_msg_id = None

    if message.photo:
        photo_file_id = message.photo[-1].file_id
        upload_res = await ImageStorageManager.upload_photo(
            bot=bot,
            photo_file_id=photo_file_id,
            caption=f"سند رسوم طالب - المبلغ: {data['amount']} ريال"
        )
        photo_file_id = upload_res["file_id"]
        photo_msg_id = upload_res["message_id"]

    student, income = await StudentService.record_payment(
        session=db_session,
        student_id=data["student_id"],
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

    # Send Notification to Telegram Group
    notif_text = NotificationService.format_income_notification(
        category_name="رسوم طالب",
        source_name=student.name,
        amount=income.amount,
        current_balance=fin_summary["current_balance"]
    )
    await NotificationService.send_group_notification(bot, db_session, notif_text)
    await db_session.commit()

    success_msg = (
        f"✅ **تم تسجيل دفع الرسوم بنجاح!**\n\n"
        f"👨‍🎓 **الطالب:** {student.name}\n"
        f"💰 **المبلغ المدفوع:** {format_currency(income.amount)}\n"
        f"📊 **إجمالي المدفوع حتى الآن:** {format_currency(student.total_paid)}\n"
        f"🔴 **المتبقي على الطالب:** {format_currency(student.remaining_amount)}\n"
        f"💵 **الرصيد الحالي للدفعة:** {format_currency(fin_summary['current_balance'])}\n"
    )
    await message.answer(success_msg, reply_markup=get_back_keyboard(), parse_mode="Markdown")


# --- STUDENT STATEMENT VIEW ---

@students_router.callback_query(F.data == "student_statement")
async def cb_student_statement(callback: CallbackQuery, db_session: AsyncSession):
    stats = await StudentService.get_student_stats(db_session)
    students = stats["paid_list"] + stats["unpaid_list"]

    if not students:
        await callback.message.edit_text("📭 لا يوجد طلاب مسجلون حالياً في النظام.", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    text = f"📜 **كشف حساب رسوم الطلاب ({len(students)} طالب):**\n\n"
    text += f"✅ **عدد المسددين بالكامل:** {stats['paid_count']}\n"
    text += f"🔴 **عدد المتبقي عليهم:** {stats['unpaid_count']}\n"
    text += f"💰 **إجمالي المتبقي على الدفعة:** {format_currency(stats['total_remaining'])}\n"
    text += "ــــــــــــــــــــــــــــــــــــــــ\n\n"

    for st in students[:15]:
        status_icon = "✅" if st.status.value == "PAID" else "🔴"
        text += (
            f"{status_icon} **{st.name}** (`{st.student_code}`)\n"
            f"المدفوع: {format_currency(st.total_paid)} | المتبقي: {format_currency(st.remaining_amount)}\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()
