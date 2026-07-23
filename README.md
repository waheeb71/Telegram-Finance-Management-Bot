# 🤖 بوت إدارة الشؤون المالية للدفوعات والمشاريع (Telegram Finance Management Bot)

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![Framework](https://img.shields.io/badge/aiogram-3.x-green)
![Database](https://img.shields.io/badge/PostgreSQL-Neon%20DB-orange)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

نظام مالي وإداري متكامل ومفتوح المصدر عبر تليجرام، مصمم لإدارة الإيرادات والمصروفات، مستحقات الطلاب/العملاء، الرعاة والداعمين، مع دعم توليد التقارير الرسمية بصيغ **PDF** و **Excel** وتخزين الصور وسجل العمليات.

---

## 🌟 مميزات المشروع

- 🔐 **نظام صلاحيات متعدد المستويات (RBAC)**:
  - **المدير العام (Super Admin)**: صلاحيات كاملة، إدارة المسؤولين، التعديل والحذف، تتبع السجلات، والنسخ الاحتياطي.
  - **المسؤول المالي (Finance Admin)**: إضافة وتعديل الإيرادات والمصروفات وتسديد المستحقات وعرض التقارير.
  - **مسؤول العلاقات (Relations Admin)**: إضافة وإدارة الرعاة والداعمين.
  - **أعضاء الدفعة / المشروع (Members)**: استعراض التنبيهات والمعلومات التفاعلية فقط.

- 🖼️ **تخزين الصور عبر قناة تليجرام خاصة**:
  - حفظ وتوجيه صور السندات والفواتير تلقائياً إلى قناة تليجرام خاصة وتخزين معرّفاتها لاستعراضها فورياً.

- 📢 **إشعارات فورية متعدّدة (Multi-Group Notifications)**:
  - بث تلقائي لرسائل الإشعارات المنسقة باللغة العربية عند تسجيل أي إيراد أو مصروف لعدة مجموعات في نفس الوقت.

- 📊 **تقارير وتصدير احترافي**:
  - تصدير شيتات **Excel** شاملة لكافة البيانات بضغطة زر (`OpenPyXL`).
  - توليد تقارير **PDF** رسمية منسقة باللغة العربية (`ReportLab`).

- 📑 **سجل عمليات كامل (Audit Log)**:
  - تتبع وتوثيق لكافة عمليات الإضافة، التعديل، والحذف مع حفظ هوية المستخدم، الوقت، والقيم القديمة والجديدة.

---

## 🛠️ التقنيات والمهندسة (Tech Stack)

- **اللغة**: Python 3.12+
- **إطار عمل البوت**: `aiogram 3.x`
- **قواعد البيانات**: `SQLAlchemy 2.0 Async` + `Alembic` + `PostgreSQL (Neon Cloud)`
- **إدارة الحالة والكاش**: `Redis` / `MemoryStorage`
- **التصدير والتقارير**: `ReportLab` (PDF), `OpenPyXL` (Excel)
- **الحاويات والنشر**: `Docker`, `Docker Compose`, `Render.com`

---

## 🚀 دليل التثبيت والتشغيل المحلي (Setup & Installation)

### 1. استنسخ المشروع (Clone):
```bash
git clone https://github.com/YOUR_USERNAME/Telegram-Finance-Management-Bot.git
cd Telegram-Finance-Management-Bot
```

### 2. تثبيت المكتبات (Install Dependencies):
```bash
pip install -r requirements.txt
```

### 3. إعداد متغيرات البيئة (`.env`):
أنشئ ملف باسم `.env` بناءً على `.env.example`:
```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
SUPER_ADMIN_ID=YOUR_TELEGRAM_USER_ID

# يمكنك كتابة أكثر من جروب مفصولة بفاصلة
NOTIFICATION_GROUP_IDS=-1001234567890,-1009876543210
STORAGE_CHANNEL_ID=-1009876543210

# قاعدة البيانات (PostgreSQL / Neon DB)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname?ssl=require

# Redis (اختياري)
REDIS_URL=
```

### 4. تشغيل البوت:
```bash
python -m bot.main
```

---

## ☁️ دليل النشر المجاني على Render.com

1. ارفع المشروع إلى مستودعك على **GitHub**.
2. سجل دخول في موقع [Render.com](https://render.com).
3. أنشئ خدمة جديدة من نوع **Background Worker**.
4. حدد أمر البدء (Start Command):
   ```bash
   python -m bot.main
   ```
5. أضف متغيرات البيئة (`BOT_TOKEN`, `SUPER_ADMIN_ID`, `DATABASE_URL`, `STORAGE_CHANNEL_ID`, `NOTIFICATION_GROUP_IDS`) في قسم **Environment Variables**.
6. اضغط **Deploy Worker** وستعمل الخدمة تلقائياً 24/7.

---

## 📄 الترخيص (License)

هذا المشروع مرخص بموجب رخصة **MIT** - يمكنك استخدام المشروع وتعديله وإعادة نشره بحرية.
