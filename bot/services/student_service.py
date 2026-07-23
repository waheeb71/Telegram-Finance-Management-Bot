from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Student, StudentStatus, Income, IncomeCategory
from bot.services.audit_service import AuditService
from bot.services.finance_service import FinanceService


class StudentService:
    @staticmethod
    async def add_student(
        session: AsyncSession,
        name: str,
        student_code: str,
        phone: Optional[str],
        total_required: float,
        performed_by_user_id: int
    ) -> Student:
        student = Student(
            name=name,
            student_code=student_code,
            phone=phone,
            total_required=total_required,
            total_paid=0.0,
            remaining_amount=total_required,
            installments_count=0,
            status=StudentStatus.UNPAID
        )
        session.add(student)
        await session.flush()

        await AuditService.log_action(
            session=session,
            action="CREATE",
            entity_type="STUDENT",
            entity_id=student.id,
            performed_by_user_id=performed_by_user_id,
            new_values={
                "name": name,
                "student_code": student_code,
                "phone": phone,
                "total_required": total_required
            }
        )
        return student

    @staticmethod
    async def record_payment(
        session: AsyncSession,
        student_id: int,
        amount: float,
        recipient_name: str,
        recorded_by_user_id: int,
        notes: Optional[str] = None,
        receipt_photo_file_id: Optional[str] = None,
        receipt_photo_message_id: Optional[int] = None
    ) -> tuple[Student, Income]:
        res = await session.execute(select(Student).where(Student.id == student_id))
        student = res.scalar_one_or_none()
        if not student:
            raise ValueError("Student not found.")

        old_paid = float(student.total_paid)
        old_remaining = float(student.remaining_amount)

        # Update student balances
        student.total_paid = float(student.total_paid) + amount
        student.remaining_amount = max(0.0, float(student.total_required) - float(student.total_paid))
        student.installments_count += 1
        student.last_payment_date = datetime.utcnow()

        if student.remaining_amount <= 0:
            student.status = StudentStatus.PAID
        else:
            student.status = StudentStatus.PARTIAL

        # Register Income record
        income = await FinanceService.add_income(
            session=session,
            category=IncomeCategory.STUDENT_FEE,
            amount=amount,
            recipient_name=recipient_name,
            recorded_by_user_id=recorded_by_user_id,
            student_id=student.id,
            notes=f"رسوم طالب: {student.name} ({student.student_code}) - {notes or ''}",
            receipt_photo_file_id=receipt_photo_file_id,
            receipt_photo_message_id=receipt_photo_message_id
        )

        await AuditService.log_action(
            session=session,
            action="UPDATE",
            entity_type="STUDENT",
            entity_id=student.id,
            performed_by_user_id=recorded_by_user_id,
            old_values={"total_paid": old_paid, "remaining_amount": old_remaining},
            new_values={"total_paid": float(student.total_paid), "remaining_amount": float(student.remaining_amount)}
        )

        return student, income

    @staticmethod
    async def get_all_students(session: AsyncSession) -> List[Student]:
        res = await session.execute(select(Student).order_by(Student.name))
        return list(res.scalars().all())

    @staticmethod
    async def find_students(session: AsyncSession, term: str) -> List[Student]:
        res = await session.execute(
            select(Student).where(
                or_(
                    Student.name.ilike(f"%{term}%"),
                    Student.student_code.ilike(f"%{term}%"),
                    Student.phone.ilike(f"%{term}%")
                )
            )
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_student_stats(session: AsyncSession) -> Dict[str, Any]:
        students = await StudentService.get_all_students(session)
        paid_students = [s for s in students if s.status == StudentStatus.PAID]
        unpaid_students = [s for s in students if s.status != StudentStatus.PAID]
        total_remaining = sum(float(s.remaining_amount) for s in students)

        return {
            "total_count": len(students),
            "paid_count": len(paid_students),
            "unpaid_count": len(unpaid_students),
            "total_remaining": total_remaining,
            "paid_list": paid_students,
            "unpaid_list": unpaid_students
        }
