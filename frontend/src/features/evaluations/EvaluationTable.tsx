import { VisibilityOutlined } from "@mui/icons-material";
import {
  Box,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
  alpha,
} from "@mui/material";
import type { EvaluationRun } from "./api";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";

export type EvaluationSortField =
  | "name"
  | "evaluation_type"
  | "status"
  | "completed_cases"
  | "failed_cases"
  | "not_applicable_cases"
  | "total_cases"
  | "model"
  | "duration_ms"
  | "created_at";
export type EvaluationSortDirection = "asc" | "desc";

interface EvaluationTableProps {
  runs: EvaluationRun[];
  modelNames: Record<string, string>;
  sortField: EvaluationSortField;
  sortDirection: EvaluationSortDirection;
  onSort: (field: EvaluationSortField) => void;
  onView: (run: EvaluationRun) => void;
}

const evaluationTypeLabels: Record<EvaluationRun["evaluation_type"], string> = {
  text: "Text",
  rag: "RAG",
  conversation: "Conversation",
  safety: "Safety",
};

function formatDuration(durationMs: number | null): string {
  if (durationMs === null) return "—";
  if (durationMs < 1000) return `${durationMs} ms`;
  const seconds = durationMs / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${Math.round(seconds % 60)}s`;
}

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function EvaluationTable({
  runs,
  modelNames,
  sortField,
  sortDirection,
  onSort,
  onView,
}: EvaluationTableProps) {
  const sortLabel = (field: EvaluationSortField, label: string) => (
    <TableSortLabel
      active={sortField === field}
      direction={sortField === field ? sortDirection : "asc"}
      onClick={() => onSort(field)}
    >
      {label}
    </TableSortLabel>
  );

  return (
    <TableContainer
      component={Paper}
      variant="outlined"
      sx={{
        width: "100%",
        maxWidth: "100%",
        border: 0,
        borderRadius: 0,
        overflowX: "auto",
        overflowY: "auto",
        "&::-webkit-scrollbar": { height: 8 },
        "&::-webkit-scrollbar-thumb": {
          bgcolor: "action.disabled",
          borderRadius: 4,
        },
      }}
    >
      <Table size="small" sx={{ minWidth: 1200, tableLayout: "fixed" }}>
        <TableHead>
          <TableRow sx={{ bgcolor: "action.hover" }}>
            <TableCell sx={{ minWidth: 180 }}>{sortLabel("name", "Evaluation")}</TableCell>
            <TableCell sx={{ width: 110 }}>{sortLabel("evaluation_type", "Type")}</TableCell>
            <TableCell sx={{ width: 120 }}>{sortLabel("status", "Status")}</TableCell>
            <TableCell sx={{ minWidth: 200 }}>Case outcomes</TableCell>
            <TableCell sx={{ minWidth: 150 }}>{sortLabel("total_cases", "Progress")}</TableCell>
            <TableCell sx={{ minWidth: 140 }}>{sortLabel("model", "Model")}</TableCell>
            <TableCell sx={{ width: 110 }}>{sortLabel("duration_ms", "Duration")}</TableCell>
            <TableCell sx={{ minWidth: 155 }}>{sortLabel("created_at", "Created")}</TableCell>
            <TableCell
              align="right"
              sx={{
                width: 100,
                minWidth: 100,
                position: "sticky",
                right: 0,
                zIndex: 3,
                bgcolor: "action.hover",
              }}
            >
              Actions
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {runs.length === 0 && (
            <TableRow>
              <TableCell colSpan={9} align="center" sx={{ py: 5 }}>
                <Typography variant="body2" color="text.secondary">
                  No evaluations match your search.
                </Typography>
              </TableCell>
            </TableRow>
          )}
          {runs.map((run) => {
            const pending = run.status === "pending";
            const processed = run.completed_cases + run.failed_cases + run.not_applicable_cases;
            const progress = run.total_cases > 0
              ? Math.min(100, (processed / run.total_cases) * 100)
              : 0;
            const modelName = modelNames[run.model_id] ?? "Unknown model";
            return (
              <TableRow key={run.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight={600} sx={{ overflowWrap: "anywhere" }}>{run.name}</Typography>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={evaluationTypeLabels[run.evaluation_type] ?? run.evaluation_type} variant="outlined" />
                </TableCell>
                <TableCell>
                  <StatusChip status={run.status} />
                </TableCell>
                <TableCell>
                  {pending ? (
                    <Typography variant="body2" color="text.secondary">Not started</Typography>
                  ) : (
                    <Stack spacing={0.25}>
                      <Typography variant="body2" sx={{ whiteSpace: "nowrap" }}>
                        {run.completed_cases} completed · {run.failed_cases} failed
                      </Typography>
                      {run.not_applicable_cases > 0 && (
                        <Typography variant="caption" color="text.secondary">
                          {run.not_applicable_cases} not applicable
                        </Typography>
                      )}
                    </Stack>
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip title={pending ? "Evaluation has not started" : `${processed} of ${run.total_cases} cases processed`}>
                    <Box sx={{ maxWidth: 140 }}>
                      <Typography variant="caption" color="text.secondary">
                        {pending ? "Not started" : `${processed} of ${run.total_cases}`}
                      </Typography>
                      {!pending && (
                        <LinearProgress
                          variant="determinate"
                          value={progress}
                          color={run.status === "failed" ? "error" : "primary"}
                          sx={{ mt: 0.5, height: 6, borderRadius: 3, bgcolor: (theme) => alpha(theme.palette.text.primary, 0.08) }}
                        />
                      )}
                    </Box>
                  </Tooltip>
                </TableCell>
                <TableCell>
                  <Tooltip title={modelName}>
                    <Typography variant="body2" sx={{ maxWidth: 150, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {modelName}
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell><Typography variant="body2" color="text.secondary">{formatDuration(run.duration_ms)}</Typography></TableCell>
                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  <Typography variant="body2" color="text.secondary">{formatCreatedAt(run.created_at)}</Typography>
                </TableCell>
                <TableCell
                  align="right"
                  sx={{
                    width: 100,
                    minWidth: 100,
                    p: 1,
                    position: "sticky",
                    right: 0,
                    zIndex: 1,
                    bgcolor: "background.paper",
                  }}
                >
                  <TableActionButton
                    label={`View ${run.name}`}
                    icon={<VisibilityOutlined fontSize="small" />}
                    onClick={() => onView(run)}
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
