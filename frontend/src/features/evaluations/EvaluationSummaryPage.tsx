import {
  AssessmentOutlined,
  AutoAwesomeOutlined,
  CheckCircleOutlined,
  ErrorOutlineOutlined,
  InfoOutlined,
  LightbulbOutlined,
  RefreshOutlined,
  RuleOutlined,
  ThumbDownAltOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { StatusChip } from "../../components/common/StatusChip";

import { useEvaluationRun, useEvaluationRunSummary } from "./hooks";

const evaluationTypeDescriptions: Record<string, string> = {
  text: "Evaluate generated responses against expected answers.",
  rag: "Evaluate responses produced using retrieved context.",
  conversation: "Evaluate multi-turn conversational responses.",
  safety: "Evaluate safety-related behavior and guardrails.",
};

const sectionPaperSx = {
  p: { xs: 2, sm: 2.5 },
  borderRadius: 3,
  borderColor: "divider",
};

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

function formatMetricValue(value: number): string {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 4,
  }).format(value);
}

function formatMetricLabel(metric: string): string {
  return metric
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

interface MetricGuide {
  meaning: string;
  requiredData: string;
  example: string;
}

const metricGuides: Record<string, MetricGuide> = {
  exact_match: {
    meaning: "Checks whether the output exactly matches the expected answer.",
    requiredData: "Generated output and expected answer.",
    example: "Expected “Paris” and output “Paris” gives a match.",
  },
  contains: {
    meaning: "Checks whether the expected text appears in the output.",
    requiredData: "Generated output and expected text.",
    example: "Expected “Paris” matches output “The answer is Paris.”",
  },
  f1: {
    meaning:
      "Measures precision and recall overlap between generated and expected text.",
    requiredData: "Generated output and expected answer.",
    example:
      "More correct word overlap, with fewer extra or missing words, raises F1.",
  },
  bleu: {
    meaning: "Measures n-gram precision against a reference answer.",
    requiredData: "Generated output and reference answer.",
    example: "Matching phrases such as “blue sky” contribute to the score.",
  },
  rouge_l: {
    meaning:
      "Measures longest-common-subsequence overlap with a reference answer.",
    requiredData: "Generated output and reference answer.",
    example: "A longer shared word sequence produces more overlap.",
  },
  relevance: {
    meaning: "Evaluates how relevant the response is to the input or question.",
    requiredData: "Question or input and generated response.",
    example: "An answer about Paris is relevant to “What is France’s capital?”",
  },
  faithfulness: {
    meaning:
      "Evaluates whether a response is supported by the provided context.",
    requiredData: "Generated response and supporting context.",
    example: "Context says “Paris is in France”; that same claim is supported.",
  },
  llm_judge: {
    meaning:
      "Uses an LLM to assess output quality against configured criteria.",
    requiredData:
      "Generated output and configured judging criteria; input or context when required by the rubric.",
    example:
      "A rubric can ask a judge to check whether the answer is accurate and concise.",
  },
  context_precision: {
    meaning:
      "Checks whether relevant retrieved context chunks rank above irrelevant chunks.",
    requiredData:
      "Question, retrieved contexts, and ideally a reference answer or relevance labels.",
    example: "Relevant chunks ranked first produce higher context precision.",
  },
  context_recall: {
    meaning:
      "Checks whether retrieved context contains the information needed to answer the question.",
    requiredData: "Question, retrieved contexts, and reference answer.",
    example:
      "If an answer needs two facts and both appear in the retrieved context, recall is high.",
  },
  overall_score: {
    meaning:
      "A derived aggregate score, not an independent metric implementation.",
    requiredData:
      "Applicable case-level overall scores and the configured aggregation.",
    example:
      "The run score aggregates the overall scores from its applicable cases.",
  },
};

const performanceGuides: Record<string, MetricGuide> = {
  total_results: {
    meaning: "Total number of evaluation cases included in the run.",
    requiredData: "Completed, failed, and not-applicable case counts.",
    example:
      "8 completed plus 1 failed and 1 not applicable equals 10 results.",
  },
  duration_ms: {
    meaning: "Elapsed time for the evaluation run.",
    requiredData: "Run start and completion times, or a recorded duration.",
    example: "A run lasting 12,500 ms is displayed as 12.50 seconds.",
  },
  total_cost: {
    meaning: "Estimated total model cost for input and output tokens.",
    requiredData: "Input and output token usage, model prices, and currency.",
    example: "$0.10 input cost plus $0.20 output cost equals $0.30 total.",
  },
  total_model_latency_ms: {
    meaning:
      "Total time spent waiting for model responses across completed cases.",
    requiredData: "Model latency for each completed case.",
    example: "Case latencies of 120 ms and 280 ms add up to 400 ms.",
  },
  avg_model_latency_ms: {
    meaning: "Average model response time per completed case.",
    requiredData: "Model latency values and the number of completed cases.",
    example: "400 ms across 2 cases gives an average of 200 ms.",
  },
  p95_model_latency_ms: {
    meaning:
      "The latency at or below which 95% of measured model responses fall.",
    requiredData: "A set of model response latency values.",
    example:
      "A P95 of 800 ms means 95% of measured responses took 800 ms or less.",
  },
  p99_model_latency_ms: {
    meaning:
      "The latency at or below which 99% of measured model responses fall.",
    requiredData: "A set of model response latency values.",
    example:
      "A P99 of 1.2 s means 99% of measured responses took 1.2 s or less.",
  },
  input_tokens: {
    meaning: "Total tokens sent to the model across the run.",
    requiredData: "Input token usage reported for each model request.",
    example: "Requests using 100 and 150 input tokens total 250 input tokens.",
  },
  output_tokens: {
    meaning: "Total tokens generated by the model across the run.",
    requiredData: "Output token usage reported for each model response.",
    example: "Responses generating 40 and 60 tokens total 100 output tokens.",
  },
  total_tokens: {
    meaning: "Combined input and output tokens used across the run.",
    requiredData: "Input and output token usage.",
    example: "250 input tokens plus 100 output tokens equals 350 total tokens.",
  },
  throughput_cases_per_second: {
    meaning: "Completed cases per second over the evaluation run duration.",
    requiredData: "Completed case count and run duration.",
    example: "20 completed cases in 10 seconds equals 2 cases per second.",
  },
  input_cost: {
    meaning: "Estimated model cost for input tokens.",
    requiredData: "Input token usage, model input price, and pricing currency.",
    example: "At $1 per million input tokens, 100,000 tokens cost $0.10.",
  },
  output_cost: {
    meaning: "Estimated model cost for output tokens.",
    requiredData:
      "Output token usage, model output price, and pricing currency.",
    example: "At $2 per million output tokens, 100,000 tokens cost $0.20.",
  },
};

function MetricHelpDialog({
  label,
  guide,
}: {
  label: string;
  guide?: MetricGuide;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <IconButton size="small" aria-label={`Learn about ${label}`} title={`Learn about ${label}`} onClick={() => setOpen(true)}>
        <InfoOutlined fontSize="small" />
      </IconButton>
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>{label}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            What it measures
          </Typography>
          <Typography variant="body2">
            {guide?.meaning ??
              "Meaning depends on the evaluation configuration."}
          </Typography>
            </Box>
            <Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            Example
          </Typography>
          <Typography variant="body2">
            {guide?.example ??
              "The evaluator applies this metric to the configured input and output."}
          </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              <strong>Required data:</strong>{" "}
              {guide?.requiredData ?? "Depends on the evaluation configuration."}
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setOpen(false)}>Close</Button></DialogActions>
      </Dialog>
    </>
  );
}

