from fastapi import APIRouter

from app.api.v1.models import router as models_router
from app.api.v1.projects import router as projects_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.dataset_versions import router as dataset_versions_router
from app.api.v1.dataset_case import router as dataset_cases_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.evaluation_results import router as evaluation_results_router
from app.api.v1.evaluators.evaluators import router as evaluators_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(projects_router)
api_router.include_router(models_router)
api_router.include_router(datasets_router)
api_router.include_router(dataset_versions_router)
api_router.include_router(dataset_cases_router)
api_router.include_router(evaluation_router)
api_router.include_router(evaluation_results_router)
api_router.include_router(evaluators_router)
