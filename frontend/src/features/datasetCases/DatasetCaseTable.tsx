import {
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  Remove,
  VisibilityOutlined,
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
import {
  DataTableSortLabel,
  type SortDirection,
} from "../../components/common/DataTableSortLabel";
import type { DatasetCase } from "./api";

type SortField =
  | "position"
  | "input"
  | "expected_output"
  | "has_reference"
  | "has_context";

interface DatasetCaseTableProps {
  cases: DatasetCase[];
  editable: boolean;
  ready: boolean;
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
  onView: (datasetCase: DatasetCase) => void;
  onEdit: (datasetCase: DatasetCase) => void;
  onDelete: (datasetCase: DatasetCase) => void;
}

export function DatasetCaseTable({
  cases,
  editable,
  ready,
  sortField,
  sortDirection,
  onSort,
  onView,
  onEdit,
  onDelete,
}: DatasetCaseTableProps) {
  return (
    <TableContainer
      component={Paper}
      variant="outlined"
      sx={{ borderRadius: 0, border: 0 }}
    >
      <Table sx={{ minWidth: 650 }}>
        <TableHead>
          <TableRow sx={{ bgcolor: "action.hover" }}>
            <TableCell sx={{ width: 70 }}>
              <DataTableSortLabel
                field="position"
                activeField={sortField}
                direction={sortDirection}
                label="#"
                onSort={onSort}
              />
            </TableCell>

            <TableCell sx={{ minWidth: 220 }}>
              <DataTableSortLabel
                field="input"
                activeField={sortField}
                direction={sortDirection}
                label="Input"
                onSort={onSort}
              />
            </TableCell>

            <TableCell sx={{ minWidth: 220 }}>
              <DataTableSortLabel
                field="expected_output"
                activeField={sortField}
                direction={sortDirection}
                label="Expected Output"
                onSort={onSort}
              />
            </TableCell>

            {ready && (
              <>
                <TableCell sx={{ width: 130 }}>
                  <DataTableSortLabel
                    field="has_reference"
                    activeField={sortField}
                    direction={sortDirection}
                    label="Reference"
                    onSort={onSort}
                  />
                </TableCell>

                <TableCell sx={{ width: 130 }}>
                  <DataTableSortLabel
                    field="has_context"
                    activeField={sortField}
                    direction={sortDirection}
                    label="Context"
                    onSort={onSort}
                  />
                </TableCell>
              </>
            )}

            <TableCell align="right" sx={{ width: 120 }}>
              Actions
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {cases.map((datasetCase) => (
            <TableRow
              key={datasetCase.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": { border: 0 },
                transition: "background-color 0.2s ease",
              }}
            >
              <TableCell>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontWeight: 600 }}
                >
                  {datasetCase.position + 1}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  sx={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    fontWeight: 500,
                  }}
                >
                  {datasetCase.input}
                </Typography>
              </TableCell>

              <TableCell>
                <Typography
                  variant="body2"
                  color={
                    datasetCase.expected_output
                      ? "text.primary"
                      : "text.disabled"
                  }
                  sx={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    fontStyle: datasetCase.expected_output
                      ? "normal"
                      : "italic",
                  }}
                >
                  {datasetCase.expected_output ?? "Not provided"}
                </Typography>
              </TableCell>

              {ready && (
                <>
                  <TableCell>
                    {datasetCase.has_reference ? (
                      <Chip
                        icon={<CheckCircleOutlined fontSize="small" />}
                        label="Ready"
                        size="small"
                        color="success"
                        variant="outlined"
                        sx={{ borderRadius: 1.5, fontWeight: 600 }}
                      />
                    ) : (
                      <Chip
                        icon={<Remove fontSize="small" />}
                        label="None"
                        size="small"
                        variant="outlined"
                        sx={{
                          borderRadius: 1.5,
                          color: "text.disabled",
                          borderColor: "divider",
                        }}
                      />
                    )}
                  </TableCell>

                  <TableCell>
                    {datasetCase.has_context ? (
                      <Chip
                        icon={<CheckCircleOutlined fontSize="small" />}
                        label="Ready"
                        size="small"
                        color="info"
                        variant="outlined"
                        sx={{ borderRadius: 1.5, fontWeight: 600 }}
                      />
                    ) : (
                      <Chip
                        icon={<Remove fontSize="small" />}
                        label="None"
                        size="small"
                        variant="outlined"
                        sx={{
                          borderRadius: 1.5,
                          color: "text.disabled",
                          borderColor: "divider",
                        }}
                      />
                    )}
                  </TableCell>
                </>
              )}

              <TableCell align="right">
                <Stack
                  direction="row"
                  spacing={0.5}
                  sx={{ justifyContent: "flex-end", alignItems: "center" }}
                >
                  <Tooltip title="View case">
                    <IconButton
                      aria-label={`View case ${datasetCase.position + 1}`}
                      onClick={() => onView(datasetCase)}
                      size="small"
                      color="primary"
                    >
                      <VisibilityOutlined fontSize="small" />
                    </IconButton>
                  </Tooltip>

                  {editable && (
                    <>
                      <Tooltip title="Edit case">
                        <IconButton
                          aria-label={`Edit case ${datasetCase.position + 1}`}
                          onClick={() => onEdit(datasetCase)}
                          size="small"
                          color="info"
                        >
                          <EditOutlined fontSize="small" />
                        </IconButton>
                      </Tooltip>

                      <Tooltip title="Delete case">
                        <IconButton
                          aria-label={`Delete case ${datasetCase.position + 1}`}
                          onClick={() => onDelete(datasetCase)}
                          size="small"
                          color="error"
                        >
                          <DeleteOutlined fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
