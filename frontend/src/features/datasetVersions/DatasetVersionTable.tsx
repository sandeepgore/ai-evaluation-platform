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
import { DatasetVersionStatusChip } from "./DatasetVersionStatusChip";
import type { DatasetVersion } from "./api";

interface DatasetVersionTableProps {
  versions: DatasetVersion[];
  onEdit: (version: DatasetVersion) => void;
  onDelete: (version: DatasetVersion) => void;
  onFinalize: (version: DatasetVersion) => void;
  onViewCases: (version: DatasetVersion) => void;
  onView: (version: DatasetVersion) => void;
}

export function DatasetVersionTable({
  versions,
  onEdit,
  onDelete,
  onFinalize,
  onViewCases,
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
            <TableCell>Data Coverage</TableCell>
            <TableCell>Workflow</TableCell>
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

              <TableCell>
                <Stack direction="row" spacing={0.5}>
                  <Tooltip title="View evaluation cases in this dataset version">
                    <IconButton
                      aria-label={`View cases for version ${version.version}`}
                      onClick={() => onViewCases(version)}
                      size="small"
                    >
                      <Box
                        component="img"
                        src="/svg/cases.svg"
                        alt=""
                        sx={{
                          width: 24,
                          height: 24,
                        }}
                      />
                    </IconButton>
                  </Tooltip>

                  {version.status === "draft" && (
                    <Tooltip
                      title={
                        version.case_count === 0
                          ? "Add at least one case before finalizing — finalized versions are used for evaluation"
                          : "Finalize version — makes it ready for evaluation"
                      }
                    >
                      <span>
                        <IconButton
                          aria-label={`Finalize version ${version.version}`}
                          onClick={() => onFinalize(version)}
                          size="small"
                          disabled={version.case_count === 0}
                        >
                          <Box
                            component="img"
                            src="/svg/finalize.svg"
                            alt=""
                            sx={{
                              width: 24,
                              height: 24,
                              opacity: version.case_count === 0 ? 0.4 : 1,
                            }}
                          />
                        </IconButton>
                      </span>
                    </Tooltip>
                  )}
                </Stack>
              </TableCell>

              <TableCell align="right">
                <Tooltip title="View dataset version details">
                  <IconButton
                    aria-label={`View version ${version.version}`}
                    onClick={() => onView(version)}
                    size="small"
                  >
                    <Box
                      component="img"
                      src="/svg/view.svg"
                      alt=""
                      sx={{
                        width: 24,
                        height: 24,
                      }}
                    />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Edit dataset version description">
                  <IconButton
                    aria-label={`Edit version ${version.version}`}
                    onClick={() => onEdit(version)}
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

                <Tooltip
                  title={
                    version.case_count > 0
                      ? "Cannot delete a version that contains cases"
                      : "Delete dataset version"
                  }
                >
                  <span>
                    <IconButton
                      aria-label={`Delete version ${version.version}`}
                      onClick={() => onDelete(version)}
                      size="small"
                      disabled={version.case_count > 0}
                    >
                      <Box
                        component="img"
                        src="/svg/delete.svg"
                        alt=""
                        sx={{
                          width: 24,
                          height: 24,
                          opacity: version.case_count > 0 ? 0.4 : 1,
                        }}
                      />
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
