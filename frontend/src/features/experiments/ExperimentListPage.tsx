import { ScreenWithActivity } from "../auditLogs/ScreenWithActivity";
import {
  AddOutlined,
  DeleteOutlined,
  SearchOutlined,
  VisibilityOutlined,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  InputAdornment,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";
import { PermissionGate } from "../../components/common/PermissionGate";
import { DataTablePagination } from "../../components/common/DataTablePagination";
import {
  DataTableSortLabel,
  type SortDirection,
} from "../../components/common/DataTableSortLabel";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useAppContextStore } from "../../store/appContextStore";
import type { Experiment } from "./api";
import {
  useCreateExperiment,
  useDeleteExperiment,
  useExperiments,
} from "./hooks";

const PAGE_SIZE = 25;
type SortField = "name" | "created_at";

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
}


export function ExperimentListPage() {
  const navigate = useNavigate();
  const selectedProjectId = useAppContextStore((state) => state.selectedProjectId);
  const { data: experiments, isLoading, isError } = useExperiments("all", selectedProjectId);
  const createMutation = useCreateExperiment();
  const deleteMutation = useDeleteExperiment();

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(PAGE_SIZE);
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState("");
  const [experimentToDelete, setExperimentToDelete] =
    useState<Experiment | null>(null);

  const visibleExperiments = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = (experiments ?? []).filter(
      (experiment) =>
        !query ||
        `${experiment.name} ${experiment.description ?? ""}`
          .toLowerCase()
          .includes(query),
    );

    return filtered.sort((left, right) => {
      const comparison =
        sortField === "name"
          ? left.name.localeCompare(right.name)
          : new Date(left.created_at).getTime() -
            new Date(right.created_at).getTime();
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [experiments, search, sortField, sortDirection]);

  const pageCount = Math.max(
    1,
    Math.ceil(visibleExperiments.length / pageSize),
  );
  const currentPage = Math.min(page, pageCount - 1);
  const pageExperiments = visibleExperiments.slice(
    currentPage * pageSize,
    currentPage * pageSize + pageSize,
  );
  const activeCount = (experiments ?? []).filter((experiment) => experiment.is_active).length;
  const latestExperiment = [...(experiments ?? [])].sort(
    (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  )[0];

  useEffect(() => {
    if (page !== currentPage) setPage(currentPage);
  }, [page, currentPage]);

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError("");
    if (!name.trim()) {
      setFormError("Enter an experiment name.");
      return;
    }
    if (!selectedProjectId) {
      setFormError("Select a project before creating an experiment.");
      return;
    }
    try {
      const experiment = await createMutation.mutateAsync({
        project_id: selectedProjectId,
        name: name.trim(),
        description: description.trim() || null,
      });
      setIsCreateOpen(false);
      setName("");
      setDescription("");
      navigate(`/experiments/${experiment.id}`);
    } catch {
      // The mutation hook reports API errors.
    }
  };

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection((direction) => (direction === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  if (!selectedProjectId) {
    return (
      <Stack spacing={3}>
        <AppBreadcrumbs items={[{ label: "Experiments" }]} />
        <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
            Select a project
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Choose an organization and project from the Dashboard to view related experiments.
          </Typography>
        </Paper>
      </Stack>
    );
  }

  if (isLoading) return <LoadingState />;
  if (isError)
    return (
      <ErrorState
        title="Experiments could not be loaded"
        message="Retry to reload the experiment list."
      />
    );

  return (
    <ScreenWithActivity screen="experiments">
    <Stack spacing={3}>
      <AppBreadcrumbs items={[{ label: "Experiments" }]} />

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        sx={{ alignItems: { sm: "center" }, justifyContent: "space-between" }}
      >
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Experiments
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Group evaluation runs and compare saved result snapshots.
          </Typography>
        </Box>
        <PermissionGate permission="write"><Button
          variant="contained"
          disableElevation
          startIcon={<AddOutlined />}
          onClick={() => setIsCreateOpen(true)}
          sx={{
            borderRadius: 2,
            textTransform: "none",
            alignSelf: { xs: "flex-start", sm: "center" },
          }}
        >
          New experiment
        </Button></PermissionGate>
      </Stack>

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
        {[
          { label: "Total experiments", value: experiments?.length ?? 0, helper: "In this project" },
          { label: "Active", value: activeCount, helper: "Available for new comparisons" },
          { label: "Most recently created", value: latestExperiment?.name ?? "No experiments yet", helper: latestExperiment ? formatDate(latestExperiment.created_at) : "Create an experiment to get started" },
        ].map((metric) => (
          <Paper key={metric.label} variant="outlined" sx={{ p: 2, borderRadius: 2.5, minWidth: 0, height: "100%" }}>
            <Typography variant="caption" color="text.secondary">{metric.label}</Typography>
            <Typography variant="h6" fontWeight={700} noWrap title={String(metric.value)} sx={{ mt: 0.25 }}>{metric.value}</Typography>
            <Typography variant="caption" color="text.secondary" noWrap display="block">{metric.helper}</Typography>
          </Paper>
        ))}
      </Box>

      {experiments?.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 3, borderRadius: 3 }}>
          <EmptyState
            title="No experiments yet"
            description="Create an experiment to compare completed evaluation runs over time."
          />
          <Stack direction="row" sx={{ justifyContent: "center" }}>
            <PermissionGate permission="write"><Button
              startIcon={<AddOutlined />}
              onClick={() => setIsCreateOpen(true)}
            >
              Create experiment
            </Button></PermissionGate>
          </Stack>
        </Paper>
      ) : (
        <Paper variant="outlined" sx={{ borderRadius: 3, overflow: "hidden" }}>
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={1.5}
            sx={{
              p: 2,
              justifyContent: "space-between",
              alignItems: { sm: "center" },
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            <TextField
              size="small"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(0);
              }}
              placeholder="Search experiments"
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchOutlined fontSize="small" />
                    </InputAdornment>
                  ),
                },
              }}
              sx={{ width: { xs: "100%", sm: 320 } }}
            />
            <Typography variant="caption" color="text.secondary">
              Showing {pageExperiments.length} of {visibleExperiments.length}{" "}
              experiments
            </Typography>
          </Stack>

          {visibleExperiments.length === 0 ? (
            <EmptyState
              title="No matching experiments"
              description="Try another search term."
            />
          ) : (
            <>
              <TableContainer sx={{ overflowX: "auto" }}>
                <Table aria-label="Experiments" sx={{ minWidth: 900 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>
                        <DataTableSortLabel
                          field="name"
                          activeField={sortField}
                          direction={sortDirection}
                          label="Experiment"
                          onSort={handleSort}
                        />
                      </TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>
                        <DataTableSortLabel
                          field="created_at"
                          activeField={sortField}
                          direction={sortDirection}
                          label="Created"
                          onSort={handleSort}
                        />
                      </TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pageExperiments.map((experiment) => (
                      <TableRow
                        key={experiment.id}
                        hover
                        sx={{ cursor: "pointer" }}
                        onClick={() =>
                          navigate(`/experiments/${experiment.id}`)
                        }
                      >
                        <TableCell sx={{ minWidth: 200 }}>
                          <Stack
                            direction="row"
                            spacing={1.25}
                            sx={{ alignItems: "center" }}
                          >
                            <Typography
                              variant="body2"
                              sx={{ fontWeight: 600 }}
                            >
                              {experiment.name}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell sx={{ minWidth: 240, maxWidth: 480 }}>
                          <Typography
                            variant="body2"
                            color={
                              experiment.description
                                ? "text.primary"
                                : "text.secondary"
                            }
                            sx={{
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                            title={experiment.description ?? "No description"}
                          >
                            {experiment.description || "No description"}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <StatusChip active={experiment.is_active} />
                        </TableCell>
                        <TableCell sx={{ whiteSpace: "nowrap" }}>
                          {formatDate(experiment.created_at)}
                        </TableCell>
                        <TableCell
                          align="right"
                          onClick={(event) => event.stopPropagation()}
                        >
                          <TableActionButton
                            label={`Open ${experiment.name}`}
                            icon={<VisibilityOutlined fontSize="small" />}
                            onClick={() => navigate(`/experiments/${experiment.id}`)}
                          />
                          <PermissionGate permission="write">
                            <TableActionButton
                              label={`Delete ${experiment.name}`}
                              icon={<DeleteOutlined fontSize="small" />}
                              destructive
                              onClick={() => setExperimentToDelete(experiment)}
                            />
                          </PermissionGate>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <DataTablePagination
                page={currentPage}
                pageSize={pageSize}
                total={visibleExperiments.length}
                onPageChange={setPage}
                onPageSizeChange={(value) => {
                  setPageSize(value);
                  setPage(0);
                }}
              />
            </>
          )}
        </Paper>
      )}

      <Dialog
        open={isCreateOpen}
        onClose={() => !createMutation.isPending && setIsCreateOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <Box component="form" onSubmit={handleCreate}>
          <DialogTitle>Create experiment</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ pt: 1 }}>
              {formError && <Alert severity="error">{formError}</Alert>}
              <TextField
                label="Name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
                autoFocus
                fullWidth
                slotProps={{ htmlInput: { maxLength: 150 } }}
                helperText="Use a name that describes the model or prompt comparison."
              />
              <TextField
                label="Description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                multiline
                minRows={3}
                fullWidth
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 2.5, pt: 0 }}>
            <Button
              onClick={() => setIsCreateOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending || !name.trim()}
            >
              {createMutation.isPending ? "Creating…" : "Create experiment"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <ConfirmDialog
        open={Boolean(experimentToDelete)}
        title="Delete experiment?"
        message={`“${experimentToDelete?.name ?? "This experiment"}” will be removed from the active experiment list.`}
        confirmLabel="Delete"
        loading={deleteMutation.isPending}
        onCancel={() => setExperimentToDelete(null)}
        onConfirm={() => {
          if (!experimentToDelete) return;
          deleteMutation.mutate(experimentToDelete.id, {
            onSuccess: () => setExperimentToDelete(null),
          });
        }}
      />
    </Stack>
      </ScreenWithActivity>
  );
}
