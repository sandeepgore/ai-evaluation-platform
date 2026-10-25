from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user.user import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = decode_access_token(credentials.credentials) if credentials else None
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive account", headers={"WWW-Authenticate": "Bearer"})
    return user


async def enforce_role_access(request: Request, user: User = Depends(get_current_user)) -> User:
    if user.role not in {"admin", "dev", "user"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown account role")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if user.role == "user":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read-only access")
        if request.url.path.startswith("/api/v1/organizations") and user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required")
    return user
