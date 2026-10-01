import {
  FormControl,
  MenuItem,
  Select,
  Stack,
  TablePagination,
  Typography,
} from "@mui/material";

interface DataTablePaginationProps {
  page: number;
  pageSize: number;
  total: number;
  pageSizeOptions?: number[];
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

export function DataTablePagination({
  page,
  pageSize,
  total,
  pageSizeOptions = [25, 50, 100],
  onPageChange,
  onPageSizeChange,
}: DataTablePaginationProps) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      sx={{
        alignItems: { xs: "stretch", sm: "center" },
        justifyContent: "space-between",
        px: 2,
        py: 1,
      }}
    >
      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Rows per page
        </Typography>

        <FormControl size="small">
          <Select
            value={pageSize}
            onChange={(event) => {
              onPageSizeChange(Number(event.target.value));
            }}
            inputProps={{
              "aria-label": "Rows per page",
            }}
          >
            {pageSizeOptions.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      <TablePagination
        component="div"
        count={total}
        page={page}
        rowsPerPage={pageSize}
        onPageChange={(_event, nextPage) => {
          onPageChange(nextPage);
        }}
        onRowsPerPageChange={() => undefined}
        rowsPerPageOptions={[]}
        labelRowsPerPage=""
        sx={{
          ".MuiTablePagination-selectLabel, .MuiTablePagination-select": {
            display: "none",
          },
        }}
      />
    </Stack>
  );
}
