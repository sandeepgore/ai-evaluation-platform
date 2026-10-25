from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(admin|dev|user)$")


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="user", pattern="^(admin|dev|user)$")


def user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: Credentials, request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    email = str(data.email).lower()
    if await db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    # Bootstrap the first account as admin. Further accounts receive the least privilege.
    role = "admin" if await db.scalar(select(func.count()).select_from(User)) == 0 else "user"
    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=role,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    await db.refresh(user)
    request.state.audit_actor_id = user.id
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "user": user_payload(user),
    }


@router.post("/login")
async def login(data: Credentials, request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(func.lower(User.email) == str(data.email).lower()))
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled")
    request.state.audit_actor_id = user.id
    return {
        "access_token": create_access_token(user.id, user.role),
        "token_type": "bearer",
        "user": user_payload(user),
    }


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict:
    return user_payload(user)


@router.get("/users")
async def list_users(
    _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    users = (await db.scalars(select(User).order_by(User.email))).all()
    return [user_payload(user) for user in users]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: AdminUserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    email = str(data.email).strip().lower()
    full_name = data.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=422, detail="Name is required")
    if await db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    await db.refresh(user)
    request.state.audit_actor_id = admin.id
    request.state.audit_details = {
        "operation": "create",
        "entity_type": "user",
        "entity_name": user.full_name or user.email,
        "created": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        },
    }
    return user_payload(user)


@router.patch("/users/{user_id}/role")
async def update_role(
    user_id: UUID,
    data: RoleUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id and data.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own administrator role")
    if user.role == "admin" and data.role != "admin":
        admin_count = await db.scalar(select(func.count()).select_from(User).where(User.role == "admin"))
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="At least one administrator must remain")
    request.state.audit_details = {
        "target_user_id": str(user.id),
        "changes": {"role": {"from": user.role, "to": data.role}},
    }
    user.role = data.role
    await db.commit()
    await db.refresh(user)
    return user_payload(user)