function MetricScoreCard({
  metric,
  value,
  averageMetricValue,
  maxMetricMagnitude,
}: {
  metric: string;
  value: number;
  averageMetricValue: number;
  maxMetricMagnitude: number;
}) {
  const isValid = typeof value === "number" && Number.isFinite(value);
  const belowAverage = isValid && (isLowerBetterMetric(metric)
    ? value > averageMetricValue
    : value < averageMetricValue);

  return <Paper variant="outlined" sx={{ p: 1.75, minWidth: 0, bgcolor: "background.default" }}>
    <Stack spacing={1}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, overflowWrap: "anywhere" }}>{formatMetricLabel(metric)}</Typography>
        <MetricHelpDialog label={formatMetricLabel(metric)} guide={metricGuides[metric]} />
      </Stack>
      <Typography variant="h5" sx={{ fontWeight: 750, fontVariantNumeric: "tabular-nums", color: belowAverage ? "warning.main" : "success.main" }}>
        {isValid ? formatMetricValue(value) : "—"}
      </Typography>
      <LinearProgress aria-label={`${formatMetricLabel(metric)} relative magnitude`} variant="determinate"
        value={isValid && maxMetricMagnitude > 0 ? (Math.abs(value) / maxMetricMagnitude) * 100 : 0}
        color={belowAverage ? "warning" : "success"} sx={{ height: 7, borderRadius: 4 }} />
    </Stack>
  </Paper>;
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

