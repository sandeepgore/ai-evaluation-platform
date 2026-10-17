import { AddOutlined } from "@mui/icons-material";
import { Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { DataTablePagination } from "../../components/common/DataTablePagination";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import type { Organization } from "./api";
import { OrganizationTable } from "./OrganizationTable";
import { useOrganizations } from "./hooks";
import { OrganizationCreateDialog } from "./OrganizationCreateDialog";
import { OrganizationEditDialog } from "./OrganizationEditDialog";
import { OrganizationDeleteDialog } from "./OrganizationDeleteDialog";

export function OrganizationListPage() {
  const { data, isLoading, isError } = useOrganizations();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [sortField, setSortField] = useState<"name" | "slug">("name");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const organizations = data ?? [];
  const sortedOrganizations = useMemo(() => [...organizations].sort((a, b) => {
    const result = a[sortField].localeCompare(b[sortField]);
    return sortDirection === "asc" ? result : -result;
  }), [organizations, sortField, sortDirection]);
  const changeSort = (field: "name" | "slug") => {
    if (sortField === field) setSortDirection((value) => value === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDirection("asc"); }
    setPage(0);
  };
  const [createOpen, setCreateOpen] = useState(false);
  const [editOrganization, setEditOrganization] = useState<Organization | null>(
    null,
  );
  const [deleteOrganization, setDeleteOrganization] =
    useState<Organization | null>(null);

  const handleEdit = (organization: Organization) => {
    setEditOrganization(organization);
  };

  const handleDelete = (organization: Organization) => {
    setDeleteOrganization(organization);
  };

  if (isLoading) {
    return <LoadingState message="Loading organizations..." />;
  }

  if (isError) {
    return <ErrorState message="Unable to load organizations." />;
  }

  return (
    <Stack spacing={3}>
      <AppBreadcrumbs items={[{ label: "Organizations" }]} />
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
            Organizations
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage organizations and their platform access.
          </Typography>
        </Stack>

        <Button
          variant="contained"
          startIcon={<AddOutlined />}
          onClick={() => setCreateOpen(true)}
        >
          Create Organization
        </Button>
      </Stack>

      {!data || data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              title="No organizations yet"
              description="Create your first organization to get started."
            />
          </CardContent>
        </Card>
      ) : (
        <OrganizationTable
          organizations={sortedOrganizations.slice(page * pageSize, (page + 1) * pageSize)}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={changeSort}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
      {organizations.length > 25 && <DataTablePagination page={page} pageSize={pageSize} total={organizations.length} onPageChange={setPage} onPageSizeChange={(size) => { setPageSize(size); setPage(0); }} />}
      <OrganizationCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <OrganizationEditDialog
        open={Boolean(editOrganization)}
        organization={editOrganization}
        onClose={() => setEditOrganization(null)}
      />
      <OrganizationDeleteDialog
        open={Boolean(deleteOrganization)}
        organization={deleteOrganization}
        onClose={() => setDeleteOrganization(null)}
      />
    </Stack>
  );
}
