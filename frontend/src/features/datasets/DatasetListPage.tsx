import { AddOutlined } from "@mui/icons-material";
import {
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAppContextStore } from "../../store/appContextStore";
import type { Dataset } from "./api";
import { DatasetCreateDialog } from "./DatasetCreateDialog";
import { DatasetDeleteDialog } from "./DatasetDeleteDialog";
import { DatasetEditDialog } from "./DatasetEditDialog";
import { DatasetTable } from "./DatasetTable";
import { useDatasets } from "./hooks";

export function DatasetListPage() {
  const navigate = useNavigate();

  const selectedProjectId = useAppContextStore(
    (state) => state.selectedProjectId,
  );

  const { data, isLoading, isError } = useDatasets(
    selectedProjectId,
  );

  const [createOpen, setCreateOpen] = useState(false);
  const [editDataset, setEditDataset] = useState<Dataset | null>(
    null,
  );
  const [deleteDataset, setDeleteDataset] =
    useState<Dataset | null>(null);

  const handleEdit = (dataset: Dataset) => {
    setEditDataset(dataset);
  };

  const handleDelete = (dataset: Dataset) => {
    setDeleteDataset(dataset);
  };

  const handleViewVersions = (dataset: Dataset) => {
    navigate(`/datasets/${dataset.id}/versions`);
  };

  if (!selectedProjectId) {
    return (
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Datasets
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage datasets for the selected project.
          </Typography>
        </Stack>

        <Card>
          <CardContent>
            <EmptyState
              title="No project selected"
              description="Select a project from the Dashboard to view its datasets."
            />
          </CardContent>
        </Card>
      </Stack>
    );
  }

  if (isLoading) {
    return <LoadingState message="Loading datasets..." />;
  }

  if (isError) {
    return <ErrorState message="Unable to load datasets." />;
  }

  return (
    <Stack spacing={3}>
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
            Datasets
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage datasets for the selected project.
          </Typography>
        </Stack>

        <Button
          variant="contained"
          startIcon={<AddOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          Create Dataset
        </Button>
      </Stack>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title="No datasets yet"
              description="Create your first dataset for this project to get started."
            />
          </CardContent>
        </Card>
      ) : (
        <DatasetTable
          datasets={data}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onViewVersions={handleViewVersions}
        />
      )}

      <DatasetCreateDialog
        open={createOpen}
        projectId={selectedProjectId}
        onClose={() => setCreateOpen(false)}
      />

      <DatasetEditDialog
        open={Boolean(editDataset)}
        dataset={editDataset}
        onClose={() => setEditDataset(null)}
      />

      <DatasetDeleteDialog
        open={Boolean(deleteDataset)}
        dataset={deleteDataset}
        onClose={() => setDeleteDataset(null)}
      />
    </Stack>
  );
}
