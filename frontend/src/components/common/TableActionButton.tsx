import type { ReactNode } from "react";
import { IconButton, Tooltip } from "@mui/material";

interface TableActionButtonProps {
  label: string;
  icon: ReactNode;
  onClick: () => void;
  destructive?: boolean;
  disabled?: boolean;
}

export function TableActionButton({
  label,
  icon,
  onClick,
  destructive = false,
  disabled = false,
}: TableActionButtonProps) {
  return (
    <Tooltip title={label}>
      <span>
        <IconButton
          aria-label={label}
          size="small"
          disabled={disabled}
          onClick={onClick}
          sx={{
            color: destructive ? "error.main" : "text.secondary",
            "&:hover": {
              color: destructive ? "error.main" : "text.primary",
              bgcolor: destructive ? "error.lighter" : "action.hover",
            },
          }}
        >
          {icon}
        </IconButton>
      </span>
    </Tooltip>
  );
}
