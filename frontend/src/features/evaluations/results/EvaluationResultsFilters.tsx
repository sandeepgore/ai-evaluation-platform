import { InputAdornment, MenuItem, Stack, TextField } from "@mui/material";
import { SearchOutlined } from "@mui/icons-material";

export type EvaluationResultStatusFilter =
  | "all"
  | "completed"
  | "failed"
  | "pending"
  | "not_applicable";

interface EvaluationResultsFiltersProps {
  searchText: string;
  statusFilter: EvaluationResultStatusFilter;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: EvaluationResultStatusFilter) => void;
  disabled?: boolean;
}

const STATUS_OPTIONS: Array<{
  value: EvaluationResultStatusFilter;
  label: string;
}> = [
  { value: "all", label: "All statuses" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "pending", label: "Pending" },
  { value: "not_applicable", label: "Not applicable" },
];

export default function EvaluationResultsFilters({
  searchText,
  statusFilter,
  onSearchChange,
  onStatusChange,
  disabled = false,
}: EvaluationResultsFiltersProps) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      sx={{ width: "100%" }}
    >
      <TextField
        fullWidth
        size="small"
        label="Search results"
        placeholder="Case ID, result ID, feedback..."
        value={searchText}
        onChange={(event) => onSearchChange(event.target.value)}
        disabled={disabled}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchOutlined fontSize="small" />
              </InputAdornment>
            ),
          },
        }}
      />

      <TextField
        select
        size="small"
        label="Status"
        value={statusFilter}
        onChange={(event) =>
          onStatusChange(event.target.value as EvaluationResultStatusFilter)
        }
        disabled={disabled}
        sx={{ minWidth: { xs: "100%", sm: 190 } }}
      >
        {STATUS_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
    </Stack>
  );
}
