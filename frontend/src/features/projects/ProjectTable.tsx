import { DeleteOutlined, EditOutlined } from "@mui/icons-material";
import {
  Paper,
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
import type { Project } from "./api";

interface ProjectTableProps {
  projects: Project[];
  onEdit: (project: Project) => void;
  onDelete: (project: Project) => void;
  sortField?: "name" | "slug";
  sortDirection?: SortDirection;
  onSort?: (field: "name" | "slug") => void;
}

export function ProjectTable({
  projects,
  onEdit,
  onDelete,
  sortField = "name",
  sortDirection = "asc",
  onSort = () => undefined,
}: ProjectTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table sx={{ minWidth: 900 }}>
        <TableHead>
          <TableRow>
            <TableCell><DataTableSortLabel field="name" activeField={sortField} direction={sortDirection} label="Project" onSort={onSort} /></TableCell>
            <TableCell><DataTableSortLabel field="slug" activeField={sortField} direction={sortDirection} label="Slug" onSort={onSort} /></TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {projects.map((project) => (
            <TableRow
              key={project.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
              }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {project.name}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {project.slug}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    project.description ? "text.primary" : "text.secondary"
                  }
                >
                  {project.description ?? "No description"}
                </Typography>
              </TableCell>

              <TableCell>
                <StatusChip active={project.is_active} />
              </TableCell>

              <TableCell align="right">
                <PermissionGate permission="write">
                  <TableActionButton label={`Edit ${project.name}`} icon={<EditOutlined fontSize="small" />} onClick={() => onEdit(project)} />
                  <TableActionButton label={`Delete ${project.name}`} icon={<DeleteOutlined fontSize="small" />} destructive onClick={() => onDelete(project)} />
                </PermissionGate>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
