import { AddOutlined } from "@mui/icons-material";
import {
  Button,
  Card,
  CardContent,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { DataTablePagination } from "../../components/common/DataTablePagination";
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
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortField, setSortField] = useState<"name" | "provider" | "model_identifier">("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const models = data ?? [];
  const sortedModels = useMemo(() => [...models].sort((a, b) => {
    const result = a[sortField].localeCompare(b[sortField]);
    return sortDirection === "asc" ? result : -result;
  }), [models, sortField, sortDirection]);
  const changeSort = (field: "name" | "provider" | "model_identifier") => {
    if (sortField === field) setSortDirection((value) => value === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDirection("asc"); }
    setPage(0);
  };

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
      <AppBreadcrumbs items={[{ label: "Models" }]} />
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
          models={sortedModels.slice(page * pageSize, (page + 1) * pageSize)}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={changeSort}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
      {models.length > 25 && <DataTablePagination page={page} pageSize={pageSize} total={models.length} onPageChange={setPage} onPageSizeChange={(size) => { setPageSize(size); setPage(0); }} />}

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
