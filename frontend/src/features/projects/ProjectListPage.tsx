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
import type { Project } from "./api";
import { ProjectCreateDialog } from "./ProjectCreateDialog";
import { ProjectDeleteDialog } from "./ProjectDeleteDialog";
import { ProjectEditDialog } from "./ProjectEditDialog";
import { ProjectTable } from "./ProjectTable";
import { useProjects } from "./hooks";

export function ProjectListPage() {
  const selectedOrganizationId = useAppContextStore(
    (state) => state.selectedOrganizationId,
  );

  const { data, isLoading, isError } = useProjects(
    selectedOrganizationId,
  );
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortField, setSortField] = useState<"name" | "slug">("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const projects = data ?? [];
  const sortedProjects = useMemo(() => [...projects].sort((a, b) => {
    const result = a[sortField].localeCompare(b[sortField]);
    return sortDirection === "asc" ? result : -result;
  }), [projects, sortField, sortDirection]);
  const changeSort = (field: "name" | "slug") => {
    if (sortField === field) setSortDirection((value) => value === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDirection("asc"); }
    setPage(0);
  };

  const [createOpen, setCreateOpen] = useState(false);
  const [editProject, setEditProject] = useState<Project | null>(null);
  const [deleteProject, setDeleteProject] = useState<Project | null>(
    null,
  );

  const handleEdit = (project: Project) => {
    setEditProject(project);
  };

  const handleDelete = (project: Project) => {
    setDeleteProject(project);
  };

  if (!selectedOrganizationId) {
    return (
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Projects
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage projects for the selected organization.
          </Typography>
        </Stack>

        <Card>
          <CardContent>
            <EmptyState
              title="No organization selected"
              description="Select an organization from the Dashboard to view its projects."
            />
          </CardContent>
        </Card>
      </Stack>
    );
  }

  if (isLoading) {
    return <LoadingState message="Loading projects..." />;
  }

  if (isError) {
    return <ErrorState message="Unable to load projects." />;
  }

  return (
    <Stack spacing={3}>
      <AppBreadcrumbs items={[{ label: "Projects" }]} />
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
            Projects
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage projects for the selected organization.
          </Typography>
        </Stack>

        <Button
          variant="contained"
          startIcon={<AddOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          Create Project
        </Button>
      </Stack>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title="No projects yet"
              description="Create your first project for this organization to get started."
            />
          </CardContent>
        </Card>
      ) : (
        <ProjectTable
          projects={sortedProjects.slice(page * pageSize, (page + 1) * pageSize)}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={changeSort}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
      {projects.length > 25 && <DataTablePagination page={page} pageSize={pageSize} total={projects.length} onPageChange={setPage} onPageSizeChange={(size) => { setPageSize(size); setPage(0); }} />}

      <ProjectCreateDialog
        open={createOpen}
        organizationId={selectedOrganizationId}
        onClose={() => setCreateOpen(false)}
      />

      <ProjectEditDialog
        open={Boolean(editProject)}
        project={editProject}
        onClose={() => setEditProject(null)}
      />

      <ProjectDeleteDialog
        open={Boolean(deleteProject)}
        project={deleteProject}
        onClose={() => setDeleteProject(null)}
      />
    </Stack>
  );
}
