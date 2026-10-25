import {
  Box,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from "@mui/material";
import { VisibilityOutlined } from "@mui/icons-material";
import { DataTableSortLabel, type SortDirection } from "../../../components/common/DataTableSortLabel";
import { StatusChip } from "../../../components/common/StatusChip";
import { TableActionButton } from "../../../components/common/TableActionButton";

import type { EvaluationResult } from "../api";

interface EvaluationResultsTableProps {
  results: EvaluationResult[];
  total: number;
  page: number;
  pageSize: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onInspect: (result: EvaluationResult) => void;
  sortField?: "status" | "created_at" | "latency_ms";
  sortDirection?: SortDirection;
  onSort?: (field: "status" | "created_at" | "latency_ms") => void;
}

function formatDate(value: string): string {
  const date = new Date(value);

  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function formatLatency(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toLocaleString()} ms`;
}

function getOverallScore(result: EvaluationResult): number | null {
  const overall = result.scores?.overall;
  if (!overall || typeof overall !== "object") return null;
  const score = (overall as Record<string, unknown>).score;
  return typeof score === "number" && Number.isFinite(score)
    ? Math.min(1, Math.max(0, score))
    : null;
}

function isOverallNotApplicable(result: EvaluationResult): boolean {
  const overall = result.scores?.overall;
  return Boolean(
    overall &&
      typeof overall === "object" &&
      (overall as Record<string, unknown>).status === "not_applicable",
  );
}

export default function EvaluationResultsTable({
  results,
  total,
  page,
  pageSize,
  loading = false,
  onPageChange,
  onPageSizeChange,
  onInspect,
  sortField = "created_at",
  sortDirection = "desc",
  onSort = () => undefined,
}: EvaluationResultsTableProps) {
  return (
    <Paper variant="outlined">
      <TableContainer sx={{ width: "100%", overflowX: "hidden" }}>
        <Table size="small" aria-label="Evaluation results" sx={{ width: "100%", tableLayout: "fixed" }}>
          <TableHead>
            <TableRow>
              <TableCell><DataTableSortLabel field="status" activeField={sortField} direction={sortDirection} label="Status" onSort={onSort} /></TableCell>
              <TableCell>Overall score</TableCell>
              <TableCell>Case input</TableCell>
              <TableCell>Feedback / error</TableCell>
              <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" } }}><DataTableSortLabel field="latency_ms" activeField={sortField} direction={sortDirection} label="Latency" onSort={onSort} /></TableCell>
              <TableCell sx={{ display: { xs: "none", md: "table-cell" } }}><DataTableSortLabel field="created_at" activeField={sortField} direction={sortDirection} label="Created" onSort={onSort} /></TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {!loading && results.length === 0 && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Box sx={{ py: 5, textAlign: "center" }}>
                    <Typography color="text.secondary">
                      No evaluation results found.
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}

            {results.map((result) => (
              <TableRow key={result.id} hover>
                <TableCell>
                  <StatusChip status={result.status} />
                </TableCell>

                <TableCell sx={{ minWidth: 0, width: { xs: "18%", sm: "16%" } }}>
                  {(() => {
                    const score = getOverallScore(result);
                    if (isOverallNotApplicable(result)) {
                      return <StatusChip status="not_applicable" label="Not applicable" />;
                    }
                    if (score === null) {
                      return <Typography variant="body2" color="text.secondary">—</Typography>;
                    }
                    return (
                      <Box sx={{ minWidth: 0 }}>
                        <Typography variant="body2" fontWeight={600}>{(score * 100).toFixed(1)}%</Typography>
                        <LinearProgress
                          variant="determinate"
                          value={score * 100}
                          color={score >= 0.8 ? "success" : score >= 0.5 ? "warning" : "error"}
                          sx={{ mt: 0.5, height: 5, borderRadius: 3 }}
                        />
                      </Box>
                    );
                  })()}
                </TableCell>

                <TableCell sx={{ minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    title={result.input ?? "No input available."}
                  >
                    {result.input || "No input available."}
                  </Typography>
                </TableCell>

                <TableCell sx={{ minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    color={result.error_message ? "error.main" : "text.primary"}
                    sx={{
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                    title={result.error_message ?? result.feedback ?? ""}
                  >
                    {result.error_message ?? result.feedback ?? "—"}
                  </Typography>
                </TableCell>

                <TableCell align="right" sx={{ display: { xs: "none", sm: "table-cell" }, whiteSpace: "nowrap" }}>
                  {formatLatency(result.latency_ms)}
                </TableCell>

                <TableCell sx={{ display: { xs: "none", md: "table-cell" }, whiteSpace: "nowrap" }}>
                  {formatDate(result.created_at)}
                </TableCell>

                <TableCell align="right">
                  <TableActionButton
                    label="Inspect result"
                    icon={<VisibilityOutlined fontSize="small" />}
                    onClick={() => onInspect(result)}
                  />
                </TableCell>
              </TableRow>
            ))}

            {loading && (
              <TableRow>
                <TableCell colSpan={7}>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ py: 3, textAlign: "center" }}
                  >
                    Loading evaluation results…
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={total}
        page={page}
        rowsPerPage={pageSize}
        onPageChange={(_, nextPage) => onPageChange(nextPage)}
        onRowsPerPageChange={(event) =>
          onPageSizeChange(Number(event.target.value))
        }
        rowsPerPageOptions={[10, 20, 50, 100]}
      />
    </Paper>
  );
}
