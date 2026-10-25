import {
  DeleteOutlined,
  EditOutlined,
  LayersOutlined,
} from "@mui/icons-material";
import {
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";
import { PermissionGate } from "../../components/common/PermissionGate";
import { DataTableSortLabel, type SortDirection } from "../../components/common/DataTableSortLabel";
import type { Dataset } from "./api";

interface DatasetTableProps {
  datasets: Dataset[];
  onEdit: (dataset: Dataset) => void;
  onDelete: (dataset: Dataset) => void;
  onViewVersions: (dataset: Dataset) => void;
  sortField?: "name" | "slug" | "dataset_type";
  sortDirection?: SortDirection;
  onSort?: (field: "name" | "slug" | "dataset_type") => void;
}

export function DatasetTable({
  datasets,
  onEdit,
  onDelete,
  onViewVersions,
  sortField = "name",
  sortDirection = "asc",
  onSort = () => undefined,
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
            <TableCell sx={{ minWidth: 160 }}><DataTableSortLabel field="name" activeField={sortField} direction={sortDirection} label="Dataset" onSort={onSort} /></TableCell>
            <TableCell sx={{ minWidth: 140 }}><DataTableSortLabel field="slug" activeField={sortField} direction={sortDirection} label="Slug" onSort={onSort} /></TableCell>
            <TableCell sx={{ width: 120 }}><DataTableSortLabel field="dataset_type" activeField={sortField} direction={sortDirection} label="Type" onSort={onSort} /></TableCell>
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
              <TableActionButton label={`View versions for ${dataset.name}`} icon={<LayersOutlined fontSize="small" />} onClick={() => onViewVersions(dataset)} />
              </TableCell>

              <TableCell align="right">
                <Stack
                  direction="row"
                  spacing={0.5}
                  sx={{ justifyContent: "flex-end", alignItems: "center" }}
                >
                  <PermissionGate permission="write">
                    <TableActionButton label={`Edit ${dataset.name}`} icon={<EditOutlined fontSize="small" />} onClick={() => onEdit(dataset)} />
                    <TableActionButton label={`Delete ${dataset.name}`} icon={<DeleteOutlined fontSize="small" />} destructive onClick={() => onDelete(dataset)} />
                  </PermissionGate>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
