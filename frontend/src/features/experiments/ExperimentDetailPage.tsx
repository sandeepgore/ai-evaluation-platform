import {
  AddchartOutlined,
  CompareArrowsOutlined,
  HistoryOutlined,
  RefreshOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAppContextStore } from "../../store/appContextStore";
import { DataTablePagination } from "../../components/common/DataTablePagination";
import type { EvaluationRun } from "../evaluations/api";
import { useEvaluationRuns } from "../evaluations/hooks";
import type { ExperimentSnapshot } from "./api";
import {
  useCreateExperimentSnapshot,
  useExperiment,
  useExperimentSnapshots,
} from "./hooks";

interface NumericComparison {
  baseline: number;
  candidate: number;
  delta: number;
}

interface ComparisonRow extends NumericComparison {
  category: string;
  label: string;
}

function isNumericComparison(value: unknown): value is NumericComparison {
  if (!value || typeof value !== "object") return false;
  const comparison = value as Record<string, unknown>;
  return [comparison.baseline, comparison.candidate, comparison.delta].every(
    (item) => typeof item === "number" && Number.isFinite(item),
  );
}

function comparisonRows(comparison: Record<string, unknown>): ComparisonRow[] {
  const rows: ComparisonRow[] = [];
  const excludedGroups = new Set(["feedback", "overall_score"]);

  for (const [key, value] of Object.entries(comparison)) {
    if (isNumericComparison(value)) {
      rows.push({ category: "Quality", label: key, ...value });
      continue;
    }

    if (!value || typeof value !== "object" || excludedGroups.has(key))
      continue;
    for (const [field, item] of Object.entries(
      value as Record<string, unknown>,
    )) {
      if (isNumericComparison(item)) {
        rows.push({ category: key, label: field, ...item });
      }
    }
  }

  return rows;
}

function formatValue(value: number, label: string, currency?: string) {
  if (
    currency &&
    ["cost", "input_cost", "output_cost", "total_cost"].some((key) =>
      label.includes(key),
    )
  ) {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        maximumFractionDigits: 4,
      }).format(value);
    } catch {
      return `${new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 }).format(value)} ${currency}`;
    }
  }
  const formatted = new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 4,
  }).format(value);
  if (label.endsWith("_ms")) return `${formatted} ms`;
  if (label === "throughput_cases_per_second") return `${formatted} cases/s`;
  return formatted;
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
}

function runName(snapshot: ExperimentSnapshot, id?: string) {
  return (
    (id && snapshot.run_results[id]?.run.name) ||
    (id ? `Run ${id.slice(0, 8)}` : "Unknown run")
  );
}

function isImprovement(row: ComparisonRow): boolean | null {
  if (row.category === "execution") {
    if (row.label === "completed_cases") return row.delta > 0;
    if (row.label === "failed_cases") return row.delta < 0;
    return null;
  }
  if (row.category === "tokens" || row.category === "cost")
    return row.delta < 0;
  if (row.category === "performance") {
    return row.label === "throughput_cases_per_second"
      ? row.delta > 0
      : row.delta < 0;
  }
  if (/latency|duration|response_time|cost|token|error_rate|failure_rate/i.test(row.label)) {
    return row.delta < 0;
  }
  return row.delta > 0;
}

function FeedbackComparison({ snapshot }: { snapshot: ExperimentSnapshot }) {
  const feedbackFields = [
    ["overall", "Overall assessment"],
    ["strengths", "Strengths"],
    ["weaknesses", "Weaknesses"],
    ["patterns", "Patterns"],
    ["recommendations", "Recommendations"],
    ["evaluator_feedback", "Evaluator feedback"],
  ] as const;
  const baseline =
    snapshot.run_results[snapshot.run_ids[0]]?.summary.feedback ?? {};
  const candidate =
    snapshot.run_results[snapshot.run_ids[1]]?.summary.feedback ?? {};
  const hasFeedback = feedbackFields.some(([field]) => {
    const before = baseline[field];
    const after = candidate[field];
    return (
      (Array.isArray(before) && before.length > 0) ||
      (Array.isArray(after) && after.length > 0) ||
      (typeof before === "string" && before.length > 0) ||
      (typeof after === "string" && after.length > 0)
    );
  });

  if (!hasFeedback) return null;

  const renderContent = (value: unknown) => {
    if (typeof value === "string") return value;
    if (Array.isArray(value)) {
      return value.length
        ? value.map(String).join("\n\n")
        : "No feedback reported.";
    }
    return "No feedback reported.";
  };

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
        Qualitative feedback
      </Typography>
      {feedbackFields.map(([field, label]) => {
        const before = baseline[field];
        const after = candidate[field];
        const hasValue = [before, after].some(
          (value) =>
            (Array.isArray(value) && value.length > 0) ||
            (typeof value === "string" && value.length > 0),
        );
        if (!hasValue) return null;
        return (
          <Box key={field}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.75 }}>
              {label}
            </Typography>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  md: "repeat(2, minmax(0, 1fr))",
                },
                gap: 1,
              }}
            >
              {[
                { title: "Baseline", value: before },
                { title: "Candidate", value: after },
              ].map((item) => (
                <Paper
                  key={item.title}
                  variant="outlined"
                  sx={{ p: 1.5, borderRadius: 1.5 }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {item.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      mt: 0.5,
                      whiteSpace: "pre-wrap",
                      overflowWrap: "anywhere",
                    }}
                  >
                    {renderContent(item.value)}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </Box>
        );
      })}
    </Stack>
  );
}

