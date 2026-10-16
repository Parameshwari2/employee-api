from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        # nobody can be their own manager
        CheckConstraint("manager_id <> id", name="not_own_manager"),
        # fast search by name
        Index("ix_employees_last_first_name", "last_name", "first_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hire_date: Mapped[date]
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), index=True
    )
    manager_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True
    )

    department: Mapped["Department"] = relationship(back_populates="employees")
    role: Mapped["Role"] = relationship(back_populates="employees")

    # self-reference: many employees -> one manager
    manager: Mapped[Optional["Employee"]] = relationship(
        back_populates="direct_reports", remote_side="Employee.id"
    )
    direct_reports: Mapped[list["Employee"]] = relationship(back_populates="manager")

    @validates("email")
    def _normalise_email(self, key: str, value: str) -> str:
        return value.strip().lower()