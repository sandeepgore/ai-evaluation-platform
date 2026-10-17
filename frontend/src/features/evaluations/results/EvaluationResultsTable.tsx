import {
  Box,
  Button,
  Chip,
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

function getStatusColor(
  status: string,
): "success" | "error" | "warning" | "default" {
  switch (status.toLowerCase()) {
    case "completed":
      return "success";
    case "failed":
      return "error";
    case "pending":
      return "warning";
    default:
      return "default";
  }
}

function formatDate(value: string): string {
  const date = new Date(value);

  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function formatLatency(value?: number | null): string {
  if (value == null) return "—";
  return `${value.toLocaleString()} ms`;
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
      <TableContainer sx={{ overflowX: "auto" }}>
        <Table size="small" aria-label="Evaluation results">
          <TableHead>
            <TableRow>
              <TableCell><DataTableSortLabel field="status" activeField={sortField} direction={sortDirection} label="Status" onSort={onSort} /></TableCell>
              <TableCell>Dataset case</TableCell>
              <TableCell>Feedback / error</TableCell>
              <TableCell align="right"><DataTableSortLabel field="latency_ms" activeField={sortField} direction={sortDirection} label="Latency" onSort={onSort} /></TableCell>
              <TableCell><DataTableSortLabel field="created_at" activeField={sortField} direction={sortDirection} label="Created" onSort={onSort} /></TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {!loading && results.length === 0 && (
              <TableRow>
                <TableCell colSpan={6}>
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
                  <Chip
                    size="small"
                    label={result.status.replaceAll("_", " ")}
                    color={getStatusColor(result.status)}
                    variant="outlined"
                  />
                </TableCell>

                <TableCell>
                  <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
                    {result.dataset_case_id}
                  </Typography>
                </TableCell>

                <TableCell sx={{ minWidth: 200, maxWidth: 360 }}>
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

                <TableCell align="right">
                  {formatLatency(result.latency_ms)}
                </TableCell>

                <TableCell sx={{ whiteSpace: "nowrap" }}>
                  {formatDate(result.created_at)}
                </TableCell>

                <TableCell align="right">
                  <Button
                    size="small"
                    startIcon={<VisibilityOutlined />}
                    onClick={() => onInspect(result)}
                  >
                    Inspect
                  </Button>
                </TableCell>
              </TableRow>
            ))}

            {loading && (
              <TableRow>
                <TableCell colSpan={6}>
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
