import { AddOutlined, SearchOutlined } from "@mui/icons-material";
import {
  Box,
  Button,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { DataTablePagination } from "../../components/common/DataTablePagination";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAppContextStore } from "../../store/appContextStore";
import { useModels } from "../models/hooks";
import type { EvaluationRun } from "./api";
import {
  EvaluationTable,
  type EvaluationSortDirection,
  type EvaluationSortField,
} from "./EvaluationTable";
import { useEvaluationRuns } from "./hooks";

const DEFAULT_PAGE_SIZE = 25;

export function EvaluationListPage() {
  const navigate = useNavigate();

  const selectedProjectId = useAppContextStore(
    (state) => state.selectedProjectId,
  );

  const {
    data: runs,
    isLoading: isRunsLoading,
    isError: isRunsError,
  } = useEvaluationRuns();

  const { data: models } = useModels(selectedProjectId);

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [searchQuery, setSearchQuery] = useState("");

  const [sortField, setSortField] = useState<EvaluationSortField>("created_at");

  const [sortDirection, setSortDirection] =
    useState<EvaluationSortDirection>("desc");

  const allRuns = useMemo(() => runs ?? [], [runs]);

  const modelNames = useMemo(
    () =>
      Object.fromEntries((models ?? []).map((model) => [model.id, model.name])),
    [models],
  );

  const filteredRuns = useMemo(() => {
    if (!searchQuery.trim()) {
      return allRuns;
    }

    const query = searchQuery.toLowerCase().trim();

    return allRuns.filter((run) => {
      const modelName = modelNames[run.model_id] ?? "";

      return (
        run.name.toLowerCase().includes(query) ||
        run.evaluation_type.toLowerCase().includes(query) ||
        run.status.toLowerCase().includes(query) ||
        modelName.toLowerCase().includes(query)
      );
    });
  }, [allRuns, searchQuery, modelNames]);

  const sortedRuns = useMemo(() => {
    return [...filteredRuns].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case "name":
          comparison = a.name.localeCompare(b.name);
          break;

        case "evaluation_type":
          comparison = a.evaluation_type.localeCompare(b.evaluation_type);
          break;

        case "status":
          comparison = a.status.localeCompare(b.status);
          break;

        case "completed_cases":
          comparison = a.completed_cases - b.completed_cases;
          break;

        case "model":
          comparison = (
            modelNames[a.model_id] ?? "Unknown model"
          ).localeCompare(modelNames[b.model_id] ?? "Unknown model");
          break;

        case "duration_ms":
          comparison = (a.duration_ms ?? -1) - (b.duration_ms ?? -1);
          break;

        case "created_at":
          comparison =
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredRuns, modelNames, sortField, sortDirection]);

  const totalRuns = sortedRuns.length;

  const totalPages = Math.max(1, Math.ceil(totalRuns / pageSize));

  const currentPage = Math.min(page, totalPages - 1);

  const visibleRuns = sortedRuns.slice(
    currentPage * pageSize,
    currentPage * pageSize + pageSize,
  );

  useEffect(() => {
    if (page !== currentPage) {
      setPage(currentPage);
    }
  }, [page, currentPage]);

  const handleSort = (field: EvaluationSortField) => {
    if (sortField === field) {
      setSortDirection((currentDirection) =>
        currentDirection === "asc" ? "desc" : "asc",
      );
    } else {
      setSortField(field);
      setSortDirection("asc");
    }

    setPage(0);
  };

  const handlePageSizeChange = (nextPageSize: number) => {
    setPageSize(nextPageSize);
    setPage(0);
  };

  const handleView = (run: EvaluationRun) => {
    navigate(`/evaluations/${run.id}`);
  };

  const handleCreate = () => {
    navigate("/evaluations/new");
  };

  if (isRunsLoading) {
    return <LoadingState />;
  }

  if (isRunsError) {
    return <ErrorState />;
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{
          alignItems: { xs: "stretch", sm: "center" },
          justifyContent: "space-between",
        }}
      >
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Evaluations
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage and review model evaluation runs and test performance.
          </Typography>
        </Stack>

        <Button
          variant="contained"
          disableElevation
          startIcon={<AddOutlined />}
          onClick={handleCreate}
          sx={{
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
            px: 2.5,
          }}
        >
          Create Evaluation
        </Button>
      </Stack>

      {/* Main Content Area */}
      {allRuns.length === 0 ? (
        <Paper
          variant="outlined"
          sx={{
            borderRadius: 3,
            p: 4,
            textAlign: "center",
          }}
        >
          <EmptyState
            title="No evaluations yet"
            description="Create your first evaluation run to benchmark and score model responses."
          />

          <Button
            variant="outlined"
            startIcon={<AddOutlined />}
            onClick={handleCreate}
            sx={{
              mt: 2,
              borderRadius: 2,
              textTransform: "none",
              fontWeight: 600,
            }}
          >
            Create First Evaluation
          </Button>
        </Paper>
      ) : (
        <Paper
          variant="outlined"
          sx={{
            borderRadius: 3,
            overflow: "hidden",
            borderColor: "divider",
          }}
        >
          {/* Toolbar with Search */}
          <Box
            sx={{
              p: 2,
              borderBottom: 1,
              borderColor: "divider",
              bgcolor: "background.neutral",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <TextField
              size="small"
              placeholder="Search evaluations..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(0);
              }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchOutlined fontSize="small" color="action" />
                    </InputAdornment>
                  ),
                  sx: {
                    borderRadius: 2,
                    bgcolor: "background.paper",
                    width: {
                      xs: "100%",
                      sm: 300,
                    },
                  },
                },
              }}
            />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600 }}
            >
              Showing {visibleRuns.length} of {totalRuns}{" "}
              {totalRuns === 1 ? "run" : "runs"}
            </Typography>
          </Box>

          {/* Table */}
          <EvaluationTable
            runs={visibleRuns}
            modelNames={modelNames}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
            onView={handleView}
          />

          {/* Pagination Footer */}
          <DataTablePagination
            page={currentPage}
            pageSize={pageSize}
            total={totalRuns}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
          />
        </Paper>
      )}
    </Stack>
  );
}
