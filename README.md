# 🤖 Telegram Finance Management Bot

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![Framework](https://img.shields.io/badge/aiogram-3.x-green)
![Database](https://img.shields.io/badge/PostgreSQL-Neon%20DB-orange)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

A comprehensive, production-ready, open-source **Telegram Bot** designed for managing finances, income, expenses, student/client fees, sponsor contributions, PDF & Excel reporting, audit logging, and automated Telegram notifications.

---

## 🌟 Key Features

- 🔐 **Role-Based Access Control (RBAC)**:
  - **Super Admin**: Full permissions, user & role management, edit/delete operations, audit logs, and data backups.
  - **Finance Admin**: Record income, record expenses, manage student fee payments, view reports.
  - **Relations Admin**: Manage sponsors, backers, and corporate contributions.
  - **Members**: Interactive inline button navigation for viewing financial overviews and reports.

- 🖼️ **Telegram Channel Image Storage**:
  - Automatically forwards receipt and invoice images to a private Telegram Channel for secure cloud storage and instant retrieval without local disk dependencies.

- 📢 **Multi-Group Broadcast Notifications**:
  - Automatically broadcasts formatted Arabic notification alerts with formatted currency (`20,000 ريال`) to one or multiple Telegram groups upon every new transaction.

- 📊 **Professional PDF & Excel Exports**:
  - **Excel Workbooks**: Multi-sheet export (`OpenPyXL`) covering Summary, Incomes, Expenses, Students, and Sponsors.
  - **PDF Reports**: Arabic PDF summary document generation (`ReportLab`).

- 📑 **Comprehensive Audit Logging & Backups**:
  - Tracks all system actions (CREATE, UPDATE, DELETE) with timestamps, performed user IDs, and previous/new values.
  - One-click JSON database backup generation for Super Admins.

---

## 🛠️ Technology Stack

- **Language**: Python 3.12+
- **Bot Engine**: `aiogram 3.x`
- **Database**: `SQLAlchemy 2.0 Async` + `Alembic` + `PostgreSQL (Neon Cloud)`
- **FSM & Caching**: `Redis` (with automatic fallback to `MemoryStorage`)
- **Document Export**: `ReportLab` (PDF), `OpenPyXL` (Excel)
- **Deployment**: `Docker`, `Docker Compose`, `Render.com`

---

## 🚀 Quick Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/Telegram-Finance-Management-Bot.git
cd Telegram-Finance-Management-Bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (`.env`)
Create a `.env` file based on `.env.example`:
```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
SUPER_ADMIN_ID=YOUR_TELEGRAM_USER_ID

# Comma-separated group IDs for broadcast notifications
NOTIFICATION_GROUP_IDS=-1001234567890,-1009876543210
STORAGE_CHANNEL_ID=-1009876543210

# Database URL (PostgreSQL / Neon DB)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname?ssl=require

# Redis URL (Optional, leave blank for MemoryStorage)
REDIS_URL=
```

### 4. Run the Bot
```bash
python -m bot.main
```

---

## ☁️ Deployment on Render.com

1. Push your repository to **GitHub**.
2. Log into [Render.com](https://render.com) and create a **Background Worker**.
3. Set the **Start Command**:
   ```bash
   python -m bot.main
   ```
4. Add your environment variables (`BOT_TOKEN`, `SUPER_ADMIN_ID`, `DATABASE_URL`, `STORAGE_CHANNEL_ID`, `NOTIFICATION_GROUP_IDS`) under **Environment Variables**.
5. Click **Deploy Worker**.

---

## 📄 License

This project is licensed under the **MIT License** - free for personal, community, and commercial use.
