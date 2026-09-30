import {
  DeleteOutlined,
  EditOutlined,
  FolderOpenOutlined,
} from "@mui/icons-material";
import {
  IconButton,
  Paper,
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
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Dataset</TableCell>
            <TableCell>Slug</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Actions</TableCell>
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
                >
                  {dataset.slug}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">
                  {dataset.dataset_type}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    dataset.description
                      ? "text.primary"
                      : "text.secondary"
                  }
                >
                  {dataset.description ?? "No description"}
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={dataset.is_active} />
              </TableCell>

              <TableCell align="right">
                <Tooltip title="View versions">
                  <IconButton
                    aria-label={`View versions for ${dataset.name}`}
                    onClick={() => onViewVersions(dataset)}
                    size="small"
                  >
                    <FolderOpenOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Edit dataset">
                  <IconButton
                    aria-label={`Edit ${dataset.name}`}
                    onClick={() => onEdit(dataset)}
                    size="small"
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
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
