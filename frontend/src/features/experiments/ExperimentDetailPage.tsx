import {
  AddchartOutlined,
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
  useTheme,
} from "@mui/material";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip as ChartTooltip, XAxis, YAxis } from "recharts";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { PermissionGate } from "../../components/common/PermissionGate";
import { StatusChip } from "../../components/common/StatusChip";
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

interface CategorySummary {
  category: string;
  metricDetails: ComparisonRow[];
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
    (id ? "Evaluation run" : "Unknown run")
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

function MetricScoreTooltip({
  active,
  payload,
  currency,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ComparisonRow }>;
  currency?: string;
}) {
  const metric = payload?.[0]?.payload;
  if (!active || !metric) return null;
  const improvement = isImprovement(metric);
  const deltaColor = metric.delta === 0 || improvement === null
    ? "text.secondary"
    : improvement ? "success.main" : "error.main";

  return (
    <Paper variant="outlined" sx={{ p: 1.5, borderRadius: 2, width: 520, maxWidth: "min(520px, calc(100vw - 32px))", bgcolor: (theme) => theme.palette.background.paper, backgroundImage: "none", opacity: 1, boxShadow: 8 }}>
      <Typography variant="subtitle2" fontWeight={700} sx={{ textTransform: "capitalize", mb: 1 }}>
        {metric.label.replaceAll("_", " ")}
      </Typography>
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 1, mt: 1, pb: 0.5, borderBottom: 1, borderColor: "divider" }}>
        <Typography variant="caption" color="text.secondary" fontWeight={700}>Baseline</Typography>
        <Typography variant="caption" color="text.secondary" fontWeight={700}>Candidate</Typography>
        <Typography variant="caption" color="text.secondary" fontWeight={700}>Delta</Typography>
      </Box>
      <Box sx={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 1, pt: 0.75 }}>
        <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: "anywhere" }}>
          {formatValue(metric.baseline, metric.label, metric.category === "cost" ? currency : undefined)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: "anywhere" }}>
          {formatValue(metric.candidate, metric.label, metric.category === "cost" ? currency : undefined)}
        </Typography>
        <Typography variant="caption" fontWeight={700} color={deltaColor} sx={{ overflowWrap: "anywhere" }}>
          {metric.delta > 0 ? "+" : ""}{formatValue(metric.delta, metric.label, metric.category === "cost" ? currency : undefined)}
        </Typography>
      </Box>
    </Paper>
  );
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
  const feedbackItems = (value: unknown): string[] => {
    if (Array.isArray(value)) {
      return value.map(String).map((item) => item.trim()).filter(Boolean);
    }
    return typeof value === "string" && value.trim() ? [value.trim()] : [];
  };
  const feedbackChanges = feedbackFields.slice(1).reduce(
    (counts, [field]) => {
      const before = feedbackItems(baseline[field]);
      const after = feedbackItems(candidate[field]);
      const unmatchedBaseline = [...before];
      let shared = 0;
      after.forEach((item) => {
        const matchIndex = unmatchedBaseline.findIndex(
          (baselineItem) => baselineItem.toLocaleLowerCase() === item.toLocaleLowerCase(),
        );
        if (matchIndex >= 0) {
          unmatchedBaseline.splice(matchIndex, 1);
          shared += 1;
        }
      });
      return {
        shared: counts.shared + shared,
        baselineOnly: counts.baselineOnly + unmatchedBaseline.length,
        candidateOnly: counts.candidateOnly + after.length - shared,
      };
    },
    { shared: 0, baselineOnly: 0, candidateOnly: 0 },
  );
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
  const [open, setOpen] = useState(false);

  if (!hasFeedback) return null;

  return (
    <>
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="subtitle1" fontWeight={700}>Qualitative feedback</Typography>
            <Typography variant="body2" color="text.secondary">Read the baseline and candidate feedback side by side.</Typography>
          </Box>
          <Button variant="outlined" onClick={() => setOpen(true)}>View feedback</Button>
        </Stack>
      </Paper>
      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Qualitative feedback comparison</DialogTitle>
        <DialogContent dividers sx={{ maxHeight: "70vh" }}>
          <Stack spacing={2}>
            <Paper variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="subtitle1" fontWeight={700}>Feedback changes</Typography>
              <Typography variant="caption" color="text.secondary">
                Items are matched by exact wording across strengths, weaknesses, patterns, recommendations, and evaluator feedback.
              </Typography>
              <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" }, gap: 1.5, mt: 1.5 }}>
                {[
                  { label: "Shared wording", value: feedbackChanges.shared, color: "info.main", description: "Appears in both runs" },
                  { label: "Baseline only", value: feedbackChanges.baselineOnly, color: "text.secondary", description: "Not repeated by candidate" },
                  { label: "Candidate only", value: feedbackChanges.candidateOnly, color: "primary.main", description: "New or reworded feedback" },
                ].map((item) => (
                  <Paper key={item.label} variant="outlined" sx={{ p: 1.5, borderRadius: 1.5, minWidth: 0, bgcolor: "background.default" }}>
                    <Typography variant="caption" color="text.secondary">{item.label}</Typography>
                    <Typography variant="h5" sx={{ mt: 0.25, fontWeight: 700, color: item.color }}>{item.value}</Typography>
                    <Typography variant="caption" color="text.secondary">{item.description}</Typography>
                  </Paper>
                ))}
              </Box>
            </Paper>
      {feedbackFields.map(([field, label]) => {
        const before = feedbackItems(baseline[field]);
        const after = feedbackItems(candidate[field]);
        const hasValue = before.length > 0 || after.length > 0;
        if (!hasValue) return null;
        const baselineSet = new Set(before.map((item) => item.toLocaleLowerCase()));
        const candidateSet = new Set(after.map((item) => item.toLocaleLowerCase()));
        return (
          <Paper key={field} variant="outlined" sx={{ p: 2, borderRadius: 2 }}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1} alignItems={{ sm: "center" }} justifyContent="space-between" sx={{ mb: 1.5 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{label}</Typography>
              <Stack direction="row" spacing={1}>
                <Chip size="small" variant="outlined" label={`Baseline · ${before.length}`} />
                <Chip size="small" variant="outlined" color="info" label={`Candidate · ${after.length}`} />
              </Stack>
            </Stack>
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  md: "repeat(2, minmax(0, 1fr))",
                },
                gap: 1.5,
              }}
            >
              {[
                { title: "Baseline", items: before, otherRun: candidateSet, onlyLabel: "Baseline only", sharedLabel: "Also in candidate" },
                { title: "Candidate", items: after, otherRun: baselineSet, onlyLabel: "Candidate only", sharedLabel: "Also in baseline" },
              ].map((item) => (
                <Paper
                  key={item.title}
                  variant="outlined"
                  sx={{ p: 1.5, borderRadius: 1.5, minWidth: 0, bgcolor: "background.default" }}
                >
                  <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary" fontWeight={700}>{item.title}</Typography>
                    <Chip size="small" label={`${item.items.length} ${item.items.length === 1 ? "item" : "items"}`} />
                  </Stack>
                  {item.items.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">No feedback reported for this run.</Typography>
                  ) : (
                    <Stack spacing={1}>
                      {item.items.map((text, index) => {
                        const shared = item.otherRun.has(text.toLocaleLowerCase());
                        return (
                          <Box key={`${field}-${item.title}-${index}`} sx={{ p: 1.25, borderRadius: 1.5, bgcolor: "background.paper", border: 1, borderColor: "divider" }}>
                            <Stack direction="row" spacing={1} alignItems="flex-start">
                              <Chip size="small" label={`#${index + 1}`} variant="outlined" sx={{ flexShrink: 0, height: 22 }} />
                              <Box sx={{ minWidth: 0, flex: 1 }}>
                                <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>{text}</Typography>
                                <Typography variant="caption" color={shared ? "success.main" : "text.secondary"} sx={{ display: "block", mt: 0.75 }}>
                                  {shared ? item.sharedLabel : item.onlyLabel}
                                </Typography>
                              </Box>
                            </Stack>
                          </Box>
                        );
                      })}
                    </Stack>
                  )}
                </Paper>
              ))}
            </Box>
          </Paper>
        );
      })}
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setOpen(false)}>Close</Button></DialogActions>
      </Dialog>
    </>
  );
}