function SnapshotComparison({ snapshot }: { snapshot: ExperimentSnapshot }) {
  const rows = comparisonRows(snapshot.comparison);
  const overall = isNumericComparison(snapshot.comparison.overall_score)
    ? snapshot.comparison.overall_score
    : null;
  const costGroup = snapshot.comparison.cost;
  const currency =
    costGroup &&
    typeof costGroup === "object" &&
    typeof (costGroup as Record<string, unknown>).currency === "string"
      ? (costGroup as Record<string, string>).currency
      : undefined;
  const baselineName = runName(snapshot, snapshot.run_ids[0]);
  const candidateName = runName(snapshot, snapshot.run_ids[1]);

  return (
    <Stack spacing={2.5}>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={1.5}
        sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}
      >
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            Comparison
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Saved {formatDate(snapshot.created_at)} · Version{" "}
            {snapshot.calculation_version}
          </Typography>
        </Box>
        <Chip
          icon={<CompareArrowsOutlined />}
          label={`${baselineName} → ${candidateName}`}
          variant="outlined"
        />
      </Stack>

      {overall && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" },
            gap: 1.5,
          }}
        >
          {[
            { label: "Baseline score", value: overall.baseline },
            { label: "Candidate score", value: overall.candidate },
            { label: "Score change", value: overall.delta, delta: true },
          ].map((item) => (
            <Paper
              key={item.label}
              variant="outlined"
              sx={{ p: 2, borderRadius: 2 }}
            >
              <Typography variant="body2" color="text.secondary">
                {item.label}
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  mt: 0.75,
                  fontWeight: 700,
                  color: item.delta
                    ? item.value > 0
                      ? "success.main"
                      : item.value < 0
                        ? "error.main"
                        : "text.primary"
                    : "text.primary",
                }}
              >
                {item.delta && item.value > 0 ? "+" : ""}
                {item.value.toFixed(4)}
              </Typography>
            </Paper>
          ))}
        </Box>
      )}

      {rows.length === 0 ? (
        <Alert severity="info">
          This snapshot does not contain comparable numeric metrics.
        </Alert>
      ) : (
        <TableContainer
          component={Paper}
          variant="outlined"
          sx={{ borderRadius: 2 }}
        >
          <Table size="small" aria-label="Experiment comparison metrics">
            <TableHead>
              <TableRow>
                <TableCell>Category</TableCell>
                <TableCell>Metric</TableCell>
                <TableCell align="right">Baseline</TableCell>
                <TableCell align="right">Candidate</TableCell>
                <TableCell align="right">Change</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((row) => {
                const improvement = isImprovement(row);
                return (
                  <TableRow key={`${row.category}-${row.label}`} hover>
                    <TableCell sx={{ textTransform: "capitalize" }}>
                      {row.category.replaceAll("_", " ")}
                    </TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>
                      {row.label.replaceAll("_", " ")}
                    </TableCell>
                    <TableCell align="right">
                      {formatValue(
                        row.baseline,
                        row.label,
                        row.category === "cost" ? currency : undefined,
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {formatValue(
                        row.candidate,
                        row.label,
                        row.category === "cost" ? currency : undefined,
                      )}
                    </TableCell>
                    <TableCell
                      align="right"
                      sx={{
                        color:
                          row.delta === 0 || improvement === null
                            ? "text.secondary"
                            : improvement
                              ? "success.main"
                              : "error.main",
                        fontWeight: 600,
                      }}
                    >
                      {row.delta > 0 ? "+" : ""}
                      {formatValue(
                        row.delta,
                        row.label,
                        row.category === "cost" ? currency : undefined,
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      <FeedbackComparison snapshot={snapshot} />
      <Typography variant="caption" color="text.secondary">
        Positive score changes are improvements for quality metrics. Lower
        values are favorable for execution time, token use, and cost.
      </Typography>
    </Stack>
  );
}

export function ExperimentDetailPage() {
  const { experimentId } = useParams<{ experimentId: string }>();
  const selectedProjectId = useAppContextStore((state) => state.selectedProjectId);
  const { data: experiment, isLoading, isError } = useExperiment(experimentId);
  const {
    data: snapshots,
    isLoading: isSnapshotsLoading,
    isError: isSnapshotsError,
    refetch: refetchSnapshots,
  } = useExperimentSnapshots(experimentId);
  const { data: runs, isLoading: isRunsLoading } = useEvaluationRuns({
    projectId:
      experiment?.project_id === selectedProjectId
        ? experiment.project_id
        : undefined,
  });
  const createSnapshot = useCreateExperimentSnapshot(experimentId ?? "");
  const [isSnapshotDialogOpen, setIsSnapshotDialogOpen] = useState(false);
  const [baselineRunId, setBaselineRunId] = useState("");
  const [candidateRunId, setCandidateRunId] = useState("");
  const [selectedSnapshotId, setSelectedSnapshotId] = useState("");
  const [snapshotPage, setSnapshotPage] = useState(0);
  const [snapshotPageSize, setSnapshotPageSize] = useState(25);
  const [formError, setFormError] = useState("");

  const completedRuns = useMemo(
    () => (runs ?? []).filter((run) => run.status === "completed"),
    [runs],
  );
  const selectedSnapshot =
    (snapshots ?? []).find((snapshot) => snapshot.id === selectedSnapshotId) ??
    snapshots?.[0];
  const paginatedSnapshots = (snapshots ?? []).slice(
    snapshotPage * snapshotPageSize,
    snapshotPage * snapshotPageSize + snapshotPageSize,
  );

  const submitSnapshot = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError("");
    if (!baselineRunId || !candidateRunId) {
      setFormError("Choose a baseline and candidate run.");
      return;
    }
    if (baselineRunId === candidateRunId) {
      setFormError("Choose two different evaluation runs.");
      return;
    }
    try {
      const snapshot = await createSnapshot.mutateAsync([
        baselineRunId,
        candidateRunId,
      ]);
      setSelectedSnapshotId(snapshot.id);
      setSnapshotPage(0);
      setIsSnapshotDialogOpen(false);
      setBaselineRunId("");
      setCandidateRunId("");
    } catch {
      // The mutation hook reports API errors.
    }
  };

  if (isLoading) return <LoadingState />;
  if (isError || !experiment) {
    return (
      <ErrorState
        title="Experiment could not be loaded"
        message="The experiment may have been removed, or the request failed."
      />
    );
  }

  if (!selectedProjectId || experiment.project_id !== selectedProjectId) {
    return (
      <Stack spacing={3}>
        <AppBreadcrumbs
          items={[
            { label: "Experiments", to: "/experiments" },
            { label: experiment.name },
          ]}
        />
        <Alert severity="info">
          This experiment is outside the selected project. Choose its project from the Dashboard to view its snapshots and runs.
        </Alert>
      </Stack>
    );
  }

  const runOption = (run: EvaluationRun) =>
    `${run.name} · ${run.evaluation_type.toUpperCase()} · ${run.completed_cases}/${run.total_cases} cases`;

  return (
    <Stack spacing={3}>
      <AppBreadcrumbs
        items={[
          { label: "Experiments", to: "/experiments" },
          { label: experiment.name },
        ]}
      />

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}
      >
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="h5"
            sx={{ fontWeight: 700, overflowWrap: "anywhere" }}
          >
            {experiment.name}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 0.5, overflowWrap: "anywhere" }}
          >
            {experiment.description ||
              "Compare completed evaluation runs and keep a history of their results."}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={() => void refetchSnapshots()}
            disabled={isSnapshotsLoading}
            sx={{ textTransform: "none" }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            disableElevation
            startIcon={<AddchartOutlined />}
            onClick={() => setIsSnapshotDialogOpen(true)}
            sx={{ textTransform: "none" }}
          >
            Compare runs
          </Button>
        </Stack>
      </Stack>

      {isSnapshotsError && (
        <Alert severity="error">Snapshot history could not be loaded.</Alert>
      )}

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "280px minmax(0, 1fr)" },
          gap: 2,
        }}
      >
        <Paper
          variant="outlined"
          sx={{ borderRadius: 3, overflow: "hidden", alignSelf: "start" }}
        >
          <Stack
            direction="row"
            spacing={1}
            sx={{
              p: 2,
              alignItems: "center",
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            <HistoryOutlined fontSize="small" color="action" />
            <Typography variant="subtitle1" sx={{ fontWeight: 700, flex: 1 }}>
              Snapshot history
            </Typography>
            <Chip
              size="small"
              label={snapshots?.length ?? 0}
              variant="outlined"
            />
          </Stack>
          {isSnapshotsLoading ? (
            <Box sx={{ p: 2 }}>
              <LoadingState />
            </Box>
          ) : (snapshots?.length ?? 0) === 0 ? (
            <Box sx={{ p: 1.5 }}>
              <EmptyState
                title="No snapshots yet"
                description="Compare two completed runs to save the first snapshot."
              />
            </Box>
          ) : (
            <Stack divider={<Divider />}>
              {paginatedSnapshots.map((snapshot) => (
                <Button
                  key={snapshot.id}
                  onClick={() => setSelectedSnapshotId(snapshot.id)}
                  sx={{
                    p: 1.75,
                    borderRadius: 0,
                    textAlign: "left",
                    justifyContent: "flex-start",
                    bgcolor:
                      selectedSnapshot?.id === snapshot.id
                        ? "action.selected"
                        : "transparent",
                    color: "text.primary",
                    textTransform: "none",
                  }}
                >
                  <Stack spacing={0.5} sx={{ width: "100%", minWidth: 0 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {runName(snapshot, snapshot.run_ids[1])}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      vs. {runName(snapshot, snapshot.run_ids[0])}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(snapshot.created_at)}
                    </Typography>
                  </Stack>
                </Button>
              ))}
            </Stack>
          )}
          {(snapshots?.length ?? 0) > 25 && (
            <DataTablePagination
              page={snapshotPage}
              pageSize={snapshotPageSize}
              total={snapshots?.length ?? 0}
              onPageChange={setSnapshotPage}
              onPageSizeChange={(value) => {
                setSnapshotPageSize(value);
                setSnapshotPage(0);
              }}
            />
          )}
        </Paper>

        <Paper
          variant="outlined"
          sx={{ p: { xs: 2, sm: 2.5 }, borderRadius: 3, minWidth: 0 }}
        >
          {selectedSnapshot ? (
            <SnapshotComparison snapshot={selectedSnapshot} />
          ) : (
            <EmptyState
              title="Choose a comparison"
              description="Select a saved snapshot or compare two completed runs to see their metrics side by side."
            />
          )}
        </Paper>
      </Box>

      <Dialog
        open={isSnapshotDialogOpen}
        onClose={() =>
          !createSnapshot.isPending && setIsSnapshotDialogOpen(false)
        }
        fullWidth
        maxWidth="sm"
      >
        <Box component="form" onSubmit={submitSnapshot}>
          <DialogTitle>Compare completed runs</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                The baseline is compared with the candidate. Both runs must be
                completed and have saved summaries.
              </Typography>
              {formError && <Alert severity="error">{formError}</Alert>}
              {!isRunsLoading && completedRuns.length < 2 && (
                <Alert severity="info">
                  At least two completed evaluation runs are needed to create a
                  comparison.
                </Alert>
              )}
              <TextField
                select
                label="Baseline run"
                value={baselineRunId}
                onChange={(event) => setBaselineRunId(event.target.value)}
                fullWidth
                disabled={isRunsLoading}
              >
                {completedRuns.map((run) => (
                  <MenuItem key={run.id} value={run.id}>
                    {runOption(run)}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Candidate run"
                value={candidateRunId}
                onChange={(event) => setCandidateRunId(event.target.value)}
                fullWidth
                disabled={isRunsLoading}
              >
                {completedRuns
                  .filter((run) => run.id !== baselineRunId)
                  .map((run) => (
                    <MenuItem key={run.id} value={run.id}>
                      {runOption(run)}
                    </MenuItem>
                  ))}
              </TextField>
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 2.5, pt: 0 }}>
            <Button
              onClick={() => setIsSnapshotDialogOpen(false)}
              disabled={createSnapshot.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={
                createSnapshot.isPending ||
                isRunsLoading ||
                completedRuns.length < 2 ||
                !baselineRunId ||
                !candidateRunId
              }
            >
              {createSnapshot.isPending ? "Saving…" : "Save comparison"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Stack>
  );
}
