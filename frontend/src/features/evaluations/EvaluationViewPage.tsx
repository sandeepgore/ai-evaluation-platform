import {
  AssessmentOutlined,
  DownloadOutlined,
  ListAltOutlined,
  PlayCircleOutlined,
  RefreshOutlined,
  StopCircleOutlined,
  TableChartOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip as ChartTooltip } from "recharts";
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { PermissionGate } from "../../components/common/PermissionGate";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { StatusChip } from "../../components/common/StatusChip";
import { downloadBlob } from "../../components/common/downloadBlob";
import { useNotification } from "../../components/common/NotificationProvider";
import { useDataset } from "../datasets/hooks";
import { useDatasetVersion } from "../datasetVersions/hooks";
import { useModel } from "../models/hooks";
import { downloadEvaluationRunLogs } from "./api";
import {
  useCancelEvaluationRun,
  useEvaluationRun,
  useEvaluationRunStatus,
  useExecuteEvaluationRun,
  useEvaluationRunLogsAvailability,
} from "./hooks";

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

  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [cancelRequested, setCancelRequested] = useState(false);
  const [waitingForQueue, setWaitingForQueue] = useState(false);
  const [isDownloadingLogs, setIsDownloadingLogs] = useState(false);
  const [isDetailsDialogOpen, setIsDetailsDialogOpen] = useState(false);

  // Prevent rapid duplicate clicks before React re-renders.
  const executionSubmissionLock = useRef(false);

  const {
    data: run,
    isLoading: isRunLoading,
    isError,
    error,
  } = useEvaluationRun(evaluationId);

  const {
    data: statusData,
    refetch: refreshStatus,
    isFetching: isRefreshing,
  } = useEvaluationRunStatus(evaluationId, Boolean(evaluationId));

  const executeMutation = useExecuteEvaluationRun();
  const cancelMutation = useCancelEvaluationRun();
  const { notify } = useNotification();
  const { data: hasRunLogs } = useEvaluationRunLogsAvailability(run?.id);

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

  const isPending = progressSource.status === "pending";
  const isActive = progressSource.status === "running";
  const isTerminal = ["completed", "failed", "cancelled"].includes(
    progressSource.status,
  );

  // Clear the queue-waiting state once the server reports a status change.
  useEffect(() => {
    if (progressSource.status !== "pending") {
      setWaitingForQueue(false);
      executionSubmissionLock.current = false;
    }
  }, [progressSource.status]);

  const palette = theme.palette;
  const caseColors = {
    completed: palette.success.main,
    failed: palette.error.main,
    notApplicable: palette.grey[500],
  };

  const panelBackground =
    theme.palette.mode === "dark"
      ? alpha(palette.common.white, 0.035)
      : alpha(palette.common.black, 0.018);

  const subtleBorder = alpha(
    palette.text.primary,
    theme.palette.mode === "dark" ? 0.14 : 0.09,
  );

  const metricCardSx = {
    p: 2,
    textAlign: "center" as const,
    borderRadius: 2,
    borderColor: subtleBorder,
    bgcolor: panelBackground,
  };

  if (isRunLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: 400,
        }}
      >
        <CircularProgress size={32} />
      </Box>
    );
  }

  if (isError || !run) {
    return (
      <Stack spacing={2} sx={{ maxWidth: 600, mx: "auto", mt: 4 }}>
        <AppBreadcrumbs items={[{ label: "Evaluations", to: "/evaluations" }, { label: "Evaluation" }]} />
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

  const remainingCases = Math.max(
    progressSource.total_cases - progressSource.completed_cases - progressSource.failed_cases - progressSource.not_applicable_cases,
    0,
  );
  const outcomeData = [
    { name: "Completed", value: progressSource.completed_cases, color: caseColors.completed },
    { name: "Failed", value: progressSource.failed_cases, color: caseColors.failed },
    { name: "Not applicable", value: progressSource.not_applicable_cases, color: caseColors.notApplicable },
    { name: "Remaining", value: remainingCases, color: alpha(palette.text.primary, 0.12) },
  ];

  const metadata = [
    { label: "Dataset Version", value: datasetVersionName },
    { label: "Model Targeted", value: modelName },
    {
      label: "Evaluation Category",
      value: EVALUATION_TYPE_LABELS[run.evaluation_type] ?? run.evaluation_type,
    },
    { label: "Execution Mode", value: run.mode },
    { label: "Created At", value: formatDate(run.created_at) },
    { label: "Started At", value: formatDate(progressSource.started_at) },
    { label: "Completed At", value: formatDate(progressSource.completed_at) },
    {
      label: "Total Duration",
      value: formatDuration(progressSource.duration_ms),
    },
  ];

  const isSubmitting = executeMutation.isPending;
  const isWaitingInQueue = waitingForQueue && isPending;
  const isExecutionButtonDisabled =
    isSubmitting ||
    isWaitingInQueue ||
    executionSubmissionLock.current ||
    !evaluationId;

  return (
    <Stack spacing={3} sx={{ pb: 6 }}>
      {/* Header and Navigation */}
      <Stack spacing={1.5}>
        <AppBreadcrumbs items={[{ label: "Evaluations", to: "/evaluations" }, { label: run.name }]} />

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", sm: "center" },
          }}
        >
          <Box sx={{ minWidth: 0 }}>
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
            useFlexGap
            sx={{
              alignItems: "center",
              flexWrap: "wrap",
              rowGap: 1,
            }}
          >
            <StatusChip
              status={progressSource.status}
              label={cancelRequested && isActive ? "Stopping" : undefined}
            />

            <Tooltip
              title={hasRunLogs
                ? "Download the worker logs for this evaluation run. Logs are retained for three days."
                : "No retained worker logs are available for this run."}
            >
              <span>
                <Button
                  variant="outlined"
                  startIcon={isDownloadingLogs ? <CircularProgress size={16} /> : <DownloadOutlined />}
                  disabled={!hasRunLogs || isDownloadingLogs}
                  onClick={async () => {
                    setIsDownloadingLogs(true);
                    try {
                      const archive = await downloadEvaluationRunLogs(run.id);
                      downloadBlob(archive, `evaluation-run-${run.id}-logs.zip`);
                    } catch (downloadError) {
                      notify(
                        downloadError instanceof Error
                          ? downloadError.message
                          : "Unable to download evaluation logs.",
                        "error",
                      );
                    } finally {
                      setIsDownloadingLogs(false);
                    }
                  }}
                  sx={{ borderRadius: 2, textTransform: "none" }}
                >
                  {isDownloadingLogs ? "Preparing logs..." : "Download logs"}
                </Button>
              </span>
            </Tooltip>

            {datasetVersion && (
              <Button
                variant="outlined"
                color="inherit"
                startIcon={<ListAltOutlined />}
                onClick={() =>
                  navigate(
                    `/datasets/${datasetVersion.dataset_id}/versions/${datasetVersion.id}/cases`,
                  )
                }
                sx={{ borderRadius: 2, textTransform: "none" }}
              >
                View dataset cases
              </Button>
            )}

            {isPending && (
              <PermissionGate permission="write">
              <Button
                variant="contained"
                color="primary"
                disableElevation
                disabled={isExecutionButtonDisabled}
                startIcon={
                  isSubmitting || isWaitingInQueue ? (
                    <CircularProgress size={16} color="inherit" />
                  ) : (
                    <PlayCircleOutlined />
                  )
                }
                onClick={() => {
                  if (!evaluationId || executionSubmissionLock.current) {
                    return;
                  }

                  // Lock synchronously before starting the mutation.
                  executionSubmissionLock.current = true;
                  setWaitingForQueue(true);

                  executeMutation.mutate(evaluationId, {
                    onSuccess: () => {
                      // Keep the lock while the server status is pending.
                      // Refresh once so a fast status transition is detected.
                      void refreshStatus();
                    },
                    onError: () => {
                      // Submission failed, so allow a safe retry.
                      executionSubmissionLock.current = false;
                      setWaitingForQueue(false);
                    },
                  });
                }}
                sx={{
                  borderRadius: 2,
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                {isSubmitting
                  ? "Submitting..."
                  : isWaitingInQueue
                    ? "Waiting in Queue..."
                    : "Run Evaluation"}
              </Button>
              </PermissionGate>
            )}

            {isActive && (
              <>
                <Button
                  variant="outlined"
                  color="info"
                  size="small"
                  onClick={() => void refreshStatus()}
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

                <PermissionGate permission="write"><Button
                  variant="outlined"
                  color="error"
                  size="small"
                  onClick={() => setIsCancelDialogOpen(true)}
                  disabled={
                    cancelRequested || cancelMutation.isPending || !evaluationId
                  }
                  startIcon={
                    cancelMutation.isPending ? (
                      <CircularProgress size={14} color="inherit" />
                    ) : (
                      <StopCircleOutlined fontSize="small" />
                    )
                  }
                  sx={{ borderRadius: 2, textTransform: "none" }}
                >
                  {cancelRequested
                    ? "Stopping..."
                    : cancelMutation.isPending
                      ? "Requesting..."
                      : "Stop Evaluation"}
                </Button></PermissionGate>
              </>
            )}

            {isTerminal && (
              <>
                <Button
                  variant="contained"
                  color="primary"
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
                  color="primary"
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

      {/* Queue waiting status */}
      {isWaitingInQueue && (
        <Alert severity="info">
          Evaluation submitted. Waiting for the worker to pick it up. This
          button will remain disabled until the evaluation status changes.
        </Alert>
      )}

      {/* Cancellation status */}
      {cancelRequested && isActive && (
        <Alert severity="info">
          Cancellation has been requested. The current case or batch may finish
          before the evaluation stops.
        </Alert>
      )}

      {/* Execution Progress */}
      <Paper
        variant="outlined"
        sx={{
          p: { xs: 2, sm: 3 },
          borderRadius: 3,
          borderColor: subtleBorder,
        }}
      >
        <Stack spacing={2.5}>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={1}
            sx={{
              justifyContent: "space-between",
              alignItems: { xs: "flex-start", sm: "baseline" },
            }}
          >
            <Box>
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Execution Progress
                </Typography>

                {isActive && <CircularProgress size={16} color="info" />}
              </Stack>

              <Typography variant="body2" color="text.secondary">
                {isPending
                  ? isWaitingInQueue
                    ? "Evaluation submitted and waiting for execution."
                    : "Not started. Submit this evaluation when you're ready."
                  : `${progressSource.processed_cases} of ${progressSource.total_cases} test cases evaluated.`}
              </Typography>
            </Box>

            <Typography
              variant="h5"
              color="primary.main"
              sx={{ fontWeight: 700 }}
            >
              {progressSource.progress_percent.toFixed(1)}%
            </Typography>
          </Stack>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", md: "220px minmax(0, 1fr)" },
              gap: 2,
              alignItems: "center",
            }}
          >
            <Box sx={{ position: "relative", width: "100%", height: 200 }} aria-label="Evaluation case outcome chart">
              {progressSource.total_cases > 0 && <ResponsiveContainer>
                <PieChart>
                  <Pie data={outcomeData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={82} paddingAngle={2}>
                    {outcomeData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Pie>
                  <ChartTooltip formatter={(value, name) => [value, String(name)]} />
                </PieChart>
              </ResponsiveContainer>}
              <Box sx={{ position: "absolute", inset: 0, display: "grid", placeContent: "center", pointerEvents: "none", textAlign: "center" }}>
                <Typography variant="h6" fontWeight={700}>{progressSource.progress_percent.toFixed(0)}%</Typography>
                <Typography variant="caption" color="text.secondary">{progressSource.total_cases ? "evaluated" : "no cases"}</Typography>
              </Box>
            </Box>
            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "repeat(2, minmax(0, 1fr))", sm: "repeat(4, minmax(0, 1fr))" }, gap: 1.5 }}>
              {[
                { label: "Completed", value: progressSource.completed_cases, color: "success.main" },
                { label: "Failed", value: progressSource.failed_cases, color: "error.main" },
                { label: "Not applicable", value: progressSource.not_applicable_cases, color: caseColors.notApplicable },
                { label: "Remaining", value: remainingCases, color: "text.primary" },
              ].map((item) => <Paper key={item.label} variant="outlined" sx={metricCardSx}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: "uppercase" }}>{item.label}</Typography>
                <Typography variant="h6" sx={{ color: item.color, fontWeight: 700, mt: 0.5 }}>{item.value}</Typography>
              </Paper>)}
            </Box>
          </Box>

          {isTerminal && progressSource.failed_cases > 0 && (
            <Alert
              severity="warning"
              variant="outlined"
              action={
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => navigate(`/evaluations/${run.id}/results`)}
                  sx={{ textTransform: "none", whiteSpace: "nowrap" }}
                >
                  Inspect failures
                </Button>
              }
            >
              This run finished with {progressSource.failed_cases} failed case
              {progressSource.failed_cases === 1 ? "" : "s"}. A completed run
              does not mean every case succeeded.
            </Alert>
          )}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 2.5 }, borderRadius: 3, borderColor: subtleBorder }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems={{ sm: "center" }} justifyContent="space-between">
          <Box>
            <Typography variant="h6" fontWeight={600}>Run details</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {datasetVersionName} · {modelName} · {formatDuration(progressSource.duration_ms)}
            </Typography>
          </Box>
          <Button variant="outlined" onClick={() => setIsDetailsDialogOpen(true)}>View configuration and timing</Button>
        </Stack>
      </Paper>

      <Dialog open={isDetailsDialogOpen} onClose={() => setIsDetailsDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Run configuration and timing</DialogTitle>
        <DialogContent dividers sx={{ maxHeight: "70vh" }}>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", md: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
            {metadata.map((item) => <Box key={item.label} sx={{ minWidth: 0 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: "block" }}>{item.label}</Typography>
              <Typography variant="body2" sx={{ mt: 0.5, fontWeight: item.label === "Total Duration" ? 600 : 500, fontFamily: item.label === "Total Duration" ? "monospace" : "inherit", textTransform: item.label === "Execution Mode" ? "capitalize" : "none", overflowWrap: "anywhere" }}>{item.value}</Typography>
            </Box>)}
          </Box>
          {run.configuration && <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>Configuration payload</Typography>
            <Paper component="pre" variant="outlined" sx={{ p: 2, m: 0, maxHeight: 280, overflow: "auto", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{JSON.stringify(run.configuration, null, 2)}</Paper>
          </Box>}
        </DialogContent>
        <DialogActions><Button onClick={() => setIsDetailsDialogOpen(false)}>Close</Button></DialogActions>
      </Dialog>

      <ConfirmDialog
        open={isCancelDialogOpen}
        title="Stop Evaluation?"
        message="This requests a graceful stop. The current case or batch may finish before the evaluation is marked cancelled. This action cannot be undone."
        confirmLabel="Stop Evaluation"
        cancelLabel="Keep Running"
        loading={cancelMutation.isPending}
        onCancel={() => setIsCancelDialogOpen(false)}
        onConfirm={() => {
          if (!evaluationId) return;

          cancelMutation.mutate(evaluationId, {
            onSuccess: () => {
              setCancelRequested(true);
              setIsCancelDialogOpen(false);
            },
          });
        }}
      />
    </Stack>
  );
}
