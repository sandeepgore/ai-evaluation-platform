import { AddOutlined, SearchOutlined } from "@mui/icons-material";
import {
  Box,
  Button,
  Chip,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { DataTablePagination } from "../../components/common/DataTablePagination";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { DatasetCaseCreateDialog } from "./DatasetCaseCreateDialog";
import { DatasetCaseDeleteDialog } from "./DatasetCaseDeleteDialog";
import { DatasetCaseEditDialog } from "./DatasetCaseEditDialog";
import { DatasetCaseTable } from "./DatasetCaseTable";
import { DatasetCaseViewDialog } from "./DatasetCaseViewDialog";
import type { DatasetCase } from "./api";
import { useDatasetCases } from "./hooks";
import { useDatasetVersion } from "../datasetVersions/hooks";
import { useDataset } from "../datasets/hooks";

type SortField =
  | "position"
  | "input"
  | "expected_output"
  | "has_reference"
  | "has_context";

type SortDirection = "asc" | "desc";

const DEFAULT_PAGE_SIZE = 25;

export function DatasetCaseListPage() {
  const { datasetId, versionId } = useParams<{
    datasetId: string;
    versionId: string;
  }>();

  const {
    data: version,
    isLoading: isVersionLoading,
    isError: isVersionError,
  } = useDatasetVersion(versionId ?? null);

  const {
    data: cases,
    isLoading: isCasesLoading,
    isError: isCasesError,
  } = useDatasetCases(versionId ?? null);

  const { data: dataset } = useDataset(datasetId ?? null);

  const [createOpen, setCreateOpen] = useState(false);
  const [viewCase, setViewCase] = useState<DatasetCase | null>(null);
  const [editCase, setEditCase] = useState<DatasetCase | null>(null);
  const [deleteCase, setDeleteCase] = useState<DatasetCase | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const [sortField, setSortField] = useState<SortField>("position");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const allCases = useMemo(() => cases ?? [], [cases]);

  const filteredCases = useMemo(() => {
    if (!searchQuery.trim()) return allCases;
    const query = searchQuery.toLowerCase().trim();
    return allCases.filter(
      (c) =>
        c.input.toLowerCase().includes(query) ||
        (c.expected_output && c.expected_output.toLowerCase().includes(query)),
    );
  }, [allCases, searchQuery]);

  const sortedCases = useMemo(() => {
    return [...filteredCases].sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case "position":
          comparison = a.position - b.position;
          break;

        case "input":
          comparison = a.input.localeCompare(b.input);
          break;

        case "expected_output":
          comparison = (a.expected_output ?? "").localeCompare(
            b.expected_output ?? "",
          );
          break;

        case "has_reference":
          comparison = Number(a.has_reference) - Number(b.has_reference);
          break;

        case "has_context":
          comparison = Number(a.has_context) - Number(b.has_context);
          break;
      }

      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [filteredCases, sortField, sortDirection]);

  if (!datasetId || !versionId) {
    return <ErrorState message="Dataset version information is missing." />;
  }

  if (isVersionLoading || isCasesLoading) {
    return <LoadingState message="Loading dataset cases..." />;
  }

  if (isVersionError || isCasesError || !version) {
    return <ErrorState message="Unable to load dataset cases." />;
  }

  const editable = version.status === "draft";
  const ready = version.status === "ready";

  const totalCases = sortedCases.length;
  const totalPages = Math.max(1, Math.ceil(totalCases / pageSize));
  const currentPage = Math.min(page, totalPages - 1);

  const visibleCases = sortedCases.slice(
    currentPage * pageSize,
    currentPage * pageSize + pageSize,
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
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

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
    setPage(0);
  };

  const statusColorMap = {
    draft: "warning",
    ready: "success",
    archived: "default",
  } as const;

  return (
    <Stack spacing={3}>
      <AppBreadcrumbs
        items={[
          {
            label: "Datasets",
            to: "/datasets",
          },
          {
            label: dataset?.name ?? "Dataset",
          },
          {
            label: `Version v${version.version}`,
            to: `/datasets/${datasetId}/versions`,
          },
          {
            label: "Cases",
          },
        ]}
      />

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
          <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Evaluation Cases
            </Typography>
            <Chip
              label={version.status.toUpperCase()}
              size="small"
              color={statusColorMap[version.status] ?? "default"}
              sx={{ fontWeight: 700, borderRadius: 1.5, fontSize: "0.7rem" }}
            />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Manage test cases and ground-truth expectations for Version v
            {version.version}.
          </Typography>
        </Stack>

        {editable && (
          <Button
            variant="contained"
            disableElevation
            startIcon={<AddOutlined />}
            onClick={() => setCreateOpen(true)}
            sx={{
              borderRadius: 2,
              textTransform: "none",
              fontWeight: 600,
              px: 2.5,
            }}
          >
            Add Case
          </Button>
        )}
      </Stack>

      {/* Main Content Area */}
      {allCases.length === 0 ? (
        <Paper
          variant="outlined"
          sx={{ borderRadius: 3, p: 4, textAlign: "center" }}
        >
          <EmptyState
            title="No cases in this version"
            description={
              editable
                ? "Get started by adding the first evaluation case to this draft version."
                : "This dataset version does not contain any cases."
            }
          />
          {editable && (
            <Button
              variant="outlined"
              startIcon={<AddOutlined />}
              onClick={() => setCreateOpen(true)}
              sx={{
                mt: 2,
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
              }}
            >
              Create First Case
            </Button>
          )}
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
          {/* Table Toolbar & Search Filter */}
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
              placeholder="Search inputs or outputs..."
              value={searchQuery}
              onChange={handleSearchChange}
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
                    width: { xs: "100%", sm: 300 },
                  },
                },
              }}
            />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600 }}
            >
              Showing {totalCases} {totalCases === 1 ? "case" : "cases"}
            </Typography>
          </Box>

          {/* Dataset Table */}
          <DatasetCaseTable
            cases={visibleCases}
            editable={editable}
            ready={ready}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
            onView={setViewCase}
            onEdit={setEditCase}
            onDelete={setDeleteCase}
          />

          {/* Pagination Controls */}
          <DataTablePagination
            page={currentPage}
            pageSize={pageSize}
            total={totalCases}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
          />
        </Paper>
      )}

      {/* Dialog Modals */}
      <DatasetCaseCreateDialog
        open={createOpen}
        datasetVersionId={versionId}
        onClose={() => setCreateOpen(false)}
      />

      <DatasetCaseViewDialog
        open={Boolean(viewCase)}
        datasetCase={viewCase}
        onClose={() => setViewCase(null)}
      />

      <DatasetCaseEditDialog
        open={Boolean(editCase)}
        datasetCase={editCase}
        onClose={() => setEditCase(null)}
      />

      <DatasetCaseDeleteDialog
        open={Boolean(deleteCase)}
        datasetCase={deleteCase}
        onClose={() => setDeleteCase(null)}
      />
    </Stack>
  );
}
