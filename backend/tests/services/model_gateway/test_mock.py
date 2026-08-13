import pytest

from app.schemas.model_gateway.batch_response import BatchModelResponse
from app.services.model_gateway.mock import MockModelProvider


@pytest.mark.asyncio
async def test_mock_generate():
    gateway = MockModelProvider()

    response = await gateway.generate(
        prompt="What is RAG?",
    )

    assert response.output == "Mock response: What is RAG?"
    assert response.input_tokens == 3
    assert response.output_tokens == 5
    assert response.total_tokens == 8
    assert response.trace["provider"] == "mock"


@pytest.mark.asyncio
async def test_mock_generate_batch():
    gateway = MockModelProvider()

    prompts = [
        "What is RAG?",
        "What is an LLM?",
        "What is evaluation?",
    ]

    responses = await gateway.generate_batch(
        prompts=prompts,
    )

    assert len(responses) == 3

    assert all(isinstance(response, BatchModelResponse) for response in responses)

    assert responses[0].index == 0
    assert responses[0].response is not None
    assert responses[0].error is None
    assert responses[0].response.output == "Mock response: What is RAG?"

    assert responses[1].index == 1
    assert responses[1].response is not None
    assert responses[1].error is None
    assert responses[1].response.output == "Mock response: What is an LLM?"

    assert responses[2].index == 2
    assert responses[2].response is not None
    assert responses[2].error is None
    assert responses[2].response.output == "Mock response: What is evaluation?"


@pytest.mark.asyncio
async def test_mock_generate_batch_preserves_order():
    gateway = MockModelProvider()

    prompts = [
        "first",
        "second",
        "third",
    ]

    responses = await gateway.generate_batch(
        prompts=prompts,
    )

    assert [response.index for response in responses] == [0, 1, 2]

    assert [
        response.response.output for response in responses if response.response is not None
    ] == [
        "Mock response: first",
        "Mock response: second",
        "Mock response: third",
    ]


@pytest.mark.asyncio
async def test_mock_generate_batch_empty():
    gateway = MockModelProvider()

    responses = await gateway.generate_batch(
        prompts=[],
    )

    assert responses == []
