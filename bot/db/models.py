import enum
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Numeric, Text, Boolean, DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from bot.core.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    FINANCE_ADMIN = "FINANCE_ADMIN"
    RELATIONS_ADMIN = "RELATIONS_ADMIN"
    MEMBER = "MEMBER"


class StudentStatus(str, enum.Enum):
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    UNPAID = "UNPAID"


class SponsorshipType(str, enum.Enum):
    CASH = "CASH"
    IN_KIND = "IN_KIND"
    BANNER = "BANNER"
    PRINTING = "PRINTING"
    HALLS = "HALLS"
    HOSPITALITY = "HOSPITALITY"
    OTHER = "OTHER"


class IncomeCategory(str, enum.Enum):
    STUDENT_FEE = "STUDENT_FEE"
    SPONSOR = "SPONSOR"
    DONATION = "DONATION"
    CORPORATE_SUPPORT = "CORPORATE_SUPPORT"
    INSTITUTION_SUPPORT = "INSTITUTION_SUPPORT"
    OTHER = "OTHER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incomes = relationship("Income", back_populates="recorded_by_user")
    expenses = relationship("Expense", back_populates="processed_by_user")
    audit_logs = relationship("AuditLog", back_populates="performed_by_user")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    student_code = Column(String(50), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    total_required = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_paid = Column(Numeric(12, 2), default=0.00, nullable=False)
    remaining_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    installments_count = Column(Integer, default=0, nullable=False)
    last_payment_date = Column(DateTime, nullable=True)
    status = Column(Enum(StudentStatus, native_enum=False), default=StudentStatus.UNPAID, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incomes = relationship("Income", back_populates="student")


class Sponsor(Base):
    __tablename__ = "sponsors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    sponsorship_type = Column(Enum(SponsorshipType, native_enum=False), default=SponsorshipType.CASH, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incomes = relationship("Income", back_populates="sponsor")


class Income(Base):
    __tablename__ = "income"

    id = Column(Integer, primary_key=True, autoincrement=True)
    op_number = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(Enum(IncomeCategory, native_enum=False), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    recipient_name = Column(String(255), nullable=False)
    recorded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=True)
    notes = Column(Text, nullable=True)
    receipt_photo_file_id = Column(String(255), nullable=True)
    receipt_photo_message_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recorded_by_user = relationship("User", back_populates="incomes")
    student = relationship("Student", back_populates="incomes")
    sponsor = relationship("Sponsor", back_populates="incomes")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    op_number = Column(String(50), unique=True, nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    beneficiary_name = Column(String(255), nullable=False)
    processed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)
    invoice_photo_file_id = Column(String(255), nullable=True)
    invoice_photo_message_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    processed_by_user = relationship("User", back_populates="expenses")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    entity_type = Column(String(50), nullable=False)  # INCOME, EXPENSE, STUDENT, SPONSOR, USER
    entity_id = Column(Integer, nullable=True)
    performed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    performed_by_user = relationship("User", back_populates="audit_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    message_text = Column(Text, nullable=False)
    status = Column(String(50), default="SENT", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
