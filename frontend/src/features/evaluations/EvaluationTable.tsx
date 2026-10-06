import { VisibilityOutlined } from "@mui/icons-material";
import {
  Box,
  Chip,
  IconButton,
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

const statusConfig: Record<
  EvaluationRun["status"],
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
  pending: {
    label: "Pending",
    color: "default",
  },
  running: {
    label: "Running",
    color: "info",
  },
  completed: {
    label: "Completed",
    color: "success",
  },
  failed: {
    label: "Failed",
    color: "error",
  },
  cancelled: {
    label: "Cancelled",
    color: "warning",
  },
};

function formatDuration(durationMs: number | null): string {
  if (durationMs === null) {
    return "—";
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  const seconds = durationMs / 1000;

  if (seconds < 60) {
    return `${seconds.toFixed(1)} s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);

  return `${minutes}m ${remainingSeconds}s`;
}

function formatCreatedAt(createdAt: string): string {
  return new Date(createdAt).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getProcessedCases(run: EvaluationRun): number {
  return run.completed_cases + run.failed_cases + run.not_applicable_cases;
}

export function EvaluationTable({
  runs,
  modelNames,
  sortField,
  sortDirection,
  onSort,
  onView,
}: EvaluationTableProps) {
  const renderSortLabel = (field: EvaluationSortField, label: string) => (
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
        borderRadius: 0,
        border: 0,
        overflowX: "auto",
      }}
    >
      <Table sx={{ minWidth: 1000 }}>
        <TableHead>
          <TableRow sx={{ bgcolor: "action.hover" }}>
            <TableCell sx={{ minWidth: 160 }}>
              {renderSortLabel("name", "Evaluation")}
            </TableCell>

            <TableCell sx={{ width: 110 }}>
              {renderSortLabel("evaluation_type", "Type")}
            </TableCell>

            <TableCell sx={{ width: 120 }}>
              {renderSortLabel("status", "Status")}
            </TableCell>

            <TableCell sx={{ width: 100 }}>
              {renderSortLabel("completed_cases", "Completed")}
            </TableCell>

            <TableCell sx={{ width: 90 }}>
              {renderSortLabel("failed_cases", "Failed")}
            </TableCell>

            <TableCell sx={{ width: 80 }}>
              {renderSortLabel("not_applicable_cases", "N/A")}
            </TableCell>

            <TableCell sx={{ minWidth: 160 }}>
              {renderSortLabel("total_cases", "Progress")}
            </TableCell>

            <TableCell sx={{ minWidth: 140 }}>
              {renderSortLabel("model", "Model")}
            </TableCell>

            <TableCell sx={{ width: 110 }}>
              {renderSortLabel("duration_ms", "Duration")}
            </TableCell>

            <TableCell sx={{ minWidth: 160 }}>
              {renderSortLabel("created_at", "Created")}
            </TableCell>

            <TableCell align="right" sx={{ width: 80 }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {runs.map((run) => {
            const modelName = modelNames[run.model_id] ?? "Unknown model";

            const isPending = run.status === "pending";

            const processedCases = getProcessedCases(run);

            const progressPercentage =
              run.total_cases > 0
                ? Math.min(100, (processedCases / run.total_cases) * 100)
                : 0;

            const status = statusConfig[run.status] ?? {
              label: run.status,
              color: "default",
            };

            return (
              <TableRow
                key={run.id}
                hover
                sx={{
                  "&:last-child td, &:last-child th": {
                    border: 0,
                  },
                  transition: "background-color 0.2s ease",
                }}
              >
                {/* Name */}
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {run.name}
                  </Typography>
                </TableCell>
                {/* Type */}
                <TableCell>
                  <Chip
                    label={
                      evaluationTypeLabels[run.evaluation_type] ??
                      run.evaluation_type
                    }
                    size="small"
                    variant="outlined"
                    sx={{
                      borderRadius: 1.5,
                      fontSize: "0.75rem",
                      fontWeight: 600,
                    }}
                  />
                </TableCell>
                {/* Status */}
                <TableCell>
                  <Chip
                    label={status.label}
                    size="small"
                    color={status.color}
                    sx={{
                      fontWeight: 600,
                      fontSize: "0.75rem",
                      borderRadius: 1.5,
                    }}
                  />
                </TableCell>
                {/* Completed */}
                <TableCell>
                  <Tooltip
                    title={
                      isPending
                        ? "Evaluation has not started"
                        : `${run.completed_cases} completed cases`
                    }
                  >
                    <Typography
                      variant="body2"
                      color={
                        run.completed_cases > 0
                          ? "success.main"
                          : "text.secondary"
                      }
                      sx={{
                        whiteSpace: "nowrap",
                        fontWeight: 600,
                      }}
                    >
                      {isPending ? "—" : `✓ ${run.completed_cases}`}
                    </Typography>
                  </Tooltip>
                </TableCell>
                {/* Failed */}
                <TableCell>
                  <Tooltip
                    title={
                      isPending
                        ? "Evaluation has not started"
                        : `${run.failed_cases} failed cases`
                    }
                  >
                    <Typography
                      variant="body2"
                      color={
                        run.failed_cases > 0 ? "error.main" : "text.secondary"
                      }
                      sx={{
                        whiteSpace: "nowrap",
                        fontWeight: 600,
                      }}
                    >
                      {isPending ? "—" : `✕ ${run.failed_cases}`}
                    </Typography>
                  </Tooltip>
                </TableCell>
                {/* N/A */}
                <TableCell>
                  <Tooltip
                    title={
                      isPending
                        ? "Evaluation has not started"
                        : `${run.not_applicable_cases} not applicable cases`
                    }
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        whiteSpace: "nowrap",
                      }}
                    >
                      {isPending ? "—" : run.not_applicable_cases}
                    </Typography>
                  </Tooltip>
                </TableCell>
                {/* Progress */}
                <TableCell>
                  <Tooltip
                    title={
                      isPending
                        ? "Evaluation has not started"
                        : `${processedCases} of ${run.total_cases} cases processed`
                    }
                  >
                    <Box
                      sx={{
                        width: "100%",
                        maxWidth: 140,
                      }}
                    >
                      <Stack
                        direction="row"
                        sx={{
                          justifyContent: "space-between",
                          alignItems: "center",
                          mb: 0.5,
                        }}
                      >
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{
                            fontWeight: 600,
                            fontSize: "0.75rem",
                          }}
                        >
                          {isPending
                            ? "Not started"
                            : `${processedCases} / ${run.total_cases}`}
                        </Typography>
                      </Stack>

                      {!isPending && (
                        <LinearProgress
                          variant="determinate"
                          value={progressPercentage}
                          color={run.status === "failed" ? "error" : "primary"}
                          sx={{
                            height: 6,
                            borderRadius: 3,
                            bgcolor: (theme) =>
                              alpha(theme.palette.text.primary, 0.08),
                          }}
                        />
                      )}
                    </Box>
                  </Tooltip>
                </TableCell>
                {/* Model */}
                <TableCell>
                  <Tooltip
                    title={
                      modelName === "Unknown model"
                        ? "The model associated with this evaluation could not be found."
                        : modelName
                    }
                  >
                    <Typography
                      variant="body2"
                      color={
                        modelName === "Unknown model"
                          ? "text.disabled"
                          : "text.primary"
                      }
                      sx={{
                        maxWidth: 150,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {modelName}
                    </Typography>
                  </Tooltip>
                </TableCell>
                {/* Duration */}
                <TableCell>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      fontFamily: "monospace",
                      fontSize: "0.8125rem",
                    }}
                  >
                    {formatDuration(run.duration_ms)}
                  </Typography>
                </TableCell>
                {/* Created */}
                <TableCell>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      whiteSpace: "nowrap",
                      fontSize: "0.8125rem",
                    }}
                  >
                    {formatCreatedAt(run.created_at)}
                  </Typography>
                </TableCell>
                {/* Actions */}
                <TableCell
                  align="right"
                  sx={{
                    width: 80,
                    minWidth: 80,
                    p: 1,
                    position: "sticky",
                    right: 0,
                    zIndex: 2,
                    bgcolor: "background.paper",
                    visibility: "visible",
                    opacity: 1,
                  }}
                >
                  <Tooltip title="View evaluation details">
                    <IconButton
                      aria-label={`View ${run.name}`}
                      onClick={() => onView(run)}
                      size="small"
                      color="primary"
                      sx={{
                        display: "inline-flex",
                        visibility: "visible",
                        opacity: 1,
                      }}
                    >
                      <VisibilityOutlined
                        fontSize="small"
                        sx={{ display: "block", visibility: "visible" }}
                      />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
