from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Sponsor, SponsorshipType, IncomeCategory, Income
from bot.services.audit_service import AuditService
from bot.services.finance_service import FinanceService


class SponsorService:
    @staticmethod
    async def add_sponsor(
        session: AsyncSession,
        company_name: str,
        contact_person: Optional[str],
        phone: Optional[str],
        amount: float,
        sponsorship_type: SponsorshipType,
        performed_by_user_id: int,
        notes: Optional[str] = None
    ) -> tuple[Sponsor, Optional[Income]]:
        sponsor = Sponsor(
            company_name=company_name,
            contact_person=contact_person,
            phone=phone,
            amount=amount,
            sponsorship_type=sponsorship_type,
            notes=notes
        )
        session.add(sponsor)
        await session.flush()

        income = None
        # If financial contribution, register as income
        if amount > 0:
            income = await FinanceService.add_income(
                session=session,
                category=IncomeCategory.SPONSOR,
                amount=amount,
                recipient_name=company_name,
                recorded_by_user_id=performed_by_user_id,
                sponsor_id=sponsor.id,
                notes=f"رعاية: {company_name} ({sponsorship_type.value}) - {notes or ''}"
            )

        await AuditService.log_action(
            session=session,
            action="CREATE",
            entity_type="SPONSOR",
            entity_id=sponsor.id,
            performed_by_user_id=performed_by_user_id,
            new_values={
                "company_name": company_name,
                "amount": amount,
                "sponsorship_type": sponsorship_type.value
            }
        )

        return sponsor, income

    @staticmethod
    async def get_all_sponsors(session: AsyncSession) -> List[Sponsor]:
        res = await session.execute(select(Sponsor).order_by(desc(Sponsor.amount)))
        return list(res.scalars().all())

    @staticmethod
    async def get_top_sponsor(session: AsyncSession) -> Optional[Sponsor]:
        res = await session.execute(select(Sponsor).order_by(desc(Sponsor.amount)).limit(1))
        return res.scalar_one_or_none()
