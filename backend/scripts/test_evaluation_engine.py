import asyncio
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.services.evaluation_engine import EvaluationEngine
from app.services.evaluators import create_default_registry
from app.services.model_gateway import MockModelProvider
from app.services.scoring import ScoringService

RUN_ID = UUID("f7ef0caf-3daa-4a84-810b-3753d47e76eb")


async def main():
    evaluator_registry = create_default_registry()

    print("Available evaluators:")
    print(evaluator_registry.list())

    async with AsyncSessionLocal() as db:
        engine = EvaluationEngine(
            db=db,
            model_gateway=MockModelProvider(),
            evaluator_registry=evaluator_registry,
            scoring_service=ScoringService(),
        )

        run = await engine.execute(RUN_ID)

        print()
        print("Evaluation execution completed")
        print(f"Run ID: {run.id}")
        print(f"Status: {run.status}")
        print(f"Total cases: {run.total_cases}")
        print(f"Completed cases: {run.completed_cases}")
        print(f"Failed cases: {run.failed_cases}")


if __name__ == "__main__":
    asyncio.run(main())