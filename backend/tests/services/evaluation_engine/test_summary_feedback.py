from types import SimpleNamespace

from app.services.evaluation_engine.summary import (
    EvaluationRunSummaryService,
)


def make_result(*, feedback=None):
    return SimpleNamespace(feedback=feedback)


class TestEvaluationRunSummaryFeedback:
    # ------------------------------------------------------------------
    # Empty state
    # ------------------------------------------------------------------

    def test_empty_metrics_returns_default_feedback(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={},
            completed_results=[],
        )

        assert (
            result["overall"]
            == "Poor overall evaluation performance requiring significant improvement."
        )

        assert result["strengths"] == ["No major metric strengths were identified."]

        assert result["weaknesses"] == ["No major metric weaknesses were identified."]

        assert result["recommendations"] == [
            "Continue monitoring evaluation metrics across future runs."
        ]

        assert result["evaluator_feedback"] == []

    # ------------------------------------------------------------------
    # Relevance
    # ------------------------------------------------------------------

    def test_high_relevance_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"relevance": 0.9},
            completed_results=[],
        )

        assert "High relevance to the evaluation context." in result["strengths"]

    def test_medium_relevance_is_weakness(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"relevance": 0.6},
            completed_results=[],
        )

        assert "Relevance is acceptable but has room for improvement." in result["weaknesses"]

        assert (
            "Keep responses more directly aligned with the question and supporting context."
            in result["recommendations"]
        )

    def test_low_relevance_is_weakness(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"relevance": 0.4},
            completed_results=[],
        )

        assert any("Low relevance indicates" in item for item in result["weaknesses"])

        assert any("Improve response relevance" in item for item in result["recommendations"])

    # ------------------------------------------------------------------
    # Faithfulness
    # ------------------------------------------------------------------

    def test_high_faithfulness_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"faithfulness": 0.9},
            completed_results=[],
        )

        assert any("Strong faithfulness" in item for item in result["strengths"])

    def test_medium_faithfulness_is_weakness(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"faithfulness": 0.75},
            completed_results=[],
        )

        assert "Faithfulness is acceptable but could be improved." in result["weaknesses"]

    def test_low_faithfulness_generates_recommendation(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"faithfulness": 0.6},
            completed_results=[],
        )

        assert any("Faithfulness can be improved" in item for item in result["weaknesses"])

        assert any("Improve grounding" in item for item in result["recommendations"])

    # ------------------------------------------------------------------
    # F1
    # ------------------------------------------------------------------

    def test_high_f1_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"f1": 0.9},
            completed_results=[],
        )

        assert any("High F1" in item for item in result["strengths"])

    def test_medium_f1_is_weakness(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"f1": 0.6},
            completed_results=[],
        )

        assert "F1 shows moderate alignment with reference answers." in result["weaknesses"]

    def test_low_f1_generates_recommendation(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"f1": 0.3},
            completed_results=[],
        )

        assert any("Low F1" in item for item in result["weaknesses"])

        assert any(
            "Improve alignment with expected answers" in item for item in result["recommendations"]
        )

    # ------------------------------------------------------------------
    # Exact Match
    # ------------------------------------------------------------------

    def test_high_exact_match_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"exact_match": 0.9},
            completed_results=[],
        )

        assert any("High exact-match" in item for item in result["strengths"])

    def test_low_exact_match_is_weakness(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"exact_match": 0.4},
            completed_results=[],
        )

        assert any("Low exact-match" in item for item in result["weaknesses"])

    # ------------------------------------------------------------------
    # Contains
    # ------------------------------------------------------------------

    def test_high_contains_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"contains": 0.9},
            completed_results=[],
        )

        assert "Responses generally contain the expected answer content." in result["strengths"]

    def test_low_contains_generates_recommendation(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"contains": 0.4},
            completed_results=[],
        )

        assert "Responses frequently omit expected answer content." in result["weaknesses"]

        assert any(
            "Ensure responses contain the key information" in item
            for item in result["recommendations"]
        )

    # ------------------------------------------------------------------
    # LLM Judge
    # ------------------------------------------------------------------

    def test_high_llm_judge_is_strength(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.9},
            completed_results=[],
        )

        assert any("LLM judge evaluation indicates strong" in item for item in result["strengths"])

    def test_medium_llm_judge_generates_recommendation(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.64},
            completed_results=[],
        )

        assert (
            "LLM judge evaluation indicates acceptable but improvable response quality."
            in result["weaknesses"]
        )

        assert any("Review judge feedback" in item for item in result["recommendations"])

    def test_low_llm_judge_generates_recommendation(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.4},
            completed_results=[],
        )

        assert any("significant quality issues" in item for item in result["weaknesses"])

        assert any("Review judge feedback" in item for item in result["recommendations"])

    # ------------------------------------------------------------------
    # Overall score
    # ------------------------------------------------------------------

    def test_strong_overall_performance(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={
                "relevance": 0.9,
                "faithfulness": 0.9,
            },
            completed_results=[],
        )

        assert result["overall"] == "Strong overall evaluation performance."

    def test_moderate_overall_performance(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={
                "relevance": 0.7,
                "faithfulness": 0.6,
            },
            completed_results=[],
        )

        assert (
            result["overall"]
            == "Moderate overall evaluation performance with some areas for improvement."
        )

    def test_below_average_overall_performance(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={
                "relevance": 0.5,
                "faithfulness": 0.3,
            },
            completed_results=[],
        )

        assert (
            result["overall"]
            == "Below-average evaluation performance with several areas requiring improvement."
        )

    def test_poor_overall_performance(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={
                "relevance": 0.2,
                "faithfulness": 0.3,
            },
            completed_results=[],
        )

        assert (
            result["overall"]
            == "Poor overall evaluation performance requiring significant improvement."
        )

    # ------------------------------------------------------------------
    # Evaluator feedback
    # ------------------------------------------------------------------

    def test_case_level_evaluator_feedback_is_collected(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.7},
            completed_results=[
                make_result(feedback="llm_judge: response lacks completeness"),
                make_result(feedback="llm_judge: response is relevant"),
            ],
        )

        assert result["evaluator_feedback"] == [
            "llm_judge: response lacks completeness",
            "llm_judge: response is relevant",
        ]

    def test_empty_case_level_feedback_is_ignored(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.7},
            completed_results=[
                make_result(feedback=None),
                make_result(feedback=""),
                make_result(feedback="   "),
                make_result(feedback="llm_judge: useful feedback"),
            ],
        )

        assert result["evaluator_feedback"] == ["llm_judge: useful feedback"]

    def test_evaluator_feedback_is_limited_to_ten_items(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={"llm_judge": 0.7},
            completed_results=[make_result(feedback=f"feedback {i}") for i in range(15)],
        )

        assert len(result["evaluator_feedback"]) == 10
        assert result["evaluator_feedback"] == [f"feedback {i}" for i in range(10)]

    # ------------------------------------------------------------------
    # Multiple metrics
    # ------------------------------------------------------------------

    def test_multiple_metrics_generate_combined_feedback(self):
        result = EvaluationRunSummaryService._build_feedback(
            metrics={
                "relevance": 0.9,
                "faithfulness": 0.6,
                "f1": 0.3,
                "llm_judge": 0.9,
            },
            completed_results=[make_result(feedback="llm_judge: response needs more context")],
        )

        assert "High relevance to the evaluation context." in result["strengths"]

        assert any("Strong faithfulness" not in item for item in result["strengths"])

        assert any("Faithfulness can be improved" in item for item in result["weaknesses"])

        assert any("Low F1" in item for item in result["weaknesses"])

        assert any("LLM judge evaluation indicates strong" in item for item in result["strengths"])

        assert result["evaluator_feedback"] == ["llm_judge: response needs more context"]
