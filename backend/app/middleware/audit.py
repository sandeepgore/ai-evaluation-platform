import json
import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models import (
    Dataset,
    DatasetCase,
    DatasetVersion,
    EvaluationRun,
    Experiment,
    Model,
    Organization,
    Project,
    User,
)
from app.models.evaluation.evaluation_schedule import EvaluationSchedule

logger = logging.getLogger(__name__)
AUTH_EVENTS = {"/api/v1/auth/login": "auth.login", "/api/v1/auth/register": "auth.register"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
RESOURCE_MODELS = {
    "organizations": Organization,
    "projects": Project,
    "models": Model,
    "datasets": Dataset,
    "dataset-cases": DatasetCase,
    "dataset-versions": DatasetVersion,
    "evaluation-runs": EvaluationRun,
    "evaluation-schedules": EvaluationSchedule,
    "experiments": Experiment,
}
REFERENCE_MODELS = {
    "organization_id": Organization,
    "project_id": Project,
    "model_id": Model,
    "dataset_id": Dataset,
    "dataset_version_id": DatasetVersion,
    "dataset_case_id": DatasetCase,
    "experiment_id": Experiment,
    "user_id": User,
    "target_user_id": User,
}
SENSITIVE_KEYS = ("password", "secret", "token", "api_key", "authorization", "credential")
MAX_DETAIL_STRING = 300


def _safe_value(value, depth: int = 0):
    if depth > 3:
        return "…"
    if isinstance(value, dict):
        safe = {}
        for key, item in list(value.items())[:50]:
            key_text = str(key)
            safe[key_text] = "[redacted]" if any(term in key_text.lower() for term in SENSITIVE_KEYS) else _safe_value(item, depth + 1)
        return safe
    if isinstance(value, (list, tuple)):
        return [_safe_value(item, depth + 1) for item in value[:10]]
    if isinstance(value, (UUID, date, datetime)):
        return value.isoformat() if isinstance(value, (date, datetime)) else str(value)
    if isinstance(value, str):
        return value if len(value) <= MAX_DETAIL_STRING else value[:MAX_DETAIL_STRING] + "…"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:MAX_DETAIL_STRING]


def _entity_model(path: str):
    parts = [part for part in path.split("/") if part]
    if len(parts) < 3 or parts[:2] != ["api", "v1"]:
        return None, None, None
    resource = parts[2]
    # Dataset imports create versions; the URL is nested beneath the dataset.
    if resource == "datasets" and len(parts) >= 5 and parts[4] in {"import", "import-file"}:
        return DatasetVersion, None, "dataset version"
    model = RESOURCE_MODELS.get(resource)
    if model is None:
        return None, None, None
    entity_id = None
    if len(parts) >= 4:
        try:
            entity_id = UUID(parts[3])
        except ValueError:
            pass
    return model, entity_id, resource.replace("-", " ").rstrip("s")


def _model_snapshot(instance):
    if instance is None:
        return None
    values = {}
    for column in instance.__table__.columns:
        name = column.name
        value = getattr(instance, name, None)
        if any(term in name.lower() for term in SENSITIVE_KEYS):
            values[name] = "[redacted]"
        else:
            values[name] = _safe_value(value)
    return values


