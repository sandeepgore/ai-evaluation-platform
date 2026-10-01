import { AddOutlined } from "@mui/icons-material";
import { Button, Stack, Typography } from "@mui/material";
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

  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  const [sortField, setSortField] = useState<SortField>("position");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const allCases = useMemo(() => cases ?? [], [cases]);

  const sortedCases = useMemo(() => {
    return [...allCases].sort((a, b) => {
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
  }, [allCases, sortField, sortDirection]);

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
            Cases
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage evaluation cases for Dataset Version v{version.version}.
          </Typography>
        </Stack>

        {editable && (
          <Button
            variant="contained"
            startIcon={<AddOutlined />}
            onClick={() => setCreateOpen(true)}
          >
            Add Case
          </Button>
        )}
      </Stack>

      {allCases.length === 0 ? (
        <Stack>
          <EmptyState
            title="No cases yet"
            description={
              editable
                ? "Add the first case to this draft dataset version."
                : "This dataset version does not contain any cases."
            }
          />
        </Stack>
      ) : (
        <Stack spacing={0}>
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

          <DataTablePagination
            page={currentPage}
            pageSize={pageSize}
            total={totalCases}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
          />
        </Stack>
      )}

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
