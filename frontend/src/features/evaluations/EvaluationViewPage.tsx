import React, { useEffect } from "react";
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Paper,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";
import {
  ArrowBackOutlined,
  RefreshOutlined,
  AssessmentOutlined,
  TableChartOutlined,
} from "@mui/icons-material";

import { useDataset } from "../datasets/hooks";
import { useDatasetVersion } from "../datasetVersions/hooks";
import { useModel } from "../models/hooks";
import { useEvaluationRun, useEvaluationRunStatus } from "./hooks";

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    color:
      | "default"
      | "primary"
      | "secondary"
      | "error"
      | "info"
      | "success"
      | "warning";
  }
> = {
  pending: { label: "Pending", color: "warning" },
  running: { label: "Running", color: "info" },
  completed: { label: "Completed", color: "success" },
  failed: { label: "Failed", color: "error" },
};

const EVALUATION_TYPE_LABELS: Record<string, string> = {
  text: "Text Generation",
  rag: "RAG Evaluation",
  conversation: "Conversational AI",
  safety: "Safety & Guardrails",
};

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatDuration(durationMs: number | null): string {
  if (durationMs === null) return "—";
  if (durationMs < 1000) return `${durationMs} ms`;

  const seconds = durationMs / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
}

export function EvaluationViewPage() {
  const { evaluationId } = useParams<{ evaluationId: string }>();
  const navigate = useNavigate();
  const theme = useTheme();

  const {
    data: run,
    isLoading: isRunLoading,
    isError,
    error,
    refetch: refetchRun,
  } = useEvaluationRun(evaluationId);

  const {
    data: statusData,
    refetch: refreshStatus,
    isFetching: isRefreshing,
  } = useEvaluationRunStatus(evaluationId, Boolean(evaluationId));

  const { data: model, isLoading: isModelLoading } = useModel(
    run?.model_id ?? null,
  );

  const { data: datasetVersion, isLoading: isDatasetVersionLoading } =
    useDatasetVersion(run?.dataset_version_id ?? null);

  const { data: dataset, isLoading: isDatasetLoading } = useDataset(
    datasetVersion?.dataset_id ?? null,
  );

  const progressSource = statusData ?? {
    total_cases: run?.total_cases ?? 0,
    completed_cases: run?.completed_cases ?? 0,
    failed_cases: run?.failed_cases ?? 0,
    not_applicable_cases: run?.not_applicable_cases ?? 0,
    processed_cases:
      (run?.completed_cases ?? 0) +
      (run?.failed_cases ?? 0) +
      (run?.not_applicable_cases ?? 0),
    progress_percent:
      (run?.total_cases ?? 0) > 0
        ? (((run?.completed_cases ?? 0) +
            (run?.failed_cases ?? 0) +
            (run?.not_applicable_cases ?? 0)) /
            (run?.total_cases ?? 1)) *
          100
        : 0,
    started_at: run?.started_at ?? null,
    completed_at: run?.completed_at ?? null,
    duration_ms: run?.duration_ms ?? null,
    id: run?.id ?? "",
    status: run?.status ?? "pending",
  };

  const isRunning = progressSource.status === "running";
  const isPending = progressSource.status === "pending";
  const isActive = isRunning || isPending;
  const isTerminal =
    progressSource.status === "completed" || progressSource.status === "failed";

  useEffect(() => {
    if (!isActive || !evaluationId) return;

    const interval = setInterval(() => {
      refreshStatus();
      refetchRun();
    }, 3000);

    return () => clearInterval(interval);
  }, [isActive, evaluationId, refreshStatus, refetchRun]);

  if (isRunLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "400px",
        }}
      >
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (isError || !run) {
    return (
      <Stack spacing={2} sx={{ maxWidth: 600, mx: "auto", mt: 4 }}>
        <Button
          variant="text"
          startIcon={<ArrowBackOutlined />}
          onClick={() => navigate("/evaluations")}
          sx={{ alignSelf: "flex-start", textTransform: "none" }}
        >
          Back to Evaluations
        </Button>

        <Alert severity="error">
          {error instanceof Error
            ? error.message
            : "Unable to load evaluation details."}
        </Alert>
      </Stack>
    );
  }

  const modelName =
    model?.name ?? (isModelLoading ? "Loading model..." : "Unknown Model");

  const datasetVersionName =
    datasetVersion && dataset
      ? `${dataset.name} (v${datasetVersion.version})`
      : isDatasetVersionLoading || isDatasetLoading
        ? "Loading dataset version..."
        : "Unknown Dataset Version";

  const total = progressSource.total_cases || 1;
  const completedPct = (progressSource.completed_cases / total) * 100;
  const failedPct = (progressSource.failed_cases / total) * 100;
  const naPct = (progressSource.not_applicable_cases / total) * 100;

  return (
    <Stack spacing={3} sx={{ pb: 6 }}>
      {/* Header & Navigation */}
      <Stack spacing={1.5}>
        <Breadcrumbs aria-label="breadcrumb">
          <Typography
            component={RouterLink}
            to="/evaluations"
            color="inherit"
            variant="body2"
            sx={{
              textDecoration: "none",
              "&:hover": { textDecoration: "underline" },
            }}
          >
            Evaluations
          </Typography>
          <Typography
            variant="body2"
            color="text.primary"
            sx={{ fontWeight: 500 }}
          >
            {run.name}
          </Typography>
        </Breadcrumbs>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", sm: "center" },
          }}
        >
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {run.name}
            </Typography>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {EVALUATION_TYPE_LABELS[run.evaluation_type] ??
                run.evaluation_type}
              {" • "}
              {modelName}
            </Typography>
          </Box>

          <Stack
            direction="row"
            spacing={1.5}
            sx={{
              alignItems: "center",
              flexWrap: "wrap",
            }}
          >
            <Chip
              label={
                STATUS_CONFIG[progressSource.status]?.label ??
                progressSource.status
              }
              color={STATUS_CONFIG[progressSource.status]?.color ?? "default"}
              sx={{
                fontWeight: 600,
                borderRadius: 1.5,
                px: 0.5,
              }}
            />

            {isActive && (
              <Button
                variant="outlined"
                size="small"
                onClick={() => refreshStatus()}
                disabled={isRefreshing}
                startIcon={
                  isRefreshing ? (
                    <CircularProgress size={14} color="inherit" />
                  ) : (
                    <RefreshOutlined fontSize="small" />
                  )
                }
                sx={{ borderRadius: 2, textTransform: "none" }}
              >
                {isRefreshing ? "Syncing..." : "Refresh"}
              </Button>
            )}

            {isTerminal && (
              <>
                <Button
                  variant="contained"
                  disableElevation
                  startIcon={<AssessmentOutlined />}
                  onClick={() => navigate(`/evaluations/${run.id}/summary`)}
                  sx={{
                    borderRadius: 2,
                    textTransform: "none",
                    fontWeight: 600,
                  }}
                >
                  View Summary
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<TableChartOutlined />}
                  onClick={() => navigate(`/evaluations/${run.id}/results`)}
                  sx={{
                    borderRadius: 2,
                    textTransform: "none",
                    fontWeight: 600,
                  }}
                >
                  View Raw Results
                </Button>
              </>
            )}
          </Stack>
        </Stack>
      </Stack>

      {/* Execution Progress Section */}
      <Paper
        variant="outlined"
        sx={{
          p: 3,
          borderRadius: 3,
          borderColor: "divider",
        }}
      >
        <Stack spacing={2.5}>
          <Stack
            direction="row"
            sx={{
              justifyContent: "space-between",
              alignItems: "baseline",
            }}
          >
            <Box>
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Execution Progress
                </Typography>
                {isActive && (
                  <CircularProgress size={16} sx={{ color: "primary.main" }} />
                )}
              </Stack>

              <Typography variant="body2" color="text.secondary">
                {isPending
                  ? "Queued for processing..."
                  : `${progressSource.processed_cases} of ${progressSource.total_cases} test cases evaluated.`}
              </Typography>
            </Box>

            <Typography variant="h5" color="primary" sx={{ fontWeight: 700 }}>
              {progressSource.progress_percent.toFixed(1)}%
            </Typography>
          </Stack>

          {/* Segmented Progress Bar */}
          <Box
            sx={{
              height: 12,
              borderRadius: 6,
              bgcolor: alpha(theme.palette.text.primary, 0.08),
              overflow: "hidden",
              display: "flex",
              width: "100%",
            }}
          >
            <Tooltip title={`Completed: ${progressSource.completed_cases}`}>
              <Box
                sx={{
                  width: `${completedPct}%`,
                  bgcolor: "success.main",
                  transition: "width 0.4s ease",
                }}
              />
            </Tooltip>

            <Tooltip title={`Failed: ${progressSource.failed_cases}`}>
              <Box
                sx={{
                  width: `${failedPct}%`,
                  bgcolor: "error.main",
                  transition: "width 0.4s ease",
                }}
              />
            </Tooltip>

            <Tooltip title={`N/A: ${progressSource.not_applicable_cases}`}>
              <Box
                sx={{
                  width: `${naPct}%`,
                  bgcolor: "grey.500",
                  transition: "width 0.4s ease",
                }}
              />
            </Tooltip>
          </Box>

          {/* Case Counters */}
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "repeat(2, 1fr)",
                sm: "repeat(4, 1fr)",
              },
              gap: 2,
            }}
          >
            <Paper
              variant="outlined"
              sx={{
                p: 2,
                textAlign: "center",
                borderRadius: 2,
                bgcolor: "background.neutral",
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: "uppercase" }}
              >
                Completed
              </Typography>
              <Typography
                variant="h6"
                color="success.main"
                sx={{ fontWeight: 700, mt: 0.5 }}
              >
                {progressSource.completed_cases}
              </Typography>
            </Paper>

            <Paper
              variant="outlined"
              sx={{
                p: 2,
                textAlign: "center",
                borderRadius: 2,
                bgcolor: "background.neutral",
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: "uppercase" }}
              >
                Failed
              </Typography>
              <Typography
                variant="h6"
                color="error.main"
                sx={{ fontWeight: 700, mt: 0.5 }}
              >
                {progressSource.failed_cases}
              </Typography>
            </Paper>

            <Paper
              variant="outlined"
              sx={{
                p: 2,
                textAlign: "center",
                borderRadius: 2,
                bgcolor: "background.neutral",
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: "uppercase" }}
              >
                N/A
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{ fontWeight: 700, mt: 0.5 }}
              >
                {progressSource.not_applicable_cases}
              </Typography>
            </Paper>

            <Paper
              variant="outlined"
              sx={{
                p: 2,
                textAlign: "center",
                borderRadius: 2,
                bgcolor: "background.neutral",
              }}
            >
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: "uppercase" }}
              >
                Total Cases
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700, mt: 0.5 }}>
                {progressSource.total_cases}
              </Typography>
            </Paper>
          </Box>
        </Stack>
      </Paper>

      {/* Run Metadata Details */}
      <Paper
        variant="outlined"
        sx={{
          p: 3,
          borderRadius: 3,
          borderColor: "divider",
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }} gutterBottom>
          Run Configuration & Timing
        </Typography>

        <Divider sx={{ mb: 3 }} />

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "repeat(1, 1fr)",
              sm: "repeat(2, 1fr)",
              md: "repeat(4, 1fr)",
            },
            gap: 3,
          }}
        >
          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Dataset Version
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 500 }}>
              {datasetVersionName}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Model Targeted
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 500 }}>
              {modelName}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Evaluation Category
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 500 }}>
              {EVALUATION_TYPE_LABELS[run.evaluation_type] ??
                run.evaluation_type}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Execution Mode
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 0.5,
                fontWeight: 500,
                textTransform: "capitalize",
              }}
            >
              {run.mode}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Created At
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {formatDate(run.created_at)}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Started At
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {formatDate(progressSource.started_at)}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Completed At
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {formatDate(progressSource.completed_at)}
            </Typography>
          </Box>

          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, display: "block" }}
            >
              Total Duration
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 0.5,
                fontWeight: 600,
                fontFamily: "monospace",
              }}
            >
              {formatDuration(progressSource.duration_ms)}
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Stack>
  );
}
