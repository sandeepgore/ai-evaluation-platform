import {
  DeleteOutlined,
  EditOutlined,
  LayersOutlined,
} from "@mui/icons-material";
import {
  Chip,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { StatusChip } from "../../components/common/StatusChip";
import type { Dataset } from "./api";

interface DatasetTableProps {
  datasets: Dataset[];
  onEdit: (dataset: Dataset) => void;
  onDelete: (dataset: Dataset) => void;
  onViewVersions: (dataset: Dataset) => void;
}

export function DatasetTable({
  datasets,
  onEdit,
  onDelete,
  onViewVersions,
}: DatasetTableProps) {
  return (
    <TableContainer
      component={Paper}
      variant="outlined"
      sx={{ borderRadius: 0, border: 0 }}
    >
      <Table sx={{ minWidth: 650 }}>
        <TableHead>
          <TableRow sx={{ bgcolor: "action.hover" }}>
            <TableCell sx={{ minWidth: 160 }}>Dataset</TableCell>
            <TableCell sx={{ minWidth: 140 }}>Slug</TableCell>
            <TableCell sx={{ width: 120 }}>Type</TableCell>
            <TableCell sx={{ minWidth: 200 }}>Description</TableCell>
            <TableCell sx={{ width: 110 }}>Status</TableCell>
            <TableCell sx={{ width: 100 }}>Versions</TableCell>
            <TableCell align="right" sx={{ width: 110 }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {datasets.map((dataset) => (
            <TableRow
              key={dataset.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
                transition: "background-color 0.2s ease",
              }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {dataset.name}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: "0.8125rem",
                  }}
                >
                  {dataset.slug}
                </Typography>
              </TableCell>

              <TableCell>
                <Chip
                  label={dataset.dataset_type}
                  size="small"
                  variant="outlined"
                  sx={{
                    borderRadius: 1.5,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    textTransform: "capitalize",
                  }}
                />
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={dataset.description ? "text.primary" : "text.disabled"}
                  sx={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    fontStyle: dataset.description ? "normal" : "italic",
                  }}
                >
                  {dataset.description ?? "No description"}
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={dataset.is_active} />
              </TableCell>

              <TableCell>
                <Tooltip title="View dataset versions">
                  <IconButton
                    aria-label={`View versions for ${dataset.name}`}
                    onClick={() => onViewVersions(dataset)}
                    size="small"
                    color="primary"
                  >
                    <LayersOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>

              <TableCell align="right">
                <Stack
                  direction="row"
                  spacing={0.5}
                  sx={{ justifyContent: "flex-end", alignItems: "center" }}
                >
                  <Tooltip title="Edit dataset">
                    <IconButton
                      aria-label={`Edit ${dataset.name}`}
                      onClick={() => onEdit(dataset)}
                      size="small"
                      color="info"
                    >
                      <EditOutlined fontSize="small" />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title="Delete dataset">
                    <IconButton
                      aria-label={`Delete ${dataset.name}`}
                      onClick={() => onDelete(dataset)}
                      size="small"
                      color="error"
                    >
                      <DeleteOutlined fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