async def _replace_reference_ids(details: dict):
    snapshots = [details.get("created"), details.get("deleted")]
    changes = details.get("changes")
    has_references = any(
        isinstance(snapshot, dict) and any(field in snapshot for field in REFERENCE_MODELS)
        for snapshot in snapshots
    ) or isinstance(changes, dict) and any(field in changes for field in REFERENCE_MODELS) or any(
        field in details for field in REFERENCE_MODELS
    )
    if not has_references:
        return
    try:
        async with AsyncSessionLocal() as session:
            for field, model in REFERENCE_MODELS.items():
                value = details.get(field)
                try:
                    reference_id = UUID(str(value))
                except (TypeError, ValueError):
                    continue
                result = await session.execute(select(model).where(model.id == reference_id))
                instance = result.scalar_one_or_none()
                display_name = None
                if instance is not None:
                    display_name = getattr(instance, "name", None) or getattr(instance, "slug", None) or getattr(instance, "email", None)
                    if model is DatasetVersion:
                        dataset = await session.get(Dataset, instance.dataset_id)
                        display_name = f"{dataset.name if dataset else 'Dataset'} v{instance.version}"
                    elif model is DatasetCase:
                        display_name = f"Case {instance.position + 1}"
                details[field.removesuffix("_id") + "_name"] = display_name or "Unknown"
                details.pop(field, None)

            for snapshot_key in ("created", "deleted"):
                snapshot = details.get(snapshot_key)
                if not isinstance(snapshot, dict):
                    continue
                for field, model in REFERENCE_MODELS.items():
                    value = snapshot.get(field)
                    try:
                        reference_id = UUID(str(value))
                    except (TypeError, ValueError):
                        continue
                    result = await session.execute(select(model).where(model.id == reference_id))
                    instance = result.scalar_one_or_none()
                    if instance is None:
                        snapshot[field.removesuffix("_id") + "_name"] = "Unknown"
                        snapshot.pop(field, None)
                        continue
                    display_name = getattr(instance, "name", None) or getattr(instance, "slug", None) or getattr(instance, "email", None)
                    if model is DatasetVersion:
                        dataset = await session.get(Dataset, instance.dataset_id)
                        display_name = f"{dataset.name if dataset else 'Dataset'} v{instance.version}"
                    elif model is DatasetCase:
                        display_name = f"Case {instance.position + 1}"
                    if display_name:
                        snapshot[field.removesuffix("_id") + "_name"] = display_name
                    snapshot.pop(field, None)

            changes = details.get("changes")
            if isinstance(changes, dict):
                for field, model in REFERENCE_MODELS.items():
                    change = changes.get(field)
                    if not isinstance(change, dict):
                        continue
                    named_change = {}
                    for direction in ("from", "to"):
                        value = change.get(direction)
                        if value is None:
                            named_change[direction] = None
                            continue
                        try:
                            reference_id = UUID(str(value))
                        except (TypeError, ValueError):
                            named_change[direction] = value
                            continue
                        result = await session.execute(select(model).where(model.id == reference_id))
                        instance = result.scalar_one_or_none()
                        display_name = None
                        if instance is not None:
                            display_name = getattr(instance, "name", None) or getattr(instance, "slug", None) or getattr(instance, "email", None)
                            if model is DatasetVersion:
                                dataset = await session.get(Dataset, instance.dataset_id)
                                display_name = f"{dataset.name if dataset else 'Dataset'} v{instance.version}"
                            elif model is DatasetCase:
                                display_name = f"Case {instance.position + 1}"
                        named_change[direction] = display_name or "Unknown"
                    changes[field.removesuffix("_id")] = named_change
                    changes.pop(field, None)
    except Exception:
        logger.exception("Unable to resolve audit reference names")


def _display_entity_name(details: dict, context: dict) -> str | None:
    if details.get("entity_name"):
        return str(details["entity_name"])[:MAX_DETAIL_STRING]
    record = details.get("created") or details.get("deleted")
    if isinstance(record, dict):
        for field in ("name", "slug", "title", "filename"):
            if record.get(field):
                return str(record[field])[:MAX_DETAIL_STRING]
        if details.get("entity_type") == "dataset version" and record.get("version") is not None:
            dataset_name = context.get("dataset_name") or record.get("dataset_name") or "Dataset"
            return f"{dataset_name} v{record['version']}"
        if details.get("entity_type") == "dataset case" and record.get("position") is not None:
            return f"Case {record['position'] + 1}"
    changes = details.get("changes")
    if isinstance(changes, dict) and "name" in changes:
        return str(changes["name"].get("to") or changes["name"].get("from"))[:MAX_DETAIL_STRING]
    if details.get("entity_type") == "dataset version" and details.get("entity_version") is not None:
        return f"{context.get('dataset_name') or 'Dataset'} v{details['entity_version']}"
    return context.get("dataset_name")


async def _capture_before(path: str, method: str):
    if method not in {"PATCH", "PUT", "DELETE", "POST"}:
        return None
    model, entity_id, _ = _entity_model(path)
    if model is None or entity_id is None:
        return None
    # A POST to a nested action (finalize/execute/cancel) changes the addressed entity.
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(model).where(model.id == entity_id))
            return _model_snapshot(result.scalar_one_or_none())
    except Exception:
        logger.exception("Unable to capture audit before-state for %s", path)
        return None


async def _capture_json_response(response: Response):
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response, None
    try:
        body_iterator = getattr(response, "body_iterator", None)
        if body_iterator is None:
            body = getattr(response, "body", b"")
        else:
            body = b"".join([chunk async for chunk in body_iterator])
        payload = json.loads(body) if body else None
        replacement = Response(
            content=body,
            status_code=response.status_code,
            background=response.background,
        )
        replacement.raw_headers = response.raw_headers
        return replacement, payload
    except Exception:
        logger.exception("Unable to capture JSON response for audit logging")
        return response, None


