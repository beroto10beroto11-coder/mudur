from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.jwt import create_access_token, create_refresh_token, get_token_expiry_datetime, hash_refresh_token
from app.auth.password import verify_password
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, NotFoundError
from app.models.user import RefreshToken
from app.repositories.user import UserRepository, RefreshTokenRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("E-posta veya şifre hatalı.")

        if not user.is_active:
            raise UnauthorizedError("Hesabınız pasife alınmış.")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.global_role.value},
        )
        raw_refresh, refresh_hash = create_refresh_token()
        expiry = get_token_expiry_datetime().isoformat()

        refresh_obj = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expiry,
        )
        await self.refresh_repo.create(refresh_obj)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_token(self, raw_refresh_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(raw_refresh_token)
        db_token = await self.refresh_repo.get_by_hash(token_hash)
        if not db_token:
            raise UnauthorizedError("Geçersiz veya iptal edilmiş refresh token.")

        user = await self.user_repo.get_by_id(db_token.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Kullanıcı aktif değil.")

        # Revoke old refresh token
        db_token.is_revoked = True
        await self.db.commit()

        # Create new tokens
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "role": user.global_role.value},
        )
        new_raw_refresh, new_refresh_hash = create_refresh_token()
        expiry = get_token_expiry_datetime().isoformat()

        new_refresh_obj = RefreshToken(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=expiry,
        )
        await self.refresh_repo.create(new_refresh_obj)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )
