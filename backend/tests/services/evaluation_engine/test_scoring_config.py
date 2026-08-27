import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.evaluation_engine.scoring_config import (
    ScoringConfigurationService,
)


def make_run(configuration=None, *, is_active=True):
    return SimpleNamespace(
        id=uuid4(),
        configuration=configuration,
        is_active=is_active,
    )


def make_db(run=None):
    db = MagicMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = run

    db.execute = AsyncMock(return_value=execute_result)

    return db


def make_redis():
    redis = MagicMock()
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()

    return redis


class TestScoringConfigurationService:
    def test_cache_key_contains_evaluation_run_id(self):
        evaluation_run_id = uuid4()

        key = ScoringConfigurationService._cache_key(evaluation_run_id)

        assert key == (f"evaluation:run:scoring-config:{evaluation_run_id}")

    def test_extract_configuration_returns_scoring_configuration(self):
        run = make_run(
            {
                "execution_mode": "batch",
                "scoring": {
                    "strategy": "weighted",
                    "weights": {
                        "exact_match": 0.5,
                        "f1": 0.5,
                    },
                },
            }
        )

        result = ScoringConfigurationService._extract_configuration(run)

        assert result == {
            "strategy": "weighted",
            "weights": {
                "exact_match": 0.5,
                "f1": 0.5,
            },
        }

    def test_extract_configuration_returns_empty_dict_when_configuration_missing(self):
        run = make_run(None)

        result = ScoringConfigurationService._extract_configuration(run)

        assert result == {}

    def test_extract_configuration_returns_empty_dict_for_invalid_configuration(self):
        run = make_run("invalid configuration")

        result = ScoringConfigurationService._extract_configuration(run)

        assert result == {}

    def test_extract_configuration_returns_empty_dict_for_invalid_scoring_configuration(self):
        run = make_run(
            {
                "scoring": "invalid",
            }
        )

        result = ScoringConfigurationService._extract_configuration(run)

        assert result == {}

    @pytest.mark.asyncio
    async def test_database_configuration_retrieval(self):
        evaluation_run_id = uuid4()

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                    "weights": {
                        "exact_match": 0.5,
                        "f1": 0.5,
                    },
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService()

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
            "weights": {
                "exact_match": 0.5,
                "f1": 0.5,
            },
        }

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_redis_cache_hit_does_not_query_database(self):
        evaluation_run_id = uuid4()

        redis = make_redis()

        redis.get.return_value = json.dumps(
            {
                "strategy": "weighted",
                "weights": {
                    "exact_match": 0.5,
                    "f1": 0.5,
                },
            }
        )

        db = make_db()

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
            "weights": {
                "exact_match": 0.5,
                "f1": 0.5,
            },
        }

        redis.get.assert_awaited_once()
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_redis_bytes_cache_hit_is_decoded(self):
        evaluation_run_id = uuid4()

        redis = make_redis()

        redis.get.return_value = json.dumps(
            {
                "strategy": "weighted",
            }
        ).encode("utf-8")

        db = make_db()

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_redis_cache_miss_queries_database(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.get.return_value = None

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        redis.get.assert_awaited_once()
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_database_configuration_is_populated_into_redis(self):
        evaluation_run_id = uuid4()

        redis = make_redis()

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                    "weights": {
                        "exact_match": 0.5,
                        "f1": 0.5,
                    },
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(
            redis=redis,
            ttl_seconds=1800,
        )

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
            "weights": {
                "exact_match": 0.5,
                "f1": 0.5,
            },
        }

        redis.set.assert_awaited_once_with(
            f"evaluation:run:scoring-config:{evaluation_run_id}",
            json.dumps(
                {
                    "strategy": "weighted",
                    "weights": {
                        "exact_match": 0.5,
                        "f1": 0.5,
                    },
                }
            ),
            ex=1800,
        )

    @pytest.mark.asyncio
    async def test_missing_evaluation_run_raises_value_error(self):
        evaluation_run_id = uuid4()

        db = make_db(None)

        service = ScoringConfigurationService()

        with pytest.raises(
            ValueError,
            match="Evaluation run not found",
        ):
            await service.get(
                db,
                evaluation_run_id,
            )

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_scoring_configuration_returns_empty_dict(self):
        evaluation_run_id = uuid4()

        run = make_run(
            {
                "execution_mode": "batch",
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService()

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_invalid_scoring_configuration_returns_empty_dict(self):
        evaluation_run_id = uuid4()

        run = make_run(
            {
                "scoring": "invalid",
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService()

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_redis_get_failure_falls_back_to_database(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.get.side_effect = RuntimeError("Redis unavailable")

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        redis.get.assert_awaited_once()
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_cached_json_falls_back_to_database(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.get.return_value = "not valid json"

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cached_non_dict_configuration_falls_back_to_database(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.get.return_value = json.dumps(["invalid", "configuration"])

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_redis_set_failure_does_not_fail_request(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.get.return_value = None
        redis.set.side_effect = RuntimeError("Redis unavailable")

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=redis)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        redis.set.assert_awaited_once()
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_redis_disabled_uses_database(self):
        evaluation_run_id = uuid4()

        run = make_run(
            {
                "scoring": {
                    "strategy": "weighted",
                }
            }
        )

        db = make_db(run)

        service = ScoringConfigurationService(redis=None)

        result = await service.get(
            db,
            evaluation_run_id,
        )

        assert result == {
            "strategy": "weighted",
        }

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalidate_deletes_cached_configuration(self):
        evaluation_run_id = uuid4()

        redis = make_redis()

        service = ScoringConfigurationService(redis=redis)

        await service.invalidate(evaluation_run_id)

        redis.delete.assert_awaited_once_with(f"evaluation:run:scoring-config:{evaluation_run_id}")

    @pytest.mark.asyncio
    async def test_invalidate_with_redis_disabled_does_nothing(self):
        service = ScoringConfigurationService(redis=None)

        await service.invalidate(uuid4())

    @pytest.mark.asyncio
    async def test_redis_delete_failure_does_not_fail_invalidation(self):
        evaluation_run_id = uuid4()

        redis = make_redis()
        redis.delete.side_effect = RuntimeError("Redis unavailable")

        service = ScoringConfigurationService(redis=redis)

        await service.invalidate(evaluation_run_id)

        redis.delete.assert_awaited_once()
