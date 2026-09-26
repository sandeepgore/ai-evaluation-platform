import { Chip } from "@mui/material";

interface StatusChipProps {
  active: boolean;
}

export function StatusChip({ active }: StatusChipProps) {
  return (
    <Chip
      size="small"
      label={active ? "Active" : "Inactive"}
      color={active ? "success" : "default"}
      variant={active ? "filled" : "outlined"}
    />
  );
}