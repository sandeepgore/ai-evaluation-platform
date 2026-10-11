import ArrowBackOutlined from "@mui/icons-material/ArrowBackOutlined";
import RefreshOutlined from "@mui/icons-material/RefreshOutlined";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import EvaluationResultsFilters, {
  EvaluationResultStatusFilter,
} from "./results/EvaluationResultsFilters";
import {
  EvaluationResult,
  EvaluationResultStatistics,
  getEvaluationResultStatistics,
  listEvaluationResults,
} from "./api";
import EvaluationResultsStats from "./results/EvaluationResultsStats";
import EvaluationResultsTable from "./results/EvaluationResultsTable";
import EvaluationResultDetailsDrawer from "./results/EvaluationResultDetailsDrawer";

// import {
//   getEvaluationResultStatistics,
//   listEvaluationResults,
// } from "../api";
// import type {
//   EvaluationResult,
//   EvaluationResultStatistics,
// } from "../api";

// import {
//   EvaluationResultDetailsDrawer,
//   EvaluationResultsFilters,
//   EvaluationResultsStats,
//   EvaluationResultsTable,
// } from "../../components/evaluations/results";

// import type { EvaluationResultStatusFilter } from "../../components/evaluations/results";

const DEFAULT_PAGE_SIZE = 20;

export default function EvaluationResultsPage() {
  const { evaluationId } = useParams<{ evaluationId: string }>();
  const navigate = useNavigate();

  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<EvaluationResultStatusFilter>("all");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selectedResult, setSelectedResult] = useState<EvaluationResult | null>(
    null,
  );

  const statisticsQuery = useQuery<EvaluationResultStatistics>({
    queryKey: ["evaluation-result-statistics", evaluationId],
    queryFn: () => getEvaluationResultStatistics(evaluationId!),
    enabled: Boolean(evaluationId),
    staleTime: 15_000,
  });

  const resultsQuery = useQuery({
    queryKey: [
      "evaluation-results",
      evaluationId,
      statusFilter,
      page,
      pageSize,
    ],
    queryFn: () =>
      listEvaluationResults({
        evaluationRunId: evaluationId!,
        status: statusFilter === "all" ? undefined : statusFilter,
        offset: page * pageSize,
        limit: pageSize,
      }),
    enabled: Boolean(evaluationId),
    staleTime: 15_000,
  });

  const results = resultsQuery.data?.items ?? [];
  const total = resultsQuery.data?.total ?? 0;

  const filteredResults = useMemo(() => {
    const query = searchText.trim().toLowerCase();

    if (!query) {
      return results;
    }

    return results.filter((result: EvaluationResult) =>
      [
        result.dataset_case_id,
        result.id,
        result.error_message,
        result.feedback,
      ].some((value) => value?.toLowerCase().includes(query)),
    );
  }, [results, searchText]);

  const handleStatusChange = (value: EvaluationResultStatusFilter) => {
    setStatusFilter(value);
    setPage(0);
    setSelectedResult(null);
  };

  const handlePageSizeChange = (value: number) => {
    setPageSize(value);
    setPage(0);
  };

  const handleRefresh = () => {
    void resultsQuery.refetch();
    void statisticsQuery.refetch();
  };

  if (!evaluationId) {
    return (
      <Alert severity="error">
        An evaluation run ID is required to view results.
      </Alert>
    );
  }

  return (
    <Box sx={{ width: "100%", minWidth: 0 }}>
      <Stack spacing={3}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "stretch", sm: "center" },
            gap: 2,
          }}
        >
          <Box sx={{ minWidth: 0 }}>
            <Button
              startIcon={<ArrowBackOutlined />}
              onClick={() => navigate(`/evaluations/${evaluationId}`)}
              sx={{ mb: 1 }}
            >
              Back to evaluation
            </Button>

            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Evaluation results
            </Typography>

            <Typography variant="body2" color="text.secondary">
              Inspect individual case outputs, scores, evaluator feedback, and
              execution traces.
            </Typography>

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 1, overflowWrap: "anywhere" }}
            >
              Run ID: {evaluationId}
            </Typography>
          </Box>

          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
            disabled={resultsQuery.isFetching || statisticsQuery.isFetching}
            sx={{ alignSelf: { xs: "flex-start", sm: "center" } }}
          >
            Refresh
          </Button>
        </Stack>

        {statisticsQuery.isError && (
          <Alert
            severity="warning"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => void statisticsQuery.refetch()}
              >
                Retry
              </Button>
            }
          >
            Result statistics could not be loaded. The results table may still
            be available.
          </Alert>
        )}

        {resultsQuery.isError && (
          <Alert
            severity="error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={() => void resultsQuery.refetch()}
              >
                Retry
              </Button>
            }
          >
            Evaluation results could not be loaded. Please retry.
          </Alert>
        )}

        <EvaluationResultsStats
          statistics={statisticsQuery.data}
          loading={statisticsQuery.isPending}
        />

        <EvaluationResultsFilters
          searchText={searchText}
          statusFilter={statusFilter}
          onSearchChange={setSearchText}
          onStatusChange={handleStatusChange}
          disabled={resultsQuery.isPending && !resultsQuery.data}
        />

        {resultsQuery.isPending && !resultsQuery.data ? (
          <Stack
            direction="row"
            sx={{
              justifyContent: "center",
              alignItems: "center",
              gap: 1.5,
              py: 8,
            }}
          >
            <CircularProgress size={24} />
            <Typography color="text.secondary">
              Loading evaluation results…
            </Typography>
          </Stack>
        ) : (
          <EvaluationResultsTable
            results={filteredResults}
            total={total}
            page={page}
            pageSize={pageSize}
            loading={resultsQuery.isFetching}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
            onInspect={setSelectedResult}
          />
        )}

        <EvaluationResultDetailsDrawer
          result={selectedResult}
          open={Boolean(selectedResult)}
          onClose={() => setSelectedResult(null)}
        />
      </Stack>
    </Box>
  );
}
