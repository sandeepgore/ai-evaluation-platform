import {
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { DatasetVersionCreateDialog } from "./DatasetVersionCreateDialog";
import { DatasetVersionDeleteDialog } from "./DatasetVersionDeleteDialog";
import { DatasetVersionEditDialog } from "./DatasetVersionEditDialog";
import { DatasetVersionFinalizeDialog } from "./DatasetVersionFinalizeDialog";
import { DatasetVersionImportDialog } from "./DatasetVersionImportDialog";
import { DatasetVersionTable } from "./DatasetVersionTable";
import type { DatasetVersion, DatasetVersionStatus } from "./api";
import { useDatasetVersions } from "./hooks";
import { useDataset } from "../datasets/hooks";

type VersionStatusFilter = "all" | DatasetVersionStatus;

export function DatasetVersionListPage() {
  const navigate = useNavigate();
  const { datasetId } = useParams<{ datasetId: string }>();

  const { data, isLoading, isError } = useDatasetVersions(datasetId ?? null);
  const { data: dataset } = useDataset(datasetId ?? null);

  const [statusFilter, setStatusFilter] = useState<VersionStatusFilter>("all");

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [editingVersion, setEditingVersion] = useState<DatasetVersion | null>(
    null,
  );
  const [deletingVersion, setDeletingVersion] = useState<DatasetVersion | null>(
    null,
  );
  const [finalizingVersion, setFinalizingVersion] =
    useState<DatasetVersion | null>(null);

  if (!datasetId) {
    return <ErrorState message="Dataset ID is missing." />;
  }

  if (isLoading) {
    return <LoadingState message="Loading dataset versions..." />;
  }

  if (isError) {
    return <ErrorState message="Unable to load dataset versions." />;
  }

  const versions = data ?? [];

  const filteredVersions =
    statusFilter === "all"
      ? versions
      : versions.filter((version) => version.status === statusFilter);

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
            label: "Versions",
          },
        ]}
      />

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{
          justifyContent: "space-between",
          alignItems: { xs: "stretch", sm: "center" },
        }}
      >
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Dataset Versions
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage versions for this dataset.
          </Typography>
        </Stack>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.5}
          sx={{ alignItems: { xs: "stretch", sm: "center" } }}
        >
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel id="dataset-version-status-filter-label">
              Status
            </InputLabel>

            <Select
              labelId="dataset-version-status-filter-label"
              value={statusFilter}
              label="Status"
              onChange={(event) =>
                setStatusFilter(event.target.value as VersionStatusFilter)
              }
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="ready">Ready</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="archived">Archived</MenuItem>
            </Select>
          </FormControl>

          <Button variant="outlined" onClick={() => setImportDialogOpen(true)}>
            Import JSON
          </Button>

          <Button variant="contained" onClick={() => setCreateDialogOpen(true)}>
            Create Version
          </Button>
        </Stack>
      </Stack>

      {filteredVersions.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title={
                versions.length === 0
                  ? "No versions yet"
                  : "No versions match this filter"
              }
              description={
                versions.length === 0
                  ? "Create or import a dataset version to get started."
                  : "Try selecting a different status filter."
              }
            />
          </CardContent>
        </Card>
      ) : (
        <DatasetVersionTable
          versions={filteredVersions}
          onEdit={setEditingVersion}
          onDelete={setDeletingVersion}
          onFinalize={setFinalizingVersion}
          onViewCases={(version) =>
            navigate(`/datasets/${datasetId}/versions/${version.id}/cases`)
          }
          onView={(version) =>
            navigate(`/datasets/${datasetId}/versions/${version.id}`)
          }
        />
      )}

      <DatasetVersionCreateDialog
        open={createDialogOpen}
        datasetId={datasetId}
        onClose={() => setCreateDialogOpen(false)}
      />

      <DatasetVersionEditDialog
        open={Boolean(editingVersion)}
        version={editingVersion}
        onClose={() => setEditingVersion(null)}
      />

      <DatasetVersionDeleteDialog
        open={Boolean(deletingVersion)}
        version={deletingVersion}
        onClose={() => setDeletingVersion(null)}
      />

      <DatasetVersionFinalizeDialog
        open={Boolean(finalizingVersion)}
        version={finalizingVersion}
        onClose={() => setFinalizingVersion(null)}
      />

      <DatasetVersionImportDialog
        open={importDialogOpen}
        datasetId={datasetId}
        onClose={() => setImportDialogOpen(false)}
      />
    </Stack>
  );
}
