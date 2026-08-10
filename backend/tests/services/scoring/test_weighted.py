import pytest

from app.services.scoring import ScoringService


def test_weighted_score_calculation():
    service = ScoringService()

    result = service.calculate(
        scores={
            "exact_match": {"score": 1.0},
            "contains": {"score": 0.5},
            "f1": {"score": 0.25},
        },
        configuration={
            "weights": {
                "exact_match": 0.2,
                "contains": 0.3,
                "f1": 0.5,
            }
        },
    )

    assert result.score == pytest.approx(0.475)

    assert result.metadata["strategy"] == "weighted"

    assert result.metadata["weights"] == {
        "exact_match": pytest.approx(0.2),
        "contains": pytest.approx(0.3),
        "f1": pytest.approx(0.5),
    }


def test_default_weights_are_equal():
    service = ScoringService()

    result = service.calculate(
        scores={
            "exact_match": {"score": 1.0},
            "contains": {"score": 0.5},
            "f1": {"score": 0.0},
        },
    )

    assert result.score == pytest.approx(0.5)

    assert result.metadata["weights"] == {
        "exact_match": pytest.approx(1 / 3),
        "contains": pytest.approx(1 / 3),
        "f1": pytest.approx(1 / 3),
    }


def test_score_above_one_is_rejected():
    service = ScoringService()

    with pytest.raises(
        ValueError,
        match="must be between 0.0 and 1.0",
    ):
        service.calculate(
            scores={
                "f1": {"score": 1.5},
            }
        )


def test_negative_score_is_rejected():
    service = ScoringService()

    with pytest.raises(
        ValueError,
        match="must be between 0.0 and 1.0",
    ):
        service.calculate(
            scores={
                "f1": {"score": -0.1},
            }
        )


def test_overall_score_cannot_be_an_input():
    service = ScoringService()

    with pytest.raises(
        ValueError,
        match="'overall' must not be included",
    ):
        service.calculate(
            scores={
                "f1": {"score": 0.5},
                "overall": {"score": 1.0},
            }
        )


def test_negative_weight_is_rejected():
    service = ScoringService()

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        service.calculate(
            scores={
                "f1": {"score": 0.5},
            },
            configuration={
                "weights": {
                    "f1": -1.0,
                }
            },
        )


def test_all_zero_weights_are_rejected():
    service = ScoringService()

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        service.calculate(
            scores={
                "exact_match": {"score": 0.5},
                "f1": {"score": 0.5},
            },
            configuration={
                "weights": {
                    "exact_match": 0.0,
                    "f1": 0.0,
                }
            },
        )


def test_unknown_weights_do_not_affect_score():
    service = ScoringService()

    result = service.calculate(
        scores={
            "f1": {"score": 0.5},
        },
        configuration={
            "weights": {
                "f1": 1.0,
                "unknown_evaluator": 100.0,
            }
        },
    )

    assert result.score == pytest.approx(0.5)

    assert result.metadata["weights"] == {
        "f1": pytest.approx(1.0),
    }