from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.audit_log import AuditLog
from app.models.user.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

SCREEN_RESOURCES = {
    "organizations": ("/api/v1/organizations",),
    "projects": ("/api/v1/projects",),
    "models": ("/api/v1/models",),
    "datasets": ("/api/v1/datasets",),
    "dataset_cases": ("/api/v1/dataset-cases",),
    "dataset_versions": (
        "/api/v1/dataset-versions",
        "/api/v1/datasets/%/import",
        "/api/v1/datasets/%/import-file",
    ),
    "evaluations": ("/api/v1/evaluation-runs", "/api/v1/evaluation-schedules"),
    "experiments": ("/api/v1/experiments",),
}


@router.get("/activity")
async def list_screen_activity(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    screen: str = Query(...),
    limit: int = Query(default=12, ge=1, le=50),
) -> list[dict]:
    prefixes = SCREEN_RESOURCES.get(screen)
    if prefixes is None:
        raise HTTPException(status_code=400, detail="Unknown activity screen")
    rows = await db.execute(
        select(AuditLog, User.full_name, User.email)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .where(or_(*[AuditLog.resource.like(f"{pattern}%") for pattern in prefixes]))
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(log.id),
            "actor_name": name,
            "actor_email": email,
            "action": log.action,
            "resource": log.resource,
            "details": log.details,
            "method": log.method,
            "status_code": log.status_code,
            "created_at": log.created_at,
        }
        for log, name, email in rows.all()
    ]


@router.get("")
async def list_audit_logs(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    rows = await db.execute(
        select(AuditLog, User.full_name, User.email)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        {
            "id": str(log.id),
            "actor_user_id": str(log.actor_user_id) if log.actor_user_id else None,
            "actor_name": name,
            "actor_email": email,
            "action": log.action,
            "resource": log.resource,
            "details": log.details,
            "method": log.method,
            "status_code": log.status_code,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at,
        }
        for log, name, email in rows.all()
    ]
