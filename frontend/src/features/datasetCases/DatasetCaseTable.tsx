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
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 80 }}>
              <DataTableSortLabel
                field="position"
                activeField={sortField}
                direction={sortDirection}
                label="#"
                onSort={onSort}
              />
            </TableCell>

            <TableCell>
              <DataTableSortLabel
                field="input"
                activeField={sortField}
                direction={sortDirection}
                label="Input"
                onSort={onSort}
              />
            </TableCell>

            <TableCell>
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
                <TableCell>
                  <DataTableSortLabel
                    field="has_reference"
                    activeField={sortField}
                    direction={sortDirection}
                    label="Reference"
                    onSort={onSort}
                  />
                </TableCell>

                <TableCell>
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

            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {cases.map((datasetCase) => (
            <TableRow
              key={datasetCase.id}
              hover
              sx={{
                "&:last-child td, &:last-child th": {
                  border: 0,
                },
              }}
            >
              <TableCell>
                <Typography variant="body2">
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
                      : "text.secondary"
                  }
                  sx={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {datasetCase.expected_output ?? "Not provided"}
                </Typography>
              </TableCell>

              {ready && (
                <>
                  <TableCell>
                    <Typography
                      variant="body2"
                      aria-label={
                        datasetCase.has_reference
                          ? "Reference available"
                          : "Reference not available"
                      }
                      sx={{
                        fontWeight: 600,
                      }}
                    >
                      {datasetCase.has_reference ? "✓" : "—"}
                    </Typography>
                  </TableCell>

                  <TableCell>
                    <Typography
                      variant="body2"
                      aria-label={
                        datasetCase.has_context
                          ? "Context available"
                          : "Context not available"
                      }
                      sx={{
                        fontWeight: 600,
                      }}
                    >
                      {datasetCase.has_context ? "✓" : "—"}
                    </Typography>
                  </TableCell>
                </>
              )}

              <TableCell align="right">
                <Stack
                  direction="row"
                  spacing={0.5}
                  sx={{ justifyContent: "flex-end" }}
                >
                  <Tooltip title="View case">
                    <IconButton
                      aria-label={`View case ${datasetCase.position + 1}`}
                      onClick={() => onView(datasetCase)}
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

                  {editable && (
                    <>
                      <Tooltip title="Edit case">
                        <IconButton
                          aria-label={`Edit case ${datasetCase.position + 1}`}
                          onClick={() => onEdit(datasetCase)}
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

                      <Tooltip title="Delete case">
                        <IconButton
                          aria-label={`Delete case ${datasetCase.position + 1}`}
                          onClick={() => onDelete(datasetCase)}
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
