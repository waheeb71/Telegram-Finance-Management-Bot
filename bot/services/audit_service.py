from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import AuditLog
from bot.core.logger import logger


class AuditService:
    @staticmethod
    async def log_action(
        session: AsyncSession,
        action: str,  # CREATE, UPDATE, DELETE
        entity_type: str,  # INCOME, EXPENSE, STUDENT, SPONSOR, USER
        entity_id: Optional[int],
        performed_by_user_id: int,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by_user_id=performed_by_user_id,
            old_values=old_values,
            new_values=new_values,
            notes=notes
        )
        session.add(audit_entry)
        await session.flush()
        logger.info(f"AuditLog created: [{action}] {entity_type} ID:{entity_id} by User:{performed_by_user_id}")
        return audit_entry
