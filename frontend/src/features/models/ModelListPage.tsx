import { AddOutlined } from "@mui/icons-material";
import {
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAppContextStore } from "../../store/appContextStore";
import type { Model } from "./api";
import { ModelCreateDialog } from "./ModelCreateDialog";
import { ModelDeleteDialog } from "./ModelDeleteDialog";
import { ModelEditDialog } from "./ModelEditDialog";
import { ModelTable } from "./ModelTable";
import { useModels } from "./hooks";

export function ModelListPage() {
  const selectedProjectId = useAppContextStore(
    (state) => state.selectedProjectId,
  );

  const { data, isLoading, isError } = useModels(
    selectedProjectId,
  );

  const [createOpen, setCreateOpen] = useState(false);
  const [editModel, setEditModel] = useState<Model | null>(null);
  const [deleteModel, setDeleteModel] = useState<Model | null>(
    null,
  );

  const handleEdit = (model: Model) => {
    setEditModel(model);
  };

  const handleDelete = (model: Model) => {
    setDeleteModel(model);
  };

  if (!selectedProjectId) {
    return (
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Models
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage models for the selected project.
          </Typography>
        </Stack>

        <Card>
          <CardContent>
            <EmptyState
              title="No project selected"
              description="Select a project from the Dashboard to view its models."
            />
          </CardContent>
        </Card>
      </Stack>
    );
  }

  if (isLoading) {
    return <LoadingState message="Loading models..." />;
  }

  if (isError) {
    return <ErrorState message="Unable to load models." />;
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
            Models
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage models for the selected project.
          </Typography>
        </Stack>

        <Button
          variant="contained"
          startIcon={<AddOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          Create Model
        </Button>
      </Stack>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title="No models yet"
              description="Create your first model for this project to get started."
            />
          </CardContent>
        </Card>
      ) : (
        <ModelTable
          models={data}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      <ModelCreateDialog
        open={createOpen}
        projectId={selectedProjectId}
        onClose={() => setCreateOpen(false)}
      />

      <ModelEditDialog
        open={Boolean(editModel)}
        model={editModel}
        onClose={() => setEditModel(null)}
      />

      <ModelDeleteDialog
        open={Boolean(deleteModel)}
        model={deleteModel}
        onClose={() => setDeleteModel(null)}
      />
    </Stack>
  );
}
