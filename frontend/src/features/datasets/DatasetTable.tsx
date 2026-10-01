import {
  Box,
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
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Dataset</TableCell>
            <TableCell>Slug</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Workflow</TableCell>
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
                <Typography variant="body2" color="text.secondary">
                  {dataset.slug}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">{dataset.dataset_type}</Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    dataset.description ? "text.primary" : "text.secondary"
                  }
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
                  >
                    <Box
                      component="img"
                      src="/svg/versions.svg"
                      alt=""
                      sx={{
                        width: 24,
                        height: 24,
                      }}
                    />
                  </IconButton>
                </Tooltip>
              </TableCell>

              <TableCell align="right">
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    gap: 0.5,
                  }}
                >
                  <Tooltip title="Edit dataset">
                    <IconButton
                      aria-label={`Edit ${dataset.name}`}
                      onClick={() => onEdit(dataset)}
                      size="small"
                    >
                      <Box
                        component="img"
                        src="/svg/edit.svg"
                        alt=""
                        sx={{
                          width: 24,
                          height: 24,
                        }}
                      />
                    </IconButton>
                  </Tooltip>

                  <Tooltip title="Delete dataset">
                    <IconButton
                      aria-label={`Delete ${dataset.name}`}
                      onClick={() => onDelete(dataset)}
                      size="small"
                    >
                      <Box
                        component="img"
                        src="/svg/delete.svg"
                        alt=""
                        sx={{
                          width: 24,
                          height: 24,
                        }}
                      />
                    </IconButton>
                  </Tooltip>
                </Box>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
