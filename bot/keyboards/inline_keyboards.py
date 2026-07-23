from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.models import UserRole


def get_main_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💰 الإيرادات", callback_data="menu_income"),
            InlineKeyboardButton(text="💸 المصروفات", callback_data="menu_expenses")
        ],
        [
            InlineKeyboardButton(text="👨‍🎓 الطلاب", callback_data="menu_students"),
            InlineKeyboardButton(text="🏢 الرعاة", callback_data="menu_sponsors")
        ],
        [
            InlineKeyboardButton(text="📊 التقارير", callback_data="menu_reports"),
            InlineKeyboardButton(text="📂 العمليات", callback_data="menu_operations")
        ],
        [
            InlineKeyboardButton(text="📁 التصدير (PDF / Excel)", callback_data="menu_export")
        ]
    ]

    if role in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        buttons.append([
            InlineKeyboardButton(text="⚙️ لوحة الإدارة والصلاحيات", callback_data="menu_admin")
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_income_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = []
    if role in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        buttons.append([InlineKeyboardButton(text="➕ إضافة إيراد جديد", callback_data="add_income")])
    
    buttons.append([InlineKeyboardButton(text="📋 عرض آخر الإيرادات", callback_data="list_incomes")])
    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_expense_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = []
    if role in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        buttons.append([InlineKeyboardButton(text="➕ إضافة مصروف جديد", callback_data="add_expense")])
    
    buttons.append([InlineKeyboardButton(text="📋 عرض آخر المصروفات", callback_data="list_expenses")])
    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_student_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = []
    if role in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        buttons.append([
            InlineKeyboardButton(text="➕ إضافة طالب جديد", callback_data="add_student"),
            InlineKeyboardButton(text="💳 تسجيل رسوم طالب", callback_data="record_student_fee")
        ])
    
    buttons.append([
        InlineKeyboardButton(text="📜 كشف حساب الطلاب", callback_data="student_statement")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sponsor_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = []
    if role in [UserRole.SUPER_ADMIN, UserRole.RELATIONS_ADMIN]:
        buttons.append([InlineKeyboardButton(text="➕ إضافة راعٍ جديد", callback_data="add_sponsor")])
    
    buttons.append([InlineKeyboardButton(text="📜 عرض قائمة الرعاة", callback_data="list_sponsors")])
    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_reports_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💵 عرض الرصيد الإجمالي", callback_data="report_balance"),
            InlineKeyboardButton(text="📜 كشف حساب الطلاب", callback_data="student_statement")
        ],
        [
            InlineKeyboardButton(text="🏢 قائمة الرعاة", callback_data="list_sponsors"),
            InlineKeyboardButton(text="💸 آخر المصروفات", callback_data="list_expenses")
        ],
        [
            InlineKeyboardButton(text="💰 آخر الإيرادات", callback_data="list_incomes"),
            InlineKeyboardButton(text="📈 إحصائيات فورية", callback_data="report_summary")
        ],
        [
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="👤 إضافة مسؤول مالي", callback_data="add_finance_admin"),
            InlineKeyboardButton(text="❌ حذف مسؤول مالي", callback_data="del_finance_admin")
        ],
        [
            InlineKeyboardButton(text="🤝 إضافة مسؤول علاقات", callback_data="add_relations_admin"),
            InlineKeyboardButton(text="❌ حذف مسؤول علاقات", callback_data="del_relations_admin")
        ],
        [
            InlineKeyboardButton(text="✏️ تعديل آخر عملية", callback_data="edit_last_op"),
            InlineKeyboardButton(text="📑 عرض سجل العمليات Audit", callback_data="view_audit_logs")
        ],
        [
            InlineKeyboardButton(text="💾 النسخ الاحتياطي للداتا", callback_data="backup_database")
        ],
        [
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_operations_menu_keyboard(role: UserRole) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💰 آخر الإيرادات", callback_data="list_incomes"),
            InlineKeyboardButton(text="💸 آخر المصروفات", callback_data="list_expenses")
        ]
    ]

    if role in [UserRole.SUPER_ADMIN, UserRole.FINANCE_ADMIN]:
        buttons.append([
            InlineKeyboardButton(text="✏️ تعديل آخر عملية", callback_data="edit_last_op"),
            InlineKeyboardButton(text="📑 سجل العمليات Audit Log", callback_data="view_audit_logs")
        ])

    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="main_menu")]
    ])
