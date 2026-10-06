import React, { useState } from "react";
import {
  AddOutlined,
  DatasetOutlined,
  FileUploadOutlined,
  FilterListOutlined,
} from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { useDataset } from "../datasets/hooks";
import { DatasetVersionCreateDialog } from "./DatasetVersionCreateDialog";
import { DatasetVersionDeleteDialog } from "./DatasetVersionDeleteDialog";
import { DatasetVersionEditDialog } from "./DatasetVersionEditDialog";
import { DatasetVersionFinalizeDialog } from "./DatasetVersionFinalizeDialog";
import { DatasetVersionImportDialog } from "./DatasetVersionImportDialog";
import { DatasetVersionTable } from "./DatasetVersionTable";
import type { DatasetVersion, DatasetVersionStatus } from "./api";
import { useDatasetVersions } from "./hooks";

type VersionStatusFilter = "all" | DatasetVersionStatus;

export function DatasetVersionListPage() {
  const navigate = useNavigate();
  const theme = useTheme();
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
    <Stack spacing={3.5} sx={{ pb: 4 }}>
      {/* Breadcrumb Navigation */}
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

      {/* Header Banner */}
      <Paper
        elevation={0}
        sx={{
          p: { xs: 2.5, sm: 3.5 },
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
          background: (theme) =>
            theme.palette.mode === "dark"
              ? `linear-gradient(135deg, ${alpha(
                  theme.palette.primary.main,
                  0.08,
                )} 0%, ${alpha(theme.palette.background.paper, 0.4)} 100%)`
              : `linear-gradient(135deg, ${alpha(
                  theme.palette.primary.main,
                  0.03,
                )} 0%, #FFFFFF 100%)`,
        }}
      >
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2.5}
          sx={{
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", md: "center" },
          }}
        >
          <Stack direction="row" spacing={2.5} sx={{ alignItems: "center" }}>
            <Box
              sx={{
                width: 52,
                height: 52,
                borderRadius: 2.5,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                color: "primary.main",
                boxShadow: `0 0 0 1px ${alpha(theme.palette.primary.main, 0.2)}`,
                flexShrink: 0,
              }}
            >
              <DatasetOutlined sx={{ fontSize: 28 }} />
            </Box>

            <Stack spacing={0.5}>
              <Typography
                variant="h5"
                sx={{ fontWeight: 700, letterSpacing: "-0.01em" }}
              >
                Dataset Versions
              </Typography>

              <Typography variant="body2" color="text.secondary">
                Manage versions and test configurations for this dataset.
              </Typography>
            </Stack>
          </Stack>

          {/* Actions & Filters */}
          <Stack
            direction={{ xs: "column", sm: "row" }}
            spacing={1.5}
            sx={{
              width: { xs: "100%", md: "auto" },
              alignItems: { xs: "stretch", sm: "center" },
            }}
          >
            <FormControl size="small" sx={{ minWidth: 150 }}>
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
                startAdornment={
                  <FilterListOutlined
                    fontSize="small"
                    sx={{ mr: 1, color: "text.secondary" }}
                  />
                }
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="ready">Ready</MenuItem>
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="archived">Archived</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="outlined"
              color="inherit"
              startIcon={<FileUploadOutlined fontSize="small" />}
              onClick={() => setImportDialogOpen(true)}
              sx={{
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
                borderColor: "divider",
              }}
            >
              Import JSON
            </Button>

            <Button
              variant="contained"
              disableElevation
              startIcon={<AddOutlined fontSize="small" />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{
                borderRadius: 2,
                textTransform: "none",
                fontWeight: 600,
                px: 2.5,
              }}
            >
              Create Version
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Main Table Content / Empty State */}
      {filteredVersions.length === 0 ? (
        <Card
          variant="outlined"
          sx={{
            borderRadius: 3,
            p: 2,
            borderColor: "divider",
          }}
        >
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

      {/* Modal Dialogs */}
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
