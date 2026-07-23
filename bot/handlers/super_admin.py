import json
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, UserRole, AuditLog, Income, Expense, Student, Sponsor
from bot.services.audit_service import AuditService
from bot.services.finance_service import FinanceService
from bot.keyboards.inline_keyboards import get_back_keyboard

super_admin_router = Router()


class RoleManagementFSM(StatesGroup):
    target_user_id = State()


# --- ROLE MANAGEMENT ---

@super_admin_router.callback_query(F.data == "add_finance_admin")
async def start_add_finance_admin(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role != UserRole.SUPER_ADMIN:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.update_data(target_role=UserRole.FINANCE_ADMIN)
    await state.set_state(RoleManagementFSM.target_user_id)
    await callback.message.edit_text("👤 **إضافة مسؤول مالي**\n\nأدخل **Telegram User ID** الخاص بالعضو المراد تعيينه كمسؤول مالي:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@super_admin_router.callback_query(F.data == "add_relations_admin")
async def start_add_relations_admin(callback: CallbackQuery, user_role: UserRole, state: FSMContext):
    if user_role != UserRole.SUPER_ADMIN:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await state.update_data(target_role=UserRole.RELATIONS_ADMIN)
    await state.set_state(RoleManagementFSM.target_user_id)
    await callback.message.edit_text("🤝 **إضافة مسؤول علاقات**\n\nأدخل **Telegram User ID** الخاص بالعضو المراد تعيينه كمسؤول علاقات:", reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


@super_admin_router.message(RoleManagementFSM.target_user_id)
async def process_role_user_id(message: Message, state: FSMContext, db_user: User, db_session: AsyncSession):
    try:
        target_tg_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ يرجى إدخال رقم Telegram ID صحيح.")
        return

    data = await state.get_data()
    target_role = data["target_role"]

    res = await db_session.execute(select(User).where(User.telegram_id == target_tg_id))
    user = res.scalar_one_or_none()

    if not user:
        # Register new user shell
        user = User(
            telegram_id=target_tg_id,
            full_name=f"مستخدم {target_tg_id}",
            role=target_role,
            is_active=True
        )
        db_session.add(user)
    else:
        user.role = target_role

    await db_session.flush()

    await AuditService.log_action(
        session=db_session,
        action="UPDATE_ROLE",
        entity_type="USER",
        entity_id=user.id,
        performed_by_user_id=db_user.id,
        new_values={"role": target_role.value, "telegram_id": target_tg_id}
    )

    await db_session.commit()
    await state.clear()

    await message.answer(
        f"✅ **تم تحديث الصلاحية بنجاح!**\n\n👤 المستخدم `{target_tg_id}` أصبح الآن: **{target_role.value}**",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown"
    )


# --- AUDIT LOGS VIEW ---

@super_admin_router.callback_query(F.data == "view_audit_logs")
async def cb_view_audit_logs(callback: CallbackQuery, user_role: UserRole, db_session: AsyncSession):
    if user_role != UserRole.SUPER_ADMIN:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    res = await db_session.execute(
        select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(15)
    )
    logs = res.scalars().all()

    if not logs:
        await callback.message.edit_text("📭 لا توجد سجلات في Audit Log حتى الآن.", reply_markup=get_back_keyboard())
        await callback.answer()
        return

    text = "📑 **سجل العمليات الإدارية (Audit Logs):**\n\n"
    for lg in logs:
        text += (
            f"🔹 `[{lg.action}]` {lg.entity_type} (ID: {lg.entity_id or '-'})\n"
            f"بواسطة المستخدم ID: {lg.performed_by_user_id} | الوقت: {lg.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            f"التفاصيل: {json.dumps(lg.new_values or {}, ensure_ascii=False)}\n"
            f"ــــــــــــــــــــــــــــــــــــــــ\n"
        )

    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
    await callback.answer()


# --- DATABASE BACKUP ---

@super_admin_router.callback_query(F.data == "backup_database")
async def cb_backup_database(callback: CallbackQuery, user_role: UserRole, db_session: AsyncSession):
    if user_role != UserRole.SUPER_ADMIN:
        await callback.answer("🚫 ليس لديك صلاحية لاستخدام هذا الأمر.", show_alert=True)
        return

    await callback.message.answer("⏳ جاري إنشاء النسخة الاحتياطية للداتا...")

    users_res = await db_session.execute(select(User))
    students_res = await db_session.execute(select(Student))
    sponsors_res = await db_session.execute(select(Sponsor))
    incomes_res = await db_session.execute(select(Income))
    expenses_res = await db_session.execute(select(Expense))

    backup_data = {
        "generated_at": datetime.now().isoformat(),
        "users": [
            {"id": u.id, "telegram_id": u.telegram_id, "name": u.full_name, "role": u.role.value}
            for u in users_res.scalars().all()
        ],
        "students": [
            {"id": s.id, "name": s.name, "code": s.student_code, "paid": float(s.total_paid), "remaining": float(s.remaining_amount)}
            for s in students_res.scalars().all()
        ],
        "sponsors": [
            {"id": sp.id, "company": sp.company_name, "amount": float(sp.amount), "type": sp.sponsorship_type.value}
            for sp in sponsors_res.scalars().all()
        ],
        "incomes": [
            {"op": inc.op_number, "category": inc.category.value, "amount": float(inc.amount), "date": inc.date.isoformat()}
            for inc in incomes_res.scalars().all()
        ],
        "expenses": [
            {"op": exp.op_number, "reason": exp.reason, "amount": float(exp.amount), "date": exp.date.isoformat()}
            for exp in expenses_res.scalars().all()
        ]
    }

    json_bytes = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"yemen_cyber_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    input_file = BufferedInputFile(json_bytes, filename=filename)
    await callback.message.answer_document(
        document=input_file,
        caption="💾 **نسخة احتياطية كاملة من قاعدة بيانات البوت.**",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()