def _audit_details(
    method: str,
    path: str,
    request_payload,
    response_payload,
    before,
    status_code: int,
):
    model, entity_id, entity_type = _entity_model(path)
    parts = [part for part in path.split("/") if part]
    tail = parts[4:] if len(parts) >= 5 else []
    operation = "create" if method == "POST" and entity_id is None else "update" if method in {"PATCH", "PUT"} else "delete" if method == "DELETE" else "update"
    if method == "POST" and entity_id is not None:
        operation = tail[-1] if tail else "update"
        if operation == "snapshots":
            operation = "create"
            entity_type = "experiment snapshot"

    after = _safe_value(response_payload) if isinstance(response_payload, dict) else None
    if operation in {"import", "import-file"}:
        operation = "create"
        entity_type = "dataset version"
    after = after if isinstance(after, dict) else None
    before = _safe_value(before) if before else None

    details = {"operation": operation, "entity_type": entity_type}
    details["outcome"] = "succeeded" if status_code < 400 else "failed"
    display_record = after or before
    if isinstance(display_record, dict):
        for field in ("name", "slug", "title", "filename"):
            if display_record.get(field):
                details["entity_name"] = str(display_record[field])[:MAX_DETAIL_STRING]
                break
        if entity_type == "dataset version" and display_record.get("version") is not None:
            details["entity_version"] = display_record["version"]
    if after and after.get("id"):
        details["entity_id"] = after["id"]
    elif entity_id:
        details["entity_id"] = str(entity_id)

    if status_code >= 400:
        return details
    if operation == "create" and after:
        details["created"] = after
    elif operation == "delete" and before:
        details["deleted"] = before
    elif operation in {"update", "execute", "cancel", "finalize"}:
        if before and after:
            changes = {
                field: {"from": before.get(field), "to": after.get(field)}
                for field in set(before) | set(after)
                if field in before and field in after
                and before.get(field) != after.get(field)
                and field not in {"updated_at", "created_at"}
            }
            if changes:
                details["changes"] = changes
        elif isinstance(request_payload, dict):
            details["changes"] = {
                key: {"to": _safe_value(value)}
                for key, value in request_payload.items()
                if not any(term in key.lower() for term in SENSITIVE_KEYS)
            }
    return details


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        method = request.method.upper()
        action = AUTH_EVENTS.get(path)
        should_log = path.startswith("/api/v1/") and (method in WRITE_METHODS or action is not None)
        if not should_log:
            return await call_next(request)

        change_details = None
        request_payload = None
        if method in WRITE_METHODS and "application/json" in request.headers.get("content-type", ""):
            body = await request.body()
            async def replay_body():
                return {"type": "http.request", "body": body, "more_body": False}

            request._receive = replay_body
            try:
                if body and len(body) <= 65536:
                    payload = json.loads(body)
                    if isinstance(payload, dict):
                        request_payload = payload
                        change_details = {"changed_fields": list(payload)[:50]}
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                change_details = None

        before = await _capture_before(path, method)
        status_code = 500
        response: Response | None = None
        response_payload = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response, response_payload = await _capture_json_response(response)
            return response
        finally:
            try:
                actor_id = getattr(request.state, "audit_actor_id", None)
                if actor_id is None:
                    authorization = request.headers.get("authorization", "")
                    if authorization.lower().startswith("bearer "):
                        actor_id = decode_access_token(authorization[7:].strip())
                if actor_id is not None and not isinstance(actor_id, UUID):
                    actor_id = UUID(str(actor_id))
                client = request.client
                audit_details = (
                    getattr(request.state, "audit_details", None)
                    or _audit_details(
                        method,
                        path,
                        request_payload,
                        response_payload,
                        before,
                        status_code,
                    )
                    or change_details
                )
                audit_context = getattr(request.state, "audit_context", None)
                if isinstance(audit_details, dict):
                    if isinstance(audit_context, dict):
                        audit_details.update(_safe_value(audit_context))
                    await _replace_reference_ids(audit_details)
                    display_name = _display_entity_name(
                        audit_details,
                        audit_context if isinstance(audit_context, dict) else {},
                    )
                    if display_name:
                        audit_details["entity_name"] = display_name
                entry = AuditLog(
                    actor_user_id=actor_id,
                    action=(action or f"{method.lower()} {path}")[:160],
                    resource=path[:500],
                    details=audit_details,
                    method=method,
                    status_code=status_code,
                    ip_address=client.host if client else None,
                    user_agent=request.headers.get("user-agent", "")[:500] or None,
                )
                async with AsyncSessionLocal() as session:
                    session.add(entry)
                    await session.commit()
            except Exception:
                # Audit storage failures must not turn a completed API request into a 500.
                logger.exception("Failed to persist audit event for %s %s", method, path)
