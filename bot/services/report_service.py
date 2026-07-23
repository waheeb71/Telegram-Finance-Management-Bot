from datetime import datetime, date, time
from typing import Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Income, Expense, Student, Sponsor, StudentStatus
from bot.services.finance_service import FinanceService
from bot.services.student_service import StudentService
from bot.services.sponsor_service import SponsorService


class ReportService:
    @staticmethod
    async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
        fin_summary = await FinanceService.get_financial_summary(session)
        student_stats = await StudentService.get_student_stats(session)
        top_sponsor = await SponsorService.get_top_sponsor(session)

        # Today's date calculations
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)

        # Month's date calculations
        first_day_of_month = datetime(date.today().year, date.today().month, 1)

        # Today's Income
        today_inc_res = await session.execute(
            select(func.coalesce(func.sum(Income.amount), 0.0)).where(
                and_(Income.date >= today_start, Income.date <= today_end)
            )
        )
        today_income = float(today_inc_res.scalar_one())

        # Today's Expense
        today_exp_res = await session.execute(
            select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                and_(Expense.date >= today_start, Expense.date <= today_end)
            )
        )
        today_expenses = float(today_exp_res.scalar_one())

        # Monthly Income
        month_inc_res = await session.execute(
            select(func.coalesce(func.sum(Income.amount), 0.0)).where(
                Income.date >= first_day_of_month
            )
        )
        monthly_income = float(month_inc_res.scalar_one())

        return {
            "total_income": fin_summary["total_income"],
            "total_expenses": fin_summary["total_expenses"],
            "current_balance": fin_summary["current_balance"],
            "total_students": student_stats["total_count"],
            "paid_students": student_stats["paid_count"],
            "unpaid_students": student_stats["unpaid_count"],
            "total_student_remaining": student_stats["total_remaining"],
            "top_sponsor": top_sponsor.company_name if top_sponsor else "لا يوجد",
            "top_sponsor_amount": float(top_sponsor.amount) if top_sponsor else 0.0,
            "today_income": today_income,
            "today_expenses": today_expenses,
            "monthly_income": monthly_income
        }
