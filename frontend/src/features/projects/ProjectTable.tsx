import {
  Box,
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
import type { Project } from "./api";

interface ProjectTableProps {
  projects: Project[];
  onEdit: (project: Project) => void;
  onDelete: (project: Project) => void;
}

export function ProjectTable({
  projects,
  onEdit,
  onDelete,
}: ProjectTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Project</TableCell>
            <TableCell>Slug</TableCell>
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
                <Tooltip title="Edit project">
                  <IconButton
                    aria-label={`Edit ${project.name}`}
                    onClick={() => onEdit(project)}
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

                <Tooltip title="Delete project">
                  <IconButton
                    aria-label={`Delete ${project.name}`}
                    onClick={() => onDelete(project)}
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
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
