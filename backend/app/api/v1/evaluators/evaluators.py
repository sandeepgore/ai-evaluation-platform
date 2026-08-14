from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.evaluator.evaluator import (
    EvaluatorListResponse,
    EvaluatorResponse,
)
from app.services.evaluators.evaluator_service import EvaluatorService


router = APIRouter(
    prefix="/evaluators",
    tags=["Evaluators"],
)


@router.get(
    "",
    response_model=EvaluatorListResponse,
)
async def list_evaluators(
    category: str | None = Query(None),
    requires_reference: bool | None = Query(None),
    requires_context: bool | None = Query(None),
    requires_llm: bool | None = Query(None),
    applicable_to: str | None = Query(None),
    tag: str | None = Query(None),
) -> EvaluatorListResponse:
    """
    List all registered evaluators with optional metadata filters.
    """

    service = EvaluatorService()

    evaluators = service.list(
        category=category,
        requires_reference=requires_reference,
        requires_context=requires_context,
        requires_llm=requires_llm,
        applicable_to=applicable_to,
        tag=tag,
    )

    return EvaluatorListResponse(
        evaluators=[
            EvaluatorResponse(
                name=evaluator.name,
                category=evaluator.metadata.category,
                description=evaluator.metadata.description,
                requires_reference=evaluator.metadata.requires_reference,
                requires_context=evaluator.metadata.requires_context,
                requires_llm=evaluator.metadata.requires_llm,
                applicable_to=list(evaluator.metadata.applicable_to),
                tags=list(evaluator.metadata.tags),
            )
            for evaluator in evaluators
        ],
        total=len(evaluators),
    )


@router.get(
    "/{evaluator_name}",
    response_model=EvaluatorResponse,
)
async def get_evaluator(
    evaluator_name: str,
) -> EvaluatorResponse:
    """
    Get metadata for a specific evaluator.
    """

    service = EvaluatorService()

    try:
        evaluator = service.get(evaluator_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    metadata = evaluator.metadata

    return EvaluatorResponse(
        name=evaluator.name,
        category=metadata.category,
        description=metadata.description,
        requires_reference=metadata.requires_reference,
        requires_context=metadata.requires_context,
        requires_llm=metadata.requires_llm,
        applicable_to=list(metadata.applicable_to),
        tags=list(metadata.tags),
    )
