import {
  CheckCircleOutlineOutlined,
  DeleteOutlined,
  EditOutlined,
  VisibilityOutlined,
} from "@mui/icons-material";
import {
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
import { DatasetVersionStatusChip } from "./DatasetVersionStatusChip";
import type { DatasetVersion } from "./api";

interface DatasetVersionTableProps {
  versions: DatasetVersion[];
  onEdit: (version: DatasetVersion) => void;
  onDelete: (version: DatasetVersion) => void;
  onFinalize: (version: DatasetVersion) => void;
  onView: (version: DatasetVersion) => void;
}

export function DatasetVersionTable({
  versions,
  onEdit,
  onDelete,
  onFinalize,
  onView,
}: DatasetVersionTableProps) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Version</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Cases</TableCell>
            <TableCell>Analytics</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {versions.map((version) => (
            <TableRow
              key={version.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
              }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  v{version.version}
                </Typography>
              </TableCell>

              <TableCell>
                <DatasetVersionStatusChip status={version.status} />
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    version.description ? "text.primary" : "text.secondary"
                  }
                >
                  {version.description ?? "No description"}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography variant="body2">{version.case_count}</Typography>
              </TableCell>

              <TableCell>
                {version.analytics ? (
                  <Stack spacing={0.25}>
                    <Typography variant="body2">
                      Ref:{" "}
                      {(version.analytics.reference_coverage * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Context:{" "}
                      {(version.analytics.context_coverage * 100).toFixed(1)}%
                    </Typography>
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    —
                  </Typography>
                )}
              </TableCell>

              <TableCell align="right">
                <Tooltip title="View version">
                  <IconButton
                    aria-label={`View version ${version.version}`}
                    onClick={() => onView(version)}
                    size="small"
                  >
                    <VisibilityOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Edit version">
                  <IconButton
                    aria-label={`Edit version ${version.version}`}
                    onClick={() => onEdit(version)}
                    size="small"
                  >
                    <EditOutlined fontSize="small" />
                  </IconButton>
                </Tooltip>

                {version.status === "draft" && (
                  <Tooltip title="Finalize version">
                    <IconButton
                      aria-label={`Finalize version ${version.version}`}
                      onClick={() => onFinalize(version)}
                      size="small"
                    >
                      <CheckCircleOutlineOutlined fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}

                <Tooltip
                  title={
                    version.case_count > 0
                      ? "Cannot delete a version that has cases"
                      : "Delete version"
                  }
                >
                  <span>
                    <IconButton
                      aria-label={`Delete version ${version.version}`}
                      onClick={() => onDelete(version)}
                      size="small"
                      color="error"
                      disabled={version.case_count > 0}
                    >
                      <DeleteOutlined fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
