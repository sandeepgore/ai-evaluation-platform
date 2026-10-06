import React from "react";
import {
  Box,
  Button,
  Chip,
  IconButton,
  LinearProgress,
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
  alpha,
  useTheme,
} from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutlined";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import StorageOutlinedIcon from "@mui/icons-material/StorageOutlined";
import TaskAltIcon from "@mui/icons-material/TaskAlt";

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
  const theme = useTheme();

  return (
    <TableContainer
      component={Paper}
      variant="outlined"
      sx={{
        borderRadius: 2.5,
        borderColor: "divider",
        overflow: "hidden",
        boxShadow: "none",
      }}
    >
      <Table sx={{ minWidth: 800 }}>
        <TableHead
          sx={{
            bgcolor: (theme) =>
              theme.palette.mode === "dark"
                ? alpha(theme.palette.common.white, 0.02)
                : alpha(theme.palette.common.black, 0.02),
          }}
        >
          <TableRow>
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              VERSION
            </TableCell>
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              STATUS
            </TableCell>
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              DESCRIPTION
            </TableCell>
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              CASES
            </TableCell>
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              DATA COVERAGE
            </TableCell>
            {/* WORKFLOW COLUMN */}
            <TableCell
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              WORKFLOW
            </TableCell>
            {/* ACTIONS COLUMN */}
            <TableCell
              align="right"
              sx={{
                fontWeight: 700,
                fontSize: "0.75rem",
                letterSpacing: 0.5,
                py: 1.5,
              }}
            >
              ACTIONS
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {versions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  No dataset versions available.
                </Typography>
              </TableCell>
            </TableRow>
          ) : (
            versions.map((version) => {
              const refCoverage =
                (version.analytics?.reference_coverage ?? 0) * 100;
              const ctxCoverage =
                (version.analytics?.context_coverage ?? 0) * 100;
              const isDraft = version.status === "draft";

              return (
                <TableRow
                  key={version.id}
                  hover
                  sx={{
                    transition: "background-color 0.2s ease",
                    "&:last-child td, &:last-child th": {
                      border: 0,
                    },
                  }}
                >
                  {/* Version Tag */}
                  <TableCell>
                    <Chip
                      label={`v${version.version}`}
                      size="small"
                      sx={{
                        fontFamily: "monospace",
                        fontWeight: 700,
                        fontSize: "0.8125rem",
                        bgcolor: alpha(theme.palette.primary.main, 0.08),
                        color: "primary.main",
                        border: "1px solid",
                        borderColor: alpha(theme.palette.primary.main, 0.2),
                      }}
                    />
                  </TableCell>

                  {/* Status Badge */}
                  <TableCell>
                    <DatasetVersionStatusChip status={version.status} />
                  </TableCell>

                  {/* Description */}
                  <TableCell sx={{ maxWidth: 260 }}>
                    <Typography
                      variant="body2"
                      color={
                        version.description ? "text.primary" : "text.secondary"
                      }
                      sx={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontStyle: version.description ? "normal" : "italic",
                      }}
                    >
                      {version.description || "No description"}
                    </Typography>
                  </TableCell>

                  {/* Case Count */}
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {version.case_count.toLocaleString()}
                    </Typography>
                  </TableCell>

                  {/* Data Coverage Bars */}
                  <TableCell sx={{ minWidth: 150 }}>
                    {version.analytics ? (
                      <Stack spacing={0.75} sx={{ py: 0.5 }}>
                        <Box sx={{ width: "100%" }}>
                          <Stack
                            direction="row"
                            spacing={1}
                            sx={{
                              justifyContent: "space-between",
                              alignItems: "center",
                              mb: 0.25,
                            }}
                          >
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ fontSize: "0.7rem", fontWeight: 600 }}
                            >
                              Ref
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{ fontSize: "0.7rem", fontWeight: 700 }}
                            >
                              {refCoverage.toFixed(1)}%
                            </Typography>
                          </Stack>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(refCoverage, 100)}
                            color="success"
                            sx={{
                              height: 4,
                              borderRadius: 2,
                              bgcolor: alpha(theme.palette.success.main, 0.12),
                            }}
                          />
                        </Box>

                        <Box sx={{ width: "100%" }}>
                          <Stack
                            direction="row"
                            spacing={1}
                            sx={{
                              justifyContent: "space-between",
                              alignItems: "center",
                              mb: 0.25,
                            }}
                          >
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ fontSize: "0.7rem", fontWeight: 600 }}
                            >
                              Ctx
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{ fontSize: "0.7rem", fontWeight: 700 }}
                            >
                              {ctxCoverage.toFixed(1)}%
                            </Typography>
                          </Stack>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min(ctxCoverage, 100)}
                            color="info"
                            sx={{
                              height: 4,
                              borderRadius: 2,
                              bgcolor: alpha(theme.palette.info.main, 0.12),
                            }}
                          />
                        </Box>
                      </Stack>
                    ) : (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontStyle: "italic" }}
                      >
                        Pending finalization
                      </Typography>
                    )}
                  </TableCell>

                  {/* WORKFLOW COLUMN: State Transition Actions */}
                  <TableCell>
                    {isDraft ? (
                      <Tooltip
                        title={
                          version.case_count === 0
                            ? "Add at least one case before finalizing"
                            : "Finalize version — locks version and prepares it for benchmarks"
                        }
                      >
                        <span>
                          <Button
                            variant="outlined"
                            color="success"
                            size="small"
                            startIcon={<CheckCircleOutlinedIcon />}
                            onClick={() => onFinalize(version)}
                            disabled={version.case_count === 0}
                            sx={{
                              borderRadius: 1.5,
                              textTransform: "none",
                              fontWeight: 600,
                              fontSize: "0.75rem",
                              py: 0.4,
                              px: 1.2,
                            }}
                          >
                            Finalize
                          </Button>
                        </span>
                      </Tooltip>
                    ) : (
                      <Stack
                        direction="row"
                        spacing={0.5}
                        sx={{ alignItems: "center" }}
                      >
                        <TaskAltIcon
                          sx={{ fontSize: 16, color: "success.main" }}
                        />
                        <Typography
                          variant="caption"
                          color="text.secondary"
                          sx={{ fontWeight: 600 }}
                        >
                          Ready
                        </Typography>
                      </Stack>
                    )}
                  </TableCell>

                  {/* ACTIONS COLUMN: Resource Management Options */}
                  <TableCell align="right">
                    <Stack
                      direction="row"
                      spacing={0.5}
                      sx={{ justifyContent: "flex-end" }}
                    >
                      {/* View Cases */}
                      <Tooltip title="Explore version cases">
                        <IconButton
                          aria-label={`View cases for version ${version.version}`}
                          onClick={() => onViewCases(version)}
                          size="small"
                          sx={{
                            color: "text.secondary",
                            "&:hover": { color: "primary.main" },
                          }}
                        >
                          <StorageOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      {/* View Version Details */}
                      <Tooltip title="View version details">
                        <IconButton
                          aria-label={`View version ${version.version}`}
                          onClick={() => onView(version)}
                          size="small"
                          sx={{
                            color: "text.secondary",
                            "&:hover": { color: "text.primary" },
                          }}
                        >
                          <VisibilityOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      {/* Edit Description */}
                      <Tooltip title="Edit description">
                        <IconButton
                          aria-label={`Edit version ${version.version}`}
                          onClick={() => onEdit(version)}
                          size="small"
                          sx={{
                            color: "text.secondary",
                            "&:hover": { color: "text.primary" },
                          }}
                        >
                          <EditOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      {/* Delete Action */}
                      <Tooltip
                        title={
                          version.case_count > 0
                            ? "Cannot delete a version that contains cases"
                            : "Delete version"
                        }
                      >
                        <span>
                          <IconButton
                            aria-label={`Delete version ${version.version}`}
                            onClick={() => onDelete(version)}
                            size="small"
                            disabled={version.case_count > 0}
                            sx={{
                              color: "error.main",
                              "&:hover": {
                                bgcolor: alpha(theme.palette.error.main, 0.08),
                              },
                            }}
                          >
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
