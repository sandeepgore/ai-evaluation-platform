import { Chip } from "@mui/material";
import type { DatasetVersionStatus } from "./api";

interface DatasetVersionStatusChipProps {
  status: DatasetVersionStatus;
}

const statusConfig: Record<
  DatasetVersionStatus,
  {
    label: string;
    color:
      | "default"
      | "primary"
      | "secondary"
      | "error"
      | "info"
      | "success"
      | "warning";
  }
> = {
  draft: {
    label: "Draft",
    color: "default",
  },
  ready: {
    label: "Ready",
    color: "success",
  },
  archived: {
    label: "Archived",
    color: "warning",
  },
};

export function DatasetVersionStatusChip({
  status,
}: DatasetVersionStatusChipProps) {
  const config = statusConfig[status];

  return (
    <Chip
      size="small"
      label={config.label}
      color={config.color}
      variant={status === "draft" ? "outlined" : "filled"}
    />
  );
}