function SnapshotComparison({ snapshot }: { snapshot: ExperimentSnapshot }) {
  const theme = useTheme();
  const rows = comparisonRows(snapshot.comparison);
  const comparisonTableRows = rows.filter((row) => row.category !== "performance");
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
  const baselineRun = snapshot.run_results[snapshot.run_ids[0]]?.run;
  const candidateRun = snapshot.run_results[snapshot.run_ids[1]]?.run;
  const scoreChartData = overall ? [
    { run: "Baseline", score: overall.baseline },
    { run: "Candidate", score: overall.candidate },
  ] : [];
  const caseChartData = [
    { run: "Baseline", completed: baselineRun?.completed_cases ?? 0, failed: baselineRun?.failed_cases ?? 0, notApplicable: baselineRun?.not_applicable_cases ?? Math.max((baselineRun?.total_cases ?? 0) - (baselineRun?.completed_cases ?? 0) - (baselineRun?.failed_cases ?? 0), 0) },
    { run: "Candidate", completed: candidateRun?.completed_cases ?? 0, failed: candidateRun?.failed_cases ?? 0, notApplicable: candidateRun?.not_applicable_cases ?? Math.max((candidateRun?.total_cases ?? 0) - (candidateRun?.completed_cases ?? 0) - (candidateRun?.failed_cases ?? 0), 0) },
  ];
  const categorySummary = new Map<string, CategorySummary>();
  rows.forEach((row) => {
    const current = categorySummary.get(row.category) ?? {
      category: row.category.replaceAll("_", " "),
      metricDetails: [],
    };
    current.metricDetails.push(row);
    categorySummary.set(row.category, current);
  });
  const categoryChartData = [...categorySummary.values()].sort((left, right) => left.category.localeCompare(right.category));

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
          label={`${baselineName} → ${candidateName}`}
          variant="outlined"
        />
      </Stack>

      {overall && (
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" },
            gap: 2,
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
              sx={{ p: 2.5, borderRadius: 2, minWidth: 0 }}
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

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: overall ? "repeat(2, minmax(0, 1fr))" : "1fr" }, gap: 2 }}>
        {overall && <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 2, minWidth: 0 }}>
          <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>Overall score</Typography>
          <Box sx={{ width: "100%", height: 260, minWidth: 0 }}><ResponsiveContainer>
            <BarChart data={scoreChartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid stroke={theme.palette.divider} vertical={false} />
              <XAxis dataKey="run" tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary }} />
              <YAxis tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary }} />
              <ChartTooltip
                formatter={(value) => [Number(value).toFixed(4), "Score"]}
                contentStyle={{ backgroundColor: theme.palette.background.paper, color: theme.palette.text.primary, border: `1px solid ${theme.palette.divider}`, borderRadius: 8, boxShadow: "0 8px 24px rgba(15, 23, 42, 0.16)", opacity: 1 }}
                wrapperStyle={{ zIndex: 1500 }}
              />
              <Bar dataKey="score" name="Score" fill={theme.palette.primary.main} radius={[5, 5, 0, 0]} maxBarSize={54} />
            </BarChart>
          </ResponsiveContainer></Box>
        </Paper>}
        <Paper variant="outlined" sx={{ p: 2.5, borderRadius: 2, minWidth: 0 }}>
          <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>Case outcomes</Typography>
          <Box sx={{ width: "100%", height: 260, minWidth: 0 }}><ResponsiveContainer>
            <BarChart data={caseChartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid stroke={theme.palette.divider} vertical={false} />
              <XAxis dataKey="run" tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary }} />
              <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary }} />
              <ChartTooltip
                contentStyle={{ backgroundColor: theme.palette.background.paper, color: theme.palette.text.primary, border: `1px solid ${theme.palette.divider}`, borderRadius: 8, boxShadow: "0 8px 24px rgba(15, 23, 42, 0.16)", opacity: 1 }}
                wrapperStyle={{ zIndex: 1500 }}
              />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="completed" stackId="cases" name="Completed" fill={theme.palette.success.main} />
              <Bar dataKey="failed" stackId="cases" name="Failed" fill={theme.palette.error.main} />
              <Bar dataKey="notApplicable" stackId="cases" name="Not applicable" fill={theme.palette.grey[500]} radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer></Box>
        </Paper>
      </Box>

      {categoryChartData.length > 0 && (
        <Box>
          <Box sx={{ mb: 1.5 }}>
            <Typography variant="subtitle1" fontWeight={700}>Metrics by category</Typography>
            <Typography variant="body2" color="text.secondary">
              Compare each metric’s baseline and candidate values within its category.
            </Typography>
          </Box>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))", xl: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
            {categoryChartData.map((category) => (
              <Paper key={category.category} variant="outlined" sx={{ p: 2.5, borderRadius: 2, minWidth: 0 }}>
                <Typography variant="subtitle2" fontWeight={700} sx={{ textTransform: "capitalize", mb: 1.5 }}>
                  {category.category}
                </Typography>
                <Box sx={{ width: "100%", height: Math.min(360, Math.max(250, category.metricDetails.length * 38 + 90)), minWidth: 0 }}>
                  <ResponsiveContainer>
                    <BarChart data={category.metricDetails} layout="vertical" margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
                      <CartesianGrid stroke={theme.palette.divider} horizontal={false} />
                      <XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary }} />
                      <YAxis type="category" dataKey="label" width={92} tickFormatter={(value) => String(value).replaceAll("_", " ")} tickLine={false} axisLine={false} tick={{ fill: theme.palette.text.secondary, fontSize: 11 }} />
                      <ChartTooltip content={(props) => (
                        <MetricScoreTooltip
                          active={props.active}
                          payload={props.payload as unknown as Array<{ payload?: ComparisonRow }>}
                          currency={currency}
                        />
                      )} wrapperStyle={{ zIndex: 1500 }} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                      <Bar dataKey="baseline" name="Baseline" fill={theme.palette.primary.main} />
                      <Bar dataKey="candidate" name="Candidate" fill={theme.palette.info.main} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Paper>
            ))}
          </Box>
        </Box>
      )}

      {rows.length === 0 ? (
        <Alert severity="info">
          This snapshot does not contain comparable numeric metrics.
        </Alert>
      ) : comparisonTableRows.length > 0 ? (
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
              {comparisonTableRows.map((row) => {
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
      ) : null}
      <FeedbackComparison snapshot={snapshot} />
      <Typography variant="caption" color="text.secondary">
        Positive score changes are improvements for quality metrics. Lower
        values are favorable for execution time, token use, and cost.
      </Typography>
    </Stack>
  );
}


export function ExperimentDetailPage() {
  const theme = useTheme();
  const navigate = useNavigate();
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
  const [snapshotPageSize, setSnapshotPageSize] = useState(6);
  const [formError, setFormError] = useState("");

  const completedRuns = useMemo(
    () => (runs ?? []).filter((run) => run.status === "completed"),
    [runs],
  );
  const newestSnapshots = useMemo(
    () => [...(snapshots ?? [])].sort(
      (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
    ),
    [snapshots],
  );
  const selectedSnapshot =
    newestSnapshots.find((snapshot) => snapshot.id === selectedSnapshotId) ??
    newestSnapshots[0];
  const latestSnapshot = newestSnapshots[0];
  const paginatedSnapshots = newestSnapshots.slice(
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
  const overallComparison = latestSnapshot?.comparison.overall_score;
  const scoreDelta = isNumericComparison(overallComparison)
    ? overallComparison.delta
    : null;

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
          <Stack direction="row" spacing={1} useFlexGap sx={{ alignItems: "center", flexWrap: "wrap" }}>
            <Typography
              variant="h5"
              sx={{ fontWeight: 700, overflowWrap: "anywhere" }}
            >
              {experiment.name}
            </Typography>
            <StatusChip active={experiment.is_active} />
          </Stack>
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
          <PermissionGate permission="write"><Button
            variant="contained"
            disableElevation
            startIcon={<AddchartOutlined />}
            onClick={() => setIsSnapshotDialogOpen(true)}
            disabled={isRunsLoading || completedRuns.length < 2}
            title={completedRuns.length < 2 ? "Two completed runs are required" : "Compare completed runs"}
            sx={{ textTransform: "none" }}
          >
            Compare runs
          </Button></PermissionGate>
        </Stack>
      </Stack>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
        {[
          { label: "Saved comparisons", value: newestSnapshots.length, helper: "Historical snapshots" },
          { label: "Runs ready", value: completedRuns.length, helper: "Completed runs in this project" },
          { label: "Latest score change", value: scoreDelta === null ? "—" : `${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(4)}`, helper: latestSnapshot ? `From ${formatDate(latestSnapshot.created_at)}` : "Save a comparison to see the change" },
        ].map((metric) => (
          <Paper key={metric.label} variant="outlined" sx={{ p: 2, borderRadius: 2.5, minWidth: 0, height: "100%" }}>
            <Typography variant="caption" color="text.secondary">{metric.label}</Typography>
            <Typography variant="h6" fontWeight={700} noWrap title={String(metric.value)} sx={{ mt: 0.25 }}>{metric.value}</Typography>
            <Typography variant="caption" color="text.secondary" noWrap display="block">{metric.helper}</Typography>
          </Paper>
        ))}
      </Box>

      {completedRuns.length < 2 && !isRunsLoading && (
        <Alert
          severity="info"
          action={<Button color="inherit" size="small" onClick={() => navigate("/evaluations")}>View evaluations</Button>}
        >
          Complete at least two evaluation runs in this project to create a comparison.
        </Alert>
      )}

      {isSnapshotsError && (
        <Alert severity="error">Snapshot history could not be loaded.</Alert>
      )}

      <Stack spacing={2.5}>
        <Paper variant="outlined" sx={{ borderRadius: 3, overflow: "hidden", minWidth: 0 }}>
          <Stack
            direction="row"
            spacing={1}
            sx={{
              px: 2.5,
              py: 2,
              alignItems: "center",
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
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
            <Box sx={{ p: 2.5 }}>
              <LoadingState />
            </Box>
          ) : (snapshots?.length ?? 0) === 0 ? (
            <Box sx={{ p: 2.5 }}>
              <EmptyState
                title="No snapshots yet"
                description="Compare two completed runs to save the first snapshot."
              />
            </Box>
          ) : (
            <Box sx={{ p: 2, display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" }, gap: 1.5 }}>
              {paginatedSnapshots.map((snapshot, index) => (
                <Button
                  key={snapshot.id}
                  onClick={() => setSelectedSnapshotId(snapshot.id)}
                  sx={{
                    p: 2,
                    minHeight: 92,
                    border: 1,
                    borderColor: selectedSnapshot?.id === snapshot.id ? "primary.main" : "divider",
                    borderRadius: 2,
                    textAlign: "left",
                    justifyContent: "flex-start",
                    alignItems: "stretch",
                    bgcolor:
                      selectedSnapshot?.id === snapshot.id
                        ? "action.hover"
                        : "background.paper",
                    color: "text.primary",
                    textTransform: "none",
                    "&:hover": { borderColor: "primary.main", bgcolor: "action.hover" },
                  }}
                >
                  <Stack spacing={0.75} sx={{ width: "100%", minWidth: 0 }}>
                    <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", minWidth: 0 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, flex: 1 }} noWrap>
                        {runName(snapshot, snapshot.run_ids[1])}
                      </Typography>
                      {index === 0 && snapshotPage === 0 && <Chip size="small" color="primary" label="Latest" />}
                    </Stack>
                    <Typography variant="caption" color="text.secondary" noWrap>
                      Baseline: {runName(snapshot, snapshot.run_ids[0])}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ pt: 0.25 }}>
                      {formatDate(snapshot.created_at)}
                    </Typography>
                  </Stack>
                </Button>
              ))}
            </Box>
          )}
          {(snapshots?.length ?? 0) > snapshotPageSize && (
            <DataTablePagination
              page={snapshotPage}
              pageSize={snapshotPageSize}
              total={snapshots?.length ?? 0}
              pageSizeOptions={[6, 12, 24]}
              onPageChange={setSnapshotPage}
              onPageSizeChange={(value) => {
                setSnapshotPageSize(value);
                setSnapshotPage(0);
              }}
            />
          )}
        </Paper>

        <Paper variant="outlined" sx={{ p: { xs: 2, sm: 2.5 }, borderRadius: 3, minWidth: 0 }}>
          {selectedSnapshot ? (
            <SnapshotComparison snapshot={selectedSnapshot} />
          ) : (
            <EmptyState
              title="Choose a comparison"
              description="Choose a saved comparison from the history, or save a new comparison between two completed runs."
            />
          )}
        </Paper>
      </Stack>

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
                Pick a reference run and a candidate run. The saved snapshot shows score, case, performance, and cost changes between them.
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
                label="Baseline (reference)"
                value={baselineRunId}
                onChange={(event) => setBaselineRunId(event.target.value)}
                fullWidth
                disabled={isRunsLoading}
                helperText="The candidate run will be compared against this run."
              >
                {completedRuns.map((run) => (
                  <MenuItem key={run.id} value={run.id}>
                    {runOption(run)}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Candidate (new version)"
                value={candidateRunId}
                onChange={(event) => setCandidateRunId(event.target.value)}
                fullWidth
                disabled={isRunsLoading}
                helperText="Choose a different completed run to compare."
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
            <PermissionGate permission="write"><Button
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
            </Button></PermissionGate>
          </DialogActions>
        </Box>
      </Dialog>
    </Stack>
  );
}
