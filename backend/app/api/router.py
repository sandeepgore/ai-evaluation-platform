from fastapi import APIRouter, Depends

from app.api.v1.auth import router as auth_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.middleware.auth import enforce_role_access

from app.api.v1.dataset_case import router as dataset_cases_router
from app.api.v1.dataset_versions import router as dataset_versions_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.evaluation.schedules import router as evaluation_schedules_router
from app.api.v1.evaluation.logs import (
    run_logs_router,
    scheduler_logs_router,
)
from app.api.v1.evaluation_results import router as evaluation_results_router
from app.api.v1.evaluators.evaluators import router as evaluators_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.models import router as models_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(audit_logs_router)

for protected_router in (
    organizations_router, projects_router, models_router, datasets_router,
    dataset_versions_router, dataset_cases_router, evaluation_router,
    evaluation_schedules_router, run_logs_router, scheduler_logs_router,
    evaluation_results_router, evaluators_router, experiments_router,
):
    api_router.include_router(protected_router, dependencies=[Depends(enforce_role_access)])