function averageOf(values: Array<number | null | undefined>): number | null {
  const validValues = values.filter(
    (value): value is number => value != null && Number.isFinite(value),
  );

  return validValues.length
    ? validValues.reduce((total, value) => total + value, 0) /
        validValues.length
    : null;
}

function isAboveAverage(
  value: number | null | undefined,
  average: number | null,
): boolean {
  return value != null && average != null && value > average;
}

function isLowerBetterMetric(metric: string): boolean {
  return /latency|duration|response_time|cost|token|error_rate|failure_rate/i.test(metric);
}

function ScoreCard({
  label,
  value,
  help,
  belowAverage = false,
}: {
  label: string;
  value: string;
  help?: MetricGuide;
  belowAverage?: boolean;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        ...sectionPaperSx,
        height: "100%",
      }}
    >
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center" }}
      >
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          {label}
        </Typography>
        {help && <MetricHelpDialog label={label} guide={help} />}
      </Stack>

      <Typography
        variant="h5"
        sx={{
          mt: 1,
          fontWeight: 700,
          overflowWrap: "anywhere",
          color: belowAverage ? "warning.main" : "text.primary",
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
  icon,
  color,
}: {
  title: string;
  items: string[];
  emptyMessage: string;
  icon: ReactNode;
  color: string;
}) {
  return (
    <Paper
      variant="outlined"
      sx={{
        ...sectionPaperSx,
        height: "100%",
      }}
    >
      <Stack
        direction="row"
        spacing={1}
        sx={{ alignItems: "center", justifyContent: "space-between", mb: 1.5 }}
      >
        <Stack
          direction="row"
          spacing={1}
          sx={{ alignItems: "center", minWidth: 0 }}
        >
          <Box sx={{ display: "flex", color, flexShrink: 0 }}>{icon}</Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
        </Stack>
        <Chip size="small" label={items.length} variant="outlined" />
      </Stack>

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
                p: 1.25,
                borderRadius: 1.5,
                bgcolor: "action.hover",
              }}
            >
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
  const [metricsOpen, setMetricsOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [performanceOpen, setPerformanceOpen] = useState(false);
  const { data: evaluationRun } = useEvaluationRun(evaluationId);

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
        <AppBreadcrumbs
          items={[
            { label: "Evaluations", to: "/evaluations" },
            { label: "Summary" },
          ]}
        />
        <Alert severity="error">Evaluation ID is missing from the URL.</Alert>
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
        <AppBreadcrumbs
          items={[
            { label: "Evaluations", to: "/evaluations" },
            { label: "Evaluation", to: `/evaluations/${evaluationId}` },
            { label: "Summary" },
          ]}
        />
        <Stack spacing={2}>
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
  const validMetricValues = metrics
    .map(([, value]) => value)
    .filter((value) => typeof value === "number" && Number.isFinite(value));
  const averageMetricValue = validMetricValues.length
    ? validMetricValues.reduce((total, value) => total + value, 0) /
      validMetricValues.length
    : 0;
  const maxMetricMagnitude = Math.max(
    0,
    ...validMetricValues.map((value) => Math.abs(value)),
  );
  const currency = performance.cost?.currency;
  const averageLatency = averageOf([
    performance.total_model_latency_ms,
    performance.avg_model_latency_ms,
    performance.p95_model_latency_ms,
    performance.p99_model_latency_ms,
  ]);
  const averageTokens = averageOf([
    performance.input_tokens,
    performance.output_tokens,
    performance.total_tokens,
  ]);
  const averageCost = averageOf([
    performance.cost?.input_cost,
    performance.cost?.output_cost,
  ]);

  const totalCases =
    summary.total_results ??
    performance.total_results ??
    performance.completed_cases +
      performance.failed_cases +
      performance.not_applicable_cases;

  const completedCases = summary.completed_cases;
  const failedCases = summary.failed_cases;
  const notApplicableCases =
    evaluationRun?.not_applicable_cases ?? summary.not_applicable_cases;

  const completedPercent =
    totalCases > 0 ? (completedCases / totalCases) * 100 : 0;
  const failedPercent = totalCases > 0 ? (failedCases / totalCases) * 100 : 0;
  const notApplicablePercent =
    totalCases > 0 ? (notApplicableCases / totalCases) * 100 : 0;

  return (
    <Box
      sx={{
        p: { xs: 1, sm: 2, md: 3 },
        maxWidth: 1440,
        mx: "auto",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <Stack spacing={{ xs: 2, md: 2.5 }}>
        <AppBreadcrumbs
          items={[
            { label: "Evaluations", to: "/evaluations" },
            { label: "Evaluation", to: `/evaluations/${evaluationId}` },
            { label: "Summary" },
          ]}
        />

        <Paper
          variant="outlined"
          sx={{
            p: { xs: 2, sm: 2.5 },
            borderRadius: 3,
            borderColor: "divider",
            bgcolor: "background.paper",
          }}
        >
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={2}
            sx={{
              justifyContent: "space-between",
              alignItems: { sm: "center" },
            }}
          >
            <Stack
              direction="row"
              spacing={1.5}
              sx={{ alignItems: "center", minWidth: 0 }}
            >
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  display: "grid",
                  placeItems: "center",
                  flexShrink: 0,
                  borderRadius: 2,
                  color: "primary.main",
                  bgcolor: "action.hover",
                }}
              >
                <AssessmentOutlined />
              </Box>
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  {evaluationRun?.name || "Evaluation summary"}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ overflowWrap: "anywhere" }}
                >
                  {evaluationTypeDescriptions[evaluationRun?.evaluation_type ?? ""] ??
                    "Evaluation results and performance summary."}
                </Typography>
              </Box>
            </Stack>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              sx={{ flexWrap: "wrap" }}
            >
              <Button
                variant="outlined"
                startIcon={<RefreshOutlined />}
                disabled={isFetching}
                onClick={() => void refetch()}
                sx={{ borderRadius: 2, textTransform: "none" }}
              >
                {isFetching ? "Refreshing…" : "Refresh"}
              </Button>
              <Button
                variant="contained"
                disableElevation
                onClick={() => navigate(`/evaluations/${evaluationId}/results`)}
                sx={{ borderRadius: 2, textTransform: "none" }}
              >
                View results
              </Button>
            </Stack>
          </Stack>

          {summary.model && (
            <Stack
              direction={{ xs: "column", sm: "row" }}
              spacing={1}
              useFlexGap
              sx={{
                mt: 2,
                pt: 2,
                flexWrap: "wrap",
                borderTop: 1,
                borderColor: "divider",
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 600, mr: 0.5 }}>
                {summary.model.name}
              </Typography>
              <Chip label={summary.model.provider} size="small" />
              <Chip
                label={summary.model.model_identifier}
                size="small"
                variant="outlined"
                sx={{ maxWidth: "100%" }}
              />
            </Stack>
          )}
        </Paper>

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
          <Paper variant="outlined" sx={{ ...sectionPaperSx, height: "100%" }}>
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

          <ScoreCard
            label="Total results"
            value={formatNumber(totalCases)}
            help={performanceGuides.total_results}
          />

          <ScoreCard
            label="Duration"
            value={formatDuration(performance.duration_ms)}
            help={performanceGuides.duration_ms}
          />

          <ScoreCard
            label="Total cost"
            value={formatCost(performance.cost?.total_cost, currency)}
            help={performanceGuides.total_cost}
          />
        </Box>

        <Paper variant="outlined" sx={sectionPaperSx}>
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
            <StatusChip status="completed" label={`Completed: ${completedCases}`} />
            <StatusChip status="failed" label={`Failed: ${failedCases}`} />
            <StatusChip status="not_applicable" label={`Not applicable: ${notApplicableCases}`} />
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

        <Paper variant="outlined" sx={sectionPaperSx}>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Metric scores
          </Typography>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Per-case averages. Open a metric for its scale and definition.
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
            <Box
              sx={{
                mt: 2,
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(2, minmax(0, 1fr))",
                  lg: "repeat(3, minmax(0, 1fr))",
                },
                gap: 1.5,
              }}
            >
                {metrics.slice(0, 4).map(([metric, value]) => (
                  <MetricScoreCard key={metric} metric={metric} value={value} averageMetricValue={averageMetricValue} maxMetricMagnitude={maxMetricMagnitude} />
                ))}
            </Box>
          )}
          {metrics.length > 4 && <Button sx={{ mt: 2 }} onClick={() => setMetricsOpen(true)}>View all {metrics.length} metrics</Button>}
        </Paper>

        <Dialog open={metricsOpen} onClose={() => setMetricsOpen(false)} fullWidth maxWidth="md">
          <DialogTitle>All metric scores</DialogTitle>
          <DialogContent dividers sx={{ maxHeight: "70vh" }}>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: 1.5 }}>
              {metrics.slice(4).map(([metric, value]) => <MetricScoreCard key={metric} metric={metric} value={value} averageMetricValue={averageMetricValue} maxMetricMagnitude={maxMetricMagnitude} />)}
            </Box>
          </DialogContent>
          <DialogActions><Button onClick={() => setMetricsOpen(false)}>Close</Button></DialogActions>
        </Dialog>

        <Paper variant="outlined" sx={sectionPaperSx}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems={{ sm: "center" }} justifyContent="space-between">
            <Box sx={{ minWidth: 0 }}>
              <Typography variant="h6" fontWeight={700}>Evaluation feedback</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                {feedback?.overall || "Open strengths, weaknesses, patterns, and recommendations."}
              </Typography>
            </Box>
            <Button variant="outlined" onClick={() => setFeedbackOpen(true)} sx={{ flexShrink: 0 }}>View feedback</Button>
          </Stack>
        </Paper>

        <Dialog open={feedbackOpen} onClose={() => setFeedbackOpen(false)} fullWidth maxWidth="md">
          <DialogTitle>Evaluation feedback</DialogTitle>
          <DialogContent dividers sx={{ maxHeight: "70vh" }}>
            <Stack spacing={2}>
              <Paper variant="outlined" sx={sectionPaperSx}>
                <Typography variant="subtitle1" fontWeight={700} gutterBottom>Overall assessment</Typography>
                <Typography sx={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{feedback?.overall || "No overall assessment is available."}</Typography>
              </Paper>
              <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" }, gap: 2 }}>
                <FeedbackSection title="Strengths" items={feedback?.strengths ?? []} emptyMessage="No strengths were reported." icon={<CheckCircleOutlined fontSize="small" />} color="success.main" />
                <FeedbackSection title="Weaknesses" items={feedback?.weaknesses ?? []} emptyMessage="No weaknesses were reported." icon={<ThumbDownAltOutlined fontSize="small" />} color="warning.main" />
                <FeedbackSection title="Patterns" items={feedback?.patterns ?? []} emptyMessage="No patterns were reported." icon={<AutoAwesomeOutlined fontSize="small" />} color="info.main" />
                <FeedbackSection title="Recommendations" items={feedback?.recommendations ?? []} emptyMessage="No recommendations were reported." icon={<LightbulbOutlined fontSize="small" />} color="primary.main" />
              </Box>
              {(feedback?.evaluator_feedback?.length ?? 0) > 0 && <Paper variant="outlined" sx={sectionPaperSx}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}><RuleOutlined fontSize="small" color="primary" /><Typography variant="subtitle1" fontWeight={700}>Evaluator feedback</Typography><Chip size="small" label={feedback.evaluator_feedback?.length ?? 0} variant="outlined" /></Stack>
                <Stack spacing={1}>{feedback.evaluator_feedback?.map((item, index) => <Box key={`evaluator-feedback-${index}`} sx={{ p: 1.25, borderRadius: 1.5, bgcolor: "action.hover" }}><Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>{item}</Typography></Box>)}</Stack>
              </Paper>}
            </Stack>
          </DialogContent>
          <DialogActions><Button onClick={() => setFeedbackOpen(false)}>Close</Button></DialogActions>
        </Dialog>

        <Paper variant="outlined" sx={sectionPaperSx}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems={{ sm: "center" }} justifyContent="space-between">
            <Box>
              <Typography variant="h6" fontWeight={700}>Performance and usage</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                {formatDuration(performance.total_model_latency_ms)} total latency · {formatNumber(performance.total_tokens)} tokens · {formatCost(performance.cost?.total_cost, currency)} total cost
              </Typography>
            </Box>
            <Button variant="outlined" onClick={() => setPerformanceOpen(true)} sx={{ flexShrink: 0 }}>View details</Button>
          </Stack>
        </Paper>

        <Dialog open={performanceOpen} onClose={() => setPerformanceOpen(false)} fullWidth maxWidth="md">
          <DialogTitle>Performance and usage</DialogTitle>
          <DialogContent dividers sx={{ maxHeight: "70vh" }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Higher-than-average latency, token use, or cost is highlighted for
            attention. Lower values are favorable; throughput is better when higher.
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
              help={performanceGuides.total_model_latency_ms}
              belowAverage={isAboveAverage(
                performance.total_model_latency_ms,
                averageLatency,
              )}
            />

            <ScoreCard
              label="Average model latency"
              value={formatDuration(performance.avg_model_latency_ms)}
              help={performanceGuides.avg_model_latency_ms}
              belowAverage={isAboveAverage(
                performance.avg_model_latency_ms,
                averageLatency,
              )}
            />

            <ScoreCard
              label="P95 latency"
              value={formatDuration(performance.p95_model_latency_ms)}
              help={performanceGuides.p95_model_latency_ms}
              belowAverage={isAboveAverage(
                performance.p95_model_latency_ms,
                averageLatency,
              )}
            />

            <ScoreCard
              label="P99 latency"
              value={formatDuration(performance.p99_model_latency_ms)}
              help={performanceGuides.p99_model_latency_ms}
              belowAverage={isAboveAverage(
                performance.p99_model_latency_ms,
                averageLatency,
              )}
            />

            <ScoreCard
              label="Input tokens"
              value={formatNumber(performance.input_tokens)}
              help={performanceGuides.input_tokens}
              belowAverage={isAboveAverage(
                performance.input_tokens,
                averageTokens,
              )}
            />

            <ScoreCard
              label="Output tokens"
              value={formatNumber(performance.output_tokens)}
              help={performanceGuides.output_tokens}
              belowAverage={isAboveAverage(
                performance.output_tokens,
                averageTokens,
              )}
            />

            <ScoreCard
              label="Total tokens"
              value={formatNumber(performance.total_tokens)}
              help={performanceGuides.total_tokens}
              belowAverage={isAboveAverage(
                performance.total_tokens,
                averageTokens,
              )}
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
              help={performanceGuides.throughput_cases_per_second}
            />

            <ScoreCard
              label="Input cost"
              value={formatCost(performance.cost?.input_cost, currency)}
              help={performanceGuides.input_cost}
              belowAverage={isAboveAverage(
                performance.cost?.input_cost,
                averageCost,
              )}
            />

            <ScoreCard
              label="Output cost"
              value={formatCost(performance.cost?.output_cost, currency)}
              help={performanceGuides.output_cost}
              belowAverage={isAboveAverage(
                performance.cost?.output_cost,
                averageCost,
              )}
            />
          </Box>
          </DialogContent>
          <DialogActions><Button onClick={() => setPerformanceOpen(false)}>Close</Button></DialogActions>
        </Dialog>
      </Stack>
    </Box>
  );
}
