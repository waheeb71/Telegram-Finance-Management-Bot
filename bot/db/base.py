from bot.core.database import Base, engine
from bot.db.models import (
    User, Student, Sponsor, Income, Expense, AuditLog, Notification, Setting,
    UserRole, StudentStatus, SponsorshipType, IncomeCategory
)

async def init_models():
    """Create all database tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
