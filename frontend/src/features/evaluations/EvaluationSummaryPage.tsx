import {
  ArrowBackOutlined,
  AssessmentOutlined,
  ErrorOutlineOutlined,
  RefreshOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";

import { useEvaluationRunSummary } from "./hooks";

function formatDuration(durationMs?: number | null): string {
  if (durationMs == null || !Number.isFinite(durationMs)) {
    return "—";
  }

  if (durationMs < 1000) {
    return `${Math.round(durationMs)} ms`;
  }

  const totalSeconds = Math.floor(durationMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }

  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }

  return `${(durationMs / 1000).toFixed(2)}s`;
}

function formatNumber(value?: number | null): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }

  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatScore(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatMetricLabel(metric: string): string {
  return metric
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatCost(amount?: number | null, currency?: string | null): string {
  if (amount == null || !Number.isFinite(amount)) {
    return "—";
  }

  if (currency) {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        maximumFractionDigits: 6,
      }).format(amount);
    } catch {
      return `${formatNumber(amount)} ${currency}`;
    }
  }

  return formatNumber(amount);
}

function ScoreCard({ label, value }: { label: string; value: string }) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        height: "100%",
      }}
    >
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        {label}
      </Typography>

      <Typography
        variant="h5"
        sx={{
          mt: 1,
          fontWeight: 700,
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </Typography>
    </Paper>
  );
}

function FeedbackSection({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: string[];
  emptyMessage: string;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        height: "100%",
      }}
    >
      <Typography variant="subtitle1" sx={{ fontWeight: 700 }} gutterBottom>
        {title}
      </Typography>

      {items.length === 0 ? (
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          {emptyMessage}
        </Typography>
      ) : (
        <Stack spacing={1}>
          {items.map((item, index) => (
            <Box
              key={`${title}-${index}`}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1,
              }}
            >
              <Box
                component="span"
                sx={{
                  width: 6,
                  height: 6,
                  mt: 0.9,
                  flexShrink: 0,
                  borderRadius: "50%",
                  bgcolor: "text.secondary",
                }}
              />

              <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
                {item}
              </Typography>
            </Box>
          ))}
        </Stack>
      )}
    </Paper>
  );
}

