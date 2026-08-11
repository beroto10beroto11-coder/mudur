"""
FastAPI dependency functions for authentication and authorization.
"""
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Dependency: returns the authenticated user from JWT token."""
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise UnauthorizedError("Token içinde kullanıcı bilgisi bulunamadı.")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedError("Geçersiz token içeriği.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("Kullanıcı bulunamadı.")

    if not user.is_active:
        raise UnauthorizedError("Kullanıcı hesabı devre dışı bırakılmış.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """
    Dependency factory: ensures the current user has one of the required global roles.
    Usage: Depends(require_role(UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN))
    """
    async def _check(current_user: CurrentUser) -> User:
        if current_user.global_role not in roles:
            raise ForbiddenError(
                f"Bu işlem için yetkiniz yok. Gerekli roller: "
                f"{', '.join(r.value for r in roles)}"
            )
        return current_user

    return _check


def require_super_admin(current_user: CurrentUser) -> User:
    """Dependency: requires SUPER_ADMIN role."""
    if current_user.global_role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Bu işlem yalnızca sistem yöneticileri tarafından yapılabilir.")
    return current_user


SuperAdmin = Annotated[User, Depends(require_super_admin)]


async def get_school_user(
    school_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> tuple[User, str]:
    """
    Dependency: ensures the current user has access to the given school.
    Returns (user, role_in_school).
    SUPER_ADMIN bypasses the school membership check.
    """
    if current_user.global_role == UserRole.SUPER_ADMIN:
        return current_user, UserRole.SUPER_ADMIN.value

    # Check if user belongs to this school
    from sqlalchemy import text
    result = await db.execute(
        text(
            "SELECT role FROM user_schools WHERE user_id = :uid AND school_id = :sid"
        ),
        {"uid": current_user.id, "sid": school_id},
    )
    row = result.fetchone()

    if not row:
        raise ForbiddenError("Bu okula erişim yetkiniz yok.")

    return current_user, row[0]


def require_school_role(*allowed_roles: str):
    """
    Dependency factory: ensures user has one of the given roles in a school.
    Requires school_id path parameter.
    """
    async def _check(
        school_id: int,
        current_user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        if current_user.global_role == UserRole.SUPER_ADMIN:
            return current_user

        from sqlalchemy import text
        result = await db.execute(
            text(
                "SELECT role FROM user_schools WHERE user_id = :uid AND school_id = :sid"
            ),
            {"uid": current_user.id, "sid": school_id},
        )
        row = result.fetchone()

        if not row:
            raise ForbiddenError("Bu okula erişim yetkiniz yok.")

        if row[0] not in [r for r in allowed_roles]:
            raise ForbiddenError(
                f"Bu işlem için yetkiniz yok. Gerekli roller: {', '.join(allowed_roles)}"
            )

        return current_user

    return _check
