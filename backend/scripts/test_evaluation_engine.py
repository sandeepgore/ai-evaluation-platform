import asyncio
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.services.evaluation_engine import EvaluationEngine
from app.services.model_gateway import MockModelProvider
from backend.app.services.evaluators.exact_match import ExactMatchEvaluator


RUN_ID = UUID("530a3848-9929-4ab9-9792-e30d0a8e1e8b")


async def main():
    async with AsyncSessionLocal() as db:
        engine = EvaluationEngine(
            db=db,
            model_gateway=MockModelProvider(),
            evaluators=[
                ExactMatchEvaluator(),
            ],
        )

        run = await engine.execute(RUN_ID)

        print("Evaluation execution completed")
        print(f"Run ID: {run.id}")
        print(f"Status: {run.status}")
        print(f"Total cases: {run.total_cases}")
        print(f"Completed cases: {run.completed_cases}")
        print(f"Failed cases: {run.failed_cases}")


if __name__ == "__main__":
    asyncio.run(main())