export function EvaluationSummaryPage() {
  const { evaluationId } = useParams<{ evaluationId: string }>();
  const navigate = useNavigate();

  const {
    data: summary,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useEvaluationRunSummary(evaluationId);

  if (!evaluationId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Evaluation ID is missing from the URL.</Alert>

        <Button
          startIcon={<ArrowBackOutlined />}
          onClick={() => navigate("/evaluations")}
          sx={{ mt: 2 }}
        >
          Back to evaluations
        </Button>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box
        sx={{
          minHeight: 300,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Stack spacing={2} sx={{ alignItems: "center" }}>
          <CircularProgress />

          <Typography sx={{ color: "text.secondary" }}>
            Loading evaluation summary…
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (isError || !summary) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : "Unable to load the evaluation summary.";

    return (
      <Box sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Button
            startIcon={<ArrowBackOutlined />}
            onClick={() => navigate(`/evaluations/${evaluationId}`)}
            sx={{ alignSelf: "flex-start" }}
          >
            Back to evaluation
          </Button>

          <Alert
            severity="error"
            action={
              <Button
                color="inherit"
                size="small"
                startIcon={<RefreshOutlined />}
                onClick={() => void refetch()}
              >
                Retry
              </Button>
            }
          >
            {errorMessage}
          </Alert>
        </Stack>
      </Box>
    );
  }

  const performance = summary.performance;
  const feedback = summary.feedback;
  const metrics = Object.entries(summary.metrics ?? {});
  const currency = performance.cost?.currency;

  const totalCases =
    summary.total_results ??
    performance.total_results ??
    performance.completed_cases +
      performance.failed_cases +
      performance.not_applicable_cases;

  const completedCases = summary.completed_cases;
  const failedCases = summary.failed_cases;
  const notApplicableCases = summary.not_applicable_cases;

  const completedPercent =
    totalCases > 0 ? (completedCases / totalCases) * 100 : 0;
  const failedPercent = totalCases > 0 ? (failedCases / totalCases) * 100 : 0;
  const notApplicablePercent =
    totalCases > 0 ? (notApplicableCases / totalCases) * 100 : 0;

  return (
    <Box
      sx={{
        p: { xs: 2, md: 3 },
        maxWidth: 1400,
        mx: "auto",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <Stack spacing={3}>
        <Stack
          spacing={2}
          sx={{
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
            alignItems: { xs: "stretch", sm: "center" },
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Button
              startIcon={<ArrowBackOutlined />}
              onClick={() => navigate(`/evaluations/${evaluationId}`)}
              sx={{ mb: 1, ml: -1 }}
            >
              Back to evaluation
            </Button>

            <Stack
              spacing={1}
              sx={{
                flexDirection: "row",
                alignItems: "center",
              }}
            >
              <AssessmentOutlined color="primary" />

              <Typography
                variant="h4"
                sx={{
                  fontWeight: 700,
                  overflowWrap: "anywhere",
                }}
              >
                Evaluation Summary
              </Typography>
            </Stack>

            <Typography
              sx={{
                mt: 1,
                color: "text.secondary",
                overflowWrap: "anywhere",
              }}
            >
              Evaluation ID: {evaluationId}
            </Typography>
          </Box>

          <Stack
            direction="row"
            spacing={1}
            useFlexGap
            sx={{
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            <Button
              variant="outlined"
              startIcon={<RefreshOutlined />}
              disabled={isFetching}
              onClick={() => void refetch()}
            >
              Refresh
            </Button>

            <Button
              variant="contained"
              onClick={() => navigate(`/evaluations/${evaluationId}/results`)}
            >
              View individual results
            </Button>
          </Stack>
        </Stack>

        {summary.model && (
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="overline" sx={{ color: "text.secondary" }}>
              Evaluated model
            </Typography>

            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                overflowWrap: "anywhere",
              }}
            >
              {summary.model.name}
            </Typography>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{
                flexWrap: "wrap",
                mt: 1,
              }}
            >
              <Chip label={summary.model.provider} size="small" />

              <Chip
                label={summary.model.model_identifier}
                size="small"
                variant="outlined"
                sx={{ maxWidth: "100%" }}
              />
            </Stack>
          </Paper>
        )}

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, minmax(0, 1fr))",
              lg: "repeat(4, minmax(0, 1fr))",
            },
            gap: 2,
          }}
        >
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              height: "100%",
              borderColor: "primary.main",
            }}
          >
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Overall score
            </Typography>

            <Typography
              variant="h4"
              sx={{
                mt: 1,
                fontWeight: 800,
                color: "primary.main",
              }}
            >
              {formatScore(summary.overall_score)}
            </Typography>

            <LinearProgress
              variant="determinate"
              value={Math.min(100, Math.max(0, summary.overall_score * 100))}
              sx={{
                mt: 2,
                height: 6,
                borderRadius: 3,
              }}
            />
          </Paper>

          <ScoreCard label="Total results" value={formatNumber(totalCases)} />

          <ScoreCard
            label="Duration"
            value={formatDuration(performance.duration_ms)}
          />

          <ScoreCard
            label="Total cost"
            value={formatCost(performance.cost?.total_cost, currency)}
          />
        </Box>

        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Case outcomes
          </Typography>

          <Typography
            variant="body2"
            sx={{
              mt: 0.5,
              color: "text.secondary",
            }}
          >
            Not-applicable cases are kept separate from failed cases.
          </Typography>

          <Box
            sx={{
              display: "flex",
              width: "100%",
              height: 12,
              overflow: "hidden",
              borderRadius: 2,
              bgcolor: "action.hover",
              mt: 2,
            }}
          >
            {completedPercent > 0 && (
              <Box
                sx={{
                  width: `${completedPercent}%`,
                  bgcolor: "success.main",
                }}
              />
            )}

            {failedPercent > 0 && (
              <Box
                sx={{
                  width: `${failedPercent}%`,
                  bgcolor: "error.main",
                }}
              />
            )}

            {notApplicablePercent > 0 && (
              <Box
                sx={{
                  width: `${notApplicablePercent}%`,
                  bgcolor: "grey.500",
                }}
              />
            )}
          </Box>

          <Stack
            direction="row"
            spacing={2}
            useFlexGap
            sx={{
              flexWrap: "wrap",
              mt: 2,
            }}
          >
            <Chip
              color="success"
              variant="outlined"
              label={`Completed: ${completedCases}`}
            />

            <Chip
              color="error"
              variant="outlined"
              label={`Failed: ${failedCases}`}
            />

            <Chip
              variant="outlined"
              label={`Not applicable: ${notApplicableCases}`}
            />
          </Stack>

          {failedCases > 0 && (
            <Alert
              severity="warning"
              icon={<ErrorOutlineOutlined />}
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() =>
                    navigate(`/evaluations/${evaluationId}/results`)
                  }
                >
                  Inspect failures
                </Button>
              }
              sx={{ mt: 2 }}
            >
              This run contains failed cases. Review individual results to
              inspect error messages and outputs.
            </Alert>
          )}
        </Paper>

        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Metric scores
          </Typography>

          <Typography
            variant="body2"
            sx={{
              mt: 0.5,
              color: "text.secondary",
            }}
          >
            Scores are displayed as percentages, assuming the API returns
            normalized values between 0 and 1.
          </Typography>

          {metrics.length === 0 ? (
            <Typography
              sx={{
                mt: 2,
                color: "text.secondary",
              }}
            >
              No metric scores are available for this run.
            </Typography>
          ) : (
            <Stack spacing={2} sx={{ mt: 2 }}>
              {metrics.map(([metric, value]) => {
                const isValid =
                  typeof value === "number" && Number.isFinite(value);

                return (
                  <Box key={metric}>
                    <Stack
                      sx={{
                        mb: 0.75,
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                      spacing={2}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 600,
                          overflowWrap: "anywhere",
                        }}
                      >
                        {formatMetricLabel(metric)}
                      </Typography>

                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {isValid ? formatScore(value) : "—"}
                      </Typography>
                    </Stack>

                    <LinearProgress
                      variant="determinate"
                      value={
                        isValid ? Math.min(100, Math.max(0, value * 100)) : 0
                      }
                      sx={{
                        height: 7,
                        borderRadius: 4,
                      }}
                    />
                  </Box>
                );
              })}
            </Stack>
          )}
        </Paper>

        <Box>
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700,
              mb: 2,
            }}
          >
            Evaluation feedback
          </Typography>

          <Paper
            variant="outlined"
            sx={{
              p: 2,
              mb: 2,
            }}
          >
            <Typography
              variant="subtitle1"
              sx={{ fontWeight: 700 }}
              gutterBottom
            >
              Overall assessment
            </Typography>

            <Typography
              sx={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
              }}
            >
              {feedback?.overall || "No overall assessment is available."}
            </Typography>
          </Paper>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "1fr",
                md: "repeat(2, minmax(0, 1fr))",
              },
              gap: 2,
            }}
          >
            <FeedbackSection
              title="Strengths"
              items={feedback?.strengths ?? []}
              emptyMessage="No strengths were reported."
            />

            <FeedbackSection
              title="Weaknesses"
              items={feedback?.weaknesses ?? []}
              emptyMessage="No weaknesses were reported."
            />

            <FeedbackSection
              title="Patterns"
              items={feedback?.patterns ?? []}
              emptyMessage="No patterns were reported."
            />

            <FeedbackSection
              title="Recommendations"
              items={feedback?.recommendations ?? []}
              emptyMessage="No recommendations were reported."
            />
          </Box>

          {(feedback?.evaluator_feedback?.length ?? 0) > 0 && (
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                mt: 2,
              }}
            >
              <Typography
                variant="subtitle1"
                sx={{ fontWeight: 700 }}
                gutterBottom
              >
                Evaluator feedback
              </Typography>

              <Stack spacing={1}>
                {feedback.evaluator_feedback?.map((item, index) => (
                  <Typography
                    key={`evaluator-feedback-${index}`}
                    variant="body2"
                    sx={{ overflowWrap: "anywhere" }}
                  >
                    {item}
                  </Typography>
                ))}
              </Stack>
            </Paper>
          )}
        </Box>

        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700 }} gutterBottom>
            Performance and usage
          </Typography>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "1fr",
                sm: "repeat(2, minmax(0, 1fr))",
                lg: "repeat(3, minmax(0, 1fr))",
              },
              gap: 2,
            }}
          >
            <ScoreCard
              label="Total model latency"
              value={formatDuration(performance.total_model_latency_ms)}
            />

            <ScoreCard
              label="Average model latency"
              value={formatDuration(performance.avg_model_latency_ms)}
            />

            <ScoreCard
              label="P95 latency"
              value={formatDuration(performance.p95_model_latency_ms)}
            />

            <ScoreCard
              label="P99 latency"
              value={formatDuration(performance.p99_model_latency_ms)}
            />

            <ScoreCard
              label="Input tokens"
              value={formatNumber(performance.input_tokens)}
            />

            <ScoreCard
              label="Output tokens"
              value={formatNumber(performance.output_tokens)}
            />

            <ScoreCard
              label="Total tokens"
              value={formatNumber(performance.total_tokens)}
            />

            <ScoreCard
              label="Throughput"
              value={
                performance.throughput_cases_per_second == null
                  ? "—"
                  : `${formatNumber(
                      performance.throughput_cases_per_second,
                    )} cases/s`
              }
            />

            <ScoreCard
              label="Input cost"
              value={formatCost(performance.cost?.input_cost, currency)}
            />

            <ScoreCard
              label="Output cost"
              value={formatCost(performance.cost?.output_cost, currency)}
            />
          </Box>
        </Paper>

        <Divider />

        <Stack
          sx={{
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
          }}
          spacing={2}
        >
          <Button
            variant="outlined"
            startIcon={<ArrowBackOutlined />}
            onClick={() => navigate(`/evaluations/${evaluationId}`)}
          >
            Back to run details
          </Button>

          <Button
            variant="contained"
            onClick={() => navigate(`/evaluations/${evaluationId}/results`)}
          >
            View individual results
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
}
