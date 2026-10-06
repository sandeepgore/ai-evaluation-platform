import { AddOutlined, SearchOutlined } from "@mui/icons-material";
import {
  Box,
  Button,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
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

  const { data, isLoading, isError } = useDatasets(selectedProjectId);

  const [createOpen, setCreateOpen] = useState(false);
  const [editDataset, setEditDataset] = useState<Dataset | null>(null);
  const [deleteDataset, setDeleteDataset] = useState<Dataset | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const datasets = useMemo(() => data ?? [], [data]);

  const filteredDatasets = useMemo(() => {
    if (!searchQuery.trim()) return datasets;
    const query = searchQuery.toLowerCase().trim();
    return datasets.filter(
      (d) =>
        d.name.toLowerCase().includes(query) ||
        d.slug.toLowerCase().includes(query) ||
        (d.description && d.description.toLowerCase().includes(query)) ||
        d.dataset_type.toLowerCase().includes(query),
    );
  }, [datasets, searchQuery]);

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

        <Paper variant="outlined" sx={{ borderRadius: 3, p: 4 }}>
          <EmptyState
            title="No project selected"
            description="Select a project from the top navigation or dashboard to view its datasets."
          />
        </Paper>
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
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            Datasets
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Manage datasets and evaluation data for the selected project.
          </Typography>
        </Stack>

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
          Create Dataset
        </Button>
      </Stack>

      {/* Main Content Area */}
      {datasets.length === 0 ? (
        <Paper
          variant="outlined"
          sx={{ borderRadius: 3, p: 4, textAlign: "center" }}
        >
          <EmptyState
            title="No datasets yet"
            description="Create your first dataset for this project to start managing evaluation test cases."
          />
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
            Create First Dataset
          </Button>
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
          {/* Table Header Toolbar */}
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
              placeholder="Search datasets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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
              Showing {filteredDatasets.length} of {datasets.length}{" "}
              {datasets.length === 1 ? "dataset" : "datasets"}
            </Typography>
          </Box>

          {/* Table */}
          <DatasetTable
            datasets={filteredDatasets}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onViewVersions={handleViewVersions}
          />
        </Paper>
      )}

      {/* Dialog Modals */}
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
