"""
User, Role, Permission models with RBAC support.
"""
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Enum,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, PyEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    VICE_PRINCIPAL = "VICE_PRINCIPAL"
    TEACHER = "TEACHER"
    VIEWER = "VIEWER"


# Many-to-many: User ↔ School (a user can belong to multiple schools)
user_school_association = Table(
    "user_schools",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True),
    Column("role", Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.VIEWER),
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(500), nullable=False)

    # Global role — SUPER_ADMIN is global, others are per-school
    global_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.VIEWER,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # If user is linked to a teacher record
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    schools: Mapped[list["School"]] = relationship(  # type: ignore[name-defined]
        "School",
        secondary=user_school_association,
        back_populates="users",
        lazy="select",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="user", lazy="select"
    )

    __table_args__ = (
        Index("ix_users_global_role", "global_role"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
    )


# Import School here to avoid circular imports at model level
from app.models.school import School  # noqa: E402
from app.models.audit import AuditLog  # noqa: E402
