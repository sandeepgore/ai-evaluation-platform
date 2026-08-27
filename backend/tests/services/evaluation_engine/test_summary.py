from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.evaluation_engine.summary import EvaluationRunSummaryService


def create_run(model_id=None, duration_ms=10_000):
    return SimpleNamespace(
        id=uuid4(),
        model_id=model_id or uuid4(),
        duration_ms=duration_ms,
        is_active=True,
    )


def create_model(
    model_id=None,
    name="Llama 3.2 3B Local",
    provider="ollama",
    model_identifier="llama3.2:3b",
    input_price_per_million=0.50,
    output_price_per_million=1.50,
    pricing_currency="USD",
):
    return SimpleNamespace(
        id=model_id or uuid4(),
        name=name,
        provider=provider,
        model_identifier=model_identifier,
        input_price_per_million=input_price_per_million,
        output_price_per_million=output_price_per_million,
        pricing_currency=pricing_currency,
        is_active=True,
    )


def create_result(
    *,
    status="completed",
    input_tokens=1_000,
    output_tokens=2_000,
    total_tokens=3_000,
    latency_ms=1_000,
    score=0.8,
):
    return SimpleNamespace(
        status=status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        scores={
            "overall": {
                "score": score,
            }
        },
        is_active=True,
    )


def create_db(run, model, results):
    run_result = MagicMock()
    run_result.scalar_one_or_none.return_value = run

    model_result = MagicMock()
    model_result.scalar_one_or_none.return_value = model

    results_result = MagicMock()
    results_result.scalars.return_value.all.return_value = results

    db = AsyncMock()
    db.execute.side_effect = [
        run_result,
        model_result,
        results_result,
    ]

    return db


@pytest.mark.asyncio
async def test_summary_uses_model_specific_pricing():
    model_id = uuid4()

    run = create_run(model_id=model_id)

    model = create_model(
        model_id=model_id,
        input_price_per_million=0.50,
        output_price_per_million=1.50,
    )

    results = [
        create_result(
            input_tokens=1_000,
            output_tokens=2_000,
            total_tokens=3_000,
        )
    ]

    db = create_db(run, model, results)

    summary = await EvaluationRunSummaryService.calculate(db, run.id)

    cost = summary["performance"]["cost"]

    assert cost["input_cost"] == pytest.approx(0.0005)
    assert cost["output_cost"] == pytest.approx(0.003)
    assert cost["total_cost"] == pytest.approx(0.0035)
    assert cost["currency"] == "USD"


@pytest.mark.asyncio
async def test_summary_uses_different_pricing_for_different_models():
    run_id = uuid4()

    run = create_run()

    llama = create_model(
        name="Llama 3.2 3B Local",
        model_identifier="llama3.2:3b",
        input_price_per_million=0.50,
        output_price_per_million=1.50,
    )

    qwen = create_model(
        name="Qwen 2.5 3B Local",
        model_identifier="qwen2.5:3b",
        input_price_per_million=0.40,
        output_price_per_million=1.20,
    )

    results = [
        create_result(
            input_tokens=1_000,
            output_tokens=2_000,
            total_tokens=3_000,
        )
    ]

    llama_db = create_db(run, llama, results)
    llama_summary = await EvaluationRunSummaryService.calculate(
        llama_db,
        run_id,
    )

    qwen_db = create_db(run, qwen, results)
    qwen_summary = await EvaluationRunSummaryService.calculate(
        qwen_db,
        run_id,
    )

    llama_cost = llama_summary["performance"]["cost"]["total_cost"]
    qwen_cost = qwen_summary["performance"]["cost"]["total_cost"]

    assert llama_cost == pytest.approx(0.0035)
    assert qwen_cost == pytest.approx(0.0028)
    assert llama_cost != qwen_cost


@pytest.mark.asyncio
async def test_summary_returns_model_information():
    model_id = uuid4()

    run = create_run(model_id=model_id)

    model = create_model(
        model_id=model_id,
        name="Llama 3.2 3B Local",
        provider="ollama",
        model_identifier="llama3.2:3b",
    )

    db = create_db(
        run,
        model,
        [create_result()],
    )

    summary = await EvaluationRunSummaryService.calculate(db, run.id)

    assert summary["model"]["id"] == model.id
    assert summary["model"]["name"] == "Llama 3.2 3B Local"
    assert summary["model"]["provider"] == "ollama"
    assert summary["model"]["model_identifier"] == "llama3.2:3b"


@pytest.mark.asyncio
async def test_summary_falls_back_to_zero_cost_when_model_is_missing():
    run = create_run()

    results = [
        create_result(
            input_tokens=1_000,
            output_tokens=2_000,
            total_tokens=3_000,
        )
    ]

    db = create_db(run, None, results)

    summary = await EvaluationRunSummaryService.calculate(db, run.id)

    assert summary["model"] is None

    cost = summary["performance"]["cost"]

    assert cost["input_cost"] == pytest.approx(0.0)
    assert cost["output_cost"] == pytest.approx(0.0)
    assert cost["total_cost"] == pytest.approx(0.0)
    assert cost["currency"] == "USD"


@pytest.mark.asyncio
async def test_summary_returns_model_and_zero_cost_for_zero_tokens():
    run = create_run()

    model = create_model(
        input_price_per_million=0.50,
        output_price_per_million=1.50,
    )

    results = [
        create_result(
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
        )
    ]

    db = create_db(run, model, results)

    summary = await EvaluationRunSummaryService.calculate(db, run.id)

    assert summary["model"]["name"] == "Llama 3.2 3B Local"

    cost = summary["performance"]["cost"]

    assert cost["input_cost"] == pytest.approx(0.0)
    assert cost["output_cost"] == pytest.approx(0.0)
    assert cost["total_cost"] == pytest.approx(0.0)
    assert cost["currency"] == "USD"
