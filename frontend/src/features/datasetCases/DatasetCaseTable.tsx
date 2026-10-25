import {
  DeleteOutlined,
  EditOutlined,
  VisibilityOutlined,
} from "@mui/icons-material";
import {
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
import {
  DataTableSortLabel,
  type SortDirection,
} from "../../components/common/DataTableSortLabel";
import type { DatasetCase } from "./api";
import { StatusChip } from "../../components/common/StatusChip";
import { TableActionButton } from "../../components/common/TableActionButton";

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
                    <StatusChip
                      status={datasetCase.has_reference ? "ready" : "none"}
                      label={datasetCase.has_reference ? "Ready" : "None"}
                    />
                  </TableCell>

                  <TableCell>
                    <StatusChip
                      status={datasetCase.has_context ? "ready" : "none"}
                      label={datasetCase.has_context ? "Ready" : "None"}
                    />
                  </TableCell>
                </>
              )}

              <TableCell align="right">
                <Stack
                  direction="row"
                  spacing={0.5}
                  sx={{ justifyContent: "flex-end", alignItems: "center" }}
                >
                  <TableActionButton label={`View case ${datasetCase.position + 1}`} icon={<VisibilityOutlined fontSize="small" />} onClick={() => onView(datasetCase)} />

                  {editable && (
                    <>
                      <TableActionButton label={`Edit case ${datasetCase.position + 1}`} icon={<EditOutlined fontSize="small" />} onClick={() => onEdit(datasetCase)} />
                      <TableActionButton label={`Delete case ${datasetCase.position + 1}`} icon={<DeleteOutlined fontSize="small" />} destructive onClick={() => onDelete(datasetCase)} />
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
