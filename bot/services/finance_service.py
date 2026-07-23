from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Income, Expense, IncomeCategory, User
from bot.services.audit_service import AuditService


class FinanceService:
    @staticmethod
    async def get_financial_summary(session: AsyncSession) -> Dict[str, float]:
        """Calculates total income, total expenses, and current net balance."""
        income_res = await session.execute(select(func.coalesce(func.sum(Income.amount), 0.0)))
        total_income = float(income_res.scalar_one())

        expense_res = await session.execute(select(func.coalesce(func.sum(Expense.amount), 0.0)))
        total_expenses = float(expense_res.scalar_one())

        current_balance = total_income - total_expenses
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "current_balance": current_balance
        }

    @staticmethod
    async def generate_op_number(session: AsyncSession, prefix: str) -> str:
        """Generates sequential operation numbers e.g. INC-0001 or EXP-0001."""
        if prefix == "INC":
            res = await session.execute(select(func.count(Income.id)))
            count = res.scalar_one() + 1
            return f"INC-{count:04d}"
        else:
            res = await session.execute(select(func.count(Expense.id)))
            count = res.scalar_one() + 1
            return f"EXP-{count:04d}"

    @staticmethod
    async def add_income(
        session: AsyncSession,
        category: IncomeCategory,
        amount: float,
        recipient_name: str,
        recorded_by_user_id: int,
        student_id: Optional[int] = None,
        sponsor_id: Optional[int] = None,
        notes: Optional[str] = None,
        receipt_photo_file_id: Optional[str] = None,
        receipt_photo_message_id: Optional[int] = None
    ) -> Income:
        op_num = await FinanceService.generate_op_number(session, "INC")
        income = Income(
            op_number=op_num,
            category=category,
            amount=amount,
            date=datetime.utcnow(),
            recipient_name=recipient_name,
            recorded_by_user_id=recorded_by_user_id,
            student_id=student_id,
            sponsor_id=sponsor_id,
            notes=notes,
            receipt_photo_file_id=receipt_photo_file_id,
            receipt_photo_message_id=receipt_photo_message_id
        )
        session.add(income)
        await session.flush()

        await AuditService.log_action(
            session=session,
            action="CREATE",
            entity_type="INCOME",
            entity_id=income.id,
            performed_by_user_id=recorded_by_user_id,
            new_values={
                "op_number": op_num,
                "category": category.value,
                "amount": amount,
                "recipient_name": recipient_name,
                "notes": notes
            }
        )
        return income

    @staticmethod
    async def add_expense(
        session: AsyncSession,
        amount: float,
        reason: str,
        beneficiary_name: str,
        processed_by_user_id: int,
        notes: Optional[str] = None,
        invoice_photo_file_id: Optional[str] = None,
        invoice_photo_message_id: Optional[int] = None
    ) -> Expense:
        op_num = await FinanceService.generate_op_number(session, "EXP")
        expense = Expense(
            op_number=op_num,
            date=datetime.utcnow(),
            amount=amount,
            reason=reason,
            beneficiary_name=beneficiary_name,
            processed_by_user_id=processed_by_user_id,
            notes=notes,
            invoice_photo_file_id=invoice_photo_file_id,
            invoice_photo_message_id=invoice_photo_message_id
        )
        session.add(expense)
        await session.flush()

        await AuditService.log_action(
            session=session,
            action="CREATE",
            entity_type="EXPENSE",
            entity_id=expense.id,
            performed_by_user_id=processed_by_user_id,
            new_values={
                "op_number": op_num,
                "amount": amount,
                "reason": reason,
                "beneficiary_name": beneficiary_name,
                "notes": notes
            }
        )
        return expense

    @staticmethod
    async def get_latest_incomes(session: AsyncSession, limit: int = 10) -> List[Income]:
        res = await session.execute(
            select(Income).order_by(desc(Income.created_at)).limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_latest_expenses(session: AsyncSession, limit: int = 10) -> List[Expense]:
        res = await session.execute(
            select(Expense).order_by(desc(Expense.created_at)).limit(limit)
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_last_operation(session: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves the last income or expense created by a specific user or globally."""
        inc_res = await session.execute(
            select(Income).where(Income.recorded_by_user_id == user_id).order_by(desc(Income.created_at)).limit(1)
        )
        last_inc = inc_res.scalar_one_or_none()

        exp_res = await session.execute(
            select(Expense).where(Expense.processed_by_user_id == user_id).order_by(desc(Expense.created_at)).limit(1)
        )
        last_exp = exp_res.scalar_one_or_none()

        if last_inc and last_exp:
            if last_inc.created_at > last_exp.created_at:
                return {"type": "INCOME", "obj": last_inc}
            else:
                return {"type": "EXPENSE", "obj": last_exp}
        elif last_inc:
            return {"type": "INCOME", "obj": last_inc}
        elif last_exp:
            return {"type": "EXPENSE", "obj": last_exp}
        return None

    @staticmethod
    async def delete_income(session: AsyncSession, income_id: int, user_id: int) -> bool:
        res = await session.execute(select(Income).where(Income.id == income_id))
        income = res.scalar_one_or_none()
        if not income:
            return False

        old_vals = {
            "op_number": income.op_number,
            "amount": float(income.amount),
            "category": income.category.value
        }
        await session.delete(income)
        await session.flush()

        await AuditService.log_action(
            session=session,
            action="DELETE",
            entity_type="INCOME",
            entity_id=income_id,
            performed_by_user_id=user_id,
            old_values=old_vals
        )
        return True

    @staticmethod
    async def delete_expense(session: AsyncSession, expense_id: int, user_id: int) -> bool:
        res = await session.execute(select(Expense).where(Expense.id == expense_id))
        expense = res.scalar_one_or_none()
        if not expense:
            return False

        old_vals = {
            "op_number": expense.op_number,
            "amount": float(expense.amount),
            "reason": expense.reason
        }
        await session.delete(expense)
        await session.flush()

        await AuditService.log_action(
            session=session,
            action="DELETE",
            entity_type="EXPENSE",
            entity_id=expense_id,
            performed_by_user_id=user_id,
            old_values=old_vals
        )
        return True
