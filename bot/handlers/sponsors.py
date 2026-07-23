from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserRole, SponsorshipType
from bot.services.sponsor_service import SponsorService
from bot.services.finance_service import FinanceService
from bot.services.notification_service import NotificationService, format_currency
from bot.keyboards.inline_keyboards import get_back_keyboard

sponsors_router = Router()


class AddSponsorFSM(StatesGroup):
    company_name = State()
    contact_person = State()
    phone = State()
    amount = State()
    sponsorship_type = State()
    notes = State()


@sponsors_router.callback_query(F.data == "add_sponsor")
async def start_add_sponsor(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role not in [UserRole.SUPER_ADMIN, UserRole.RELATIONS_ADMIN]:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.set_state(AddSponsorFSM.company_name)
    await callback.message.edit_text("🏢 **إضافة راعٍ جديد**\n\nأدخل **اسم الشركة / الجهة الراعية**:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@sponsors_router.message(AddSponsorFSM.company_name)
async def process_sponsor_company(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text.strip())
    await state.set_state(AddSponsorFSM.contact_person)
    await message.answer("👤 أدخل **اسم شخص التواصل / المسؤول** (أو 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@sponsors_router.message(AddSponsorFSM.contact_person)
async def process_sponsor_contact(message: Message, state: FSMContext):
    person = message.text.strip()
    if person == "لا يوجد":
        person = None
    await state.update_data(contact_person=person)
    await state.set_state(AddSponsorFSM.phone)
    await message.answer("📱 أدخل **رقم هاتف الراعي / المسؤول** (أو 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@sponsors_router.message(AddSponsorFSM.phone)
async def process_sponsor_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if phone == "لا يوجد":
        phone = None
    await state.update_data(phone=phone)
    await state.set_state(AddSponsorFSM.amount)
    await message.answer("💵 أدخل **مبلغ الدعم / الرعاية النقدية** (إذا كانت الرعاية غير نقدية أدخل 0):", reply_markup=get_back_keyboard(), parse_mode="Markdown")


@sponsors_router.message(AddSponsorFSM.amount)
async def process_sponsor_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", ""))
        if amount < 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم صحيح وموجب للمبلغ.")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddSponsorFSM.sponsorship_type)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="نقدي", callback_data="spo_type_CASH")],
        [InlineKeyboardButton(text="عيني", callback_data="spo_type_IN_KIND")],
        [InlineKeyboardButton(text="بانر", callback_data="spo_type_BANNER")],
        [InlineKeyboardButton(text="طباعة", callback_data="spo_type_PRINTING")],
        [InlineKeyboardButton(text="قاعات", callback_data="spo_type_HALLS")],
        [InlineKeyboardButton(text="ضيافة", callback_data="spo_type_HOSPITALITY")],
        [InlineKeyboardButton(text="أخرى", callback_data="spo_type_OTHER")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="main_menu")]
    ])
    await message.answer("🏷️ **اختر نوع الرعاية:**", reply_markup=kb, parse_mode="Markdown")


@sponsors_router.callback_query(AddSponsorFSM.sponsorship_type, F.data.startswith("spo_type_"))
async def process_sponsor_type(callback: CallbackQuery, state: FSMContext):
    stype_str = callback.data.replace("spo_type_", "")
    await state.update_data(sponsorship_type=SponsorshipType[stype_str])
    await state.set_state(AddSponsorFSM.notes)
    await callback.message.edit_text("📝 أدخل أي **ملاحظات إضافية** (أو أرسل كلمة 'لا يوجد'):", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@sponsors_router.message(AddSponsorFSM.notes)
async def process_sponsor_notes(message: Message, state: FSMContext, bot: Bot, db_user: User, db_session: AsyncSession):
    notes = message.text.strip()
    if notes == "لا يوجد":
        notes = None

    data = await state.get_data()
    sponsor, income = await SponsorService.add_sponsor(
        session=db_session,
        company_name=data["company_name"],
        contact_person=data.get("contact_person"),
        phone=data.get("phone"),
        amount=data["amount"],
        sponsorship_type=data["sponsorship_type"],
        performed_by_user_id=db_user.id,
        notes=notes
    )

    await db_session.commit()
    await state.clear()

    fin_summary = await FinanceService.get_financial_summary(db_session)

    # Send notification if financial sponsor
    if sponsor.amount > 0:
        notif_text = NotificationService.format_sponsor_notification(
            company_name=sponsor.company_name,
            amount=sponsor.amount,
            sponsorship_type=sponsor.sponsorship_type.value,
            current_balance=fin_summary["current_balance"]
        )
        await NotificationService.send_group_notification(bot, db_session, notif_text)
        await db_session.commit()

    success_msg = (
        f"✅ **تمت إضافة الراعي بنجاح!**\n\n"
        f"🏢 **الشركة / الجهة:** {sponsor.company_name}\n"
        f"🏷️ **نوع الرعاية:** {sponsor.sponsorship_type.value}\n"
        f"💰 **المبلغ:** {format_currency(sponsor.amount)}\n"
        f"💵 **الرصيد الحالي للدفعة:** {format_currency(fin_summary['current_balance'])}\n"
    )
    await message.answer(success_msg, reply_markup=get_back_keyboard(), parse_mode="Markdown")


@sponsors_router.callback_query(F.data == "list_sponsors")
async def cb_list_sponsors(callback: CallbackQuery, db_session: AsyncSession):
    sponsors = await SponsorService.get_all_sponsors(db_session)
    if not sponsors:
        await callback.message.edit_text("📭 لا يوجد رعاة مسجلون حالياً.", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    text = "🏢 **قائمة الرعاة والداعمين للدفعة:**\n\n"
    for sp in sponsors:
        text += (
            f"🔹 **{sp.company_name}** | النوع: {sp.sponsorship_type.value}\n"
            f"المبلغ: **{format_currency(sp.amount)}** | المسؤول: {sp.contact_person or 'غير محدد'}\n"
            f"ملاحظات: {sp.notes or 'لا يوجد'}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
        )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()
