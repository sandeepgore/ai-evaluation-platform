import { Chip } from "@mui/material";

interface StatusChipProps {
  active?: boolean;
  status?: string;
  label?: string;
}

const statusColors: Record<string, "default" | "info" | "success" | "error" | "warning"> = {
  active: "success",
  ready: "success",
  completed: "success",
  success: "success",
  passed: "success",
  available: "success",
  running: "info",
  processing: "info",
  in_progress: "info",
  pending: "warning",
  queued: "warning",
  draft: "warning",
  optional: "warning",
  failed: "error",
  error: "error",
  rejected: "error",
  archived: "warning",
  inactive: "default",
  cancelled: "default",
  canceled: "default",
  not_applicable: "default",
  none: "default",
  empty: "default",
};

function formatStatus(status: string) {
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function StatusChip({ active, status, label }: StatusChipProps) {
  const value = status ?? (active ? "active" : "inactive");
  const normalized = value.toLowerCase().replaceAll(" ", "_");
  return (
    <Chip
      size="small"
      label={label ?? formatStatus(value)}
      color={statusColors[normalized] ?? "default"}
      variant="outlined"
      sx={{ height: 24, borderRadius: 1.5, fontWeight: 600 }}
    />
  );
}
