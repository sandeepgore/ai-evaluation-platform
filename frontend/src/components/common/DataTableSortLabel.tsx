import { UnfoldMoreOutlined } from "@mui/icons-material";
import { TableSortLabel } from "@mui/material";
import type { ReactNode } from "react";

export type SortDirection = "asc" | "desc";

interface DataTableSortLabelProps<TField extends string> {
  field: TField;
  activeField: TField;
  direction: SortDirection;
  label: ReactNode;
  onSort: (field: TField) => void;
}

export function DataTableSortLabel<TField extends string>({
  field,
  activeField,
  direction,
  label,
  onSort,
}: DataTableSortLabelProps<TField>) {
  const active = activeField === field;

  return (
    <TableSortLabel
      active={active}
      direction={active ? direction : "asc"}
      onClick={() => onSort(field)}
      IconComponent={active ? undefined : UnfoldMoreOutlined}
    >
      {label}
    </TableSortLabel>
  );
}
