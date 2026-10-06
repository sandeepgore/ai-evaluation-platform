import React from "react";
import { Chip, alpha, useTheme } from "@mui/material";
import EditNoteIcon from "@mui/icons-material/EditNote";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import ArchiveOutlinedIcon from "@mui/icons-material/ArchiveOutlined";
import HelpOutlineIcon from "@mui/icons-material/HelpOutlined";
import type { DatasetVersionStatus } from "./api";

interface DatasetVersionStatusChipProps {
  status: DatasetVersionStatus;
}

interface StatusConfigItem {
  label: string;
  colorKey: "primary" | "success" | "warning" | "default";
  icon: React.ReactElement;
}

const statusConfig: Record<DatasetVersionStatus, StatusConfigItem> = {
  draft: {
    label: "Draft",
    colorKey: "primary",
    icon: <EditNoteIcon sx={{ fontSize: "14px !important" }} />,
  },
  ready: {
    label: "Ready",
    colorKey: "success",
    icon: <CheckCircleOutlinedIcon sx={{ fontSize: "13px !important" }} />,
  },
  archived: {
    label: "Archived",
    colorKey: "warning",
    icon: <ArchiveOutlinedIcon sx={{ fontSize: "13px !important" }} />,
  },
};

const fallbackConfig: StatusConfigItem = {
  label: "Unknown",
  colorKey: "default",
  icon: <HelpOutlineIcon sx={{ fontSize: "13px !important" }} />,
};

export function DatasetVersionStatusChip({
  status,
}: DatasetVersionStatusChipProps) {
  const theme = useTheme();
  const config = statusConfig[status] ?? fallbackConfig;

  // Resolve dynamic colors based on theme context
  const paletteColor =
    config.colorKey === "default"
      ? theme.palette.text.secondary
      : theme.palette[config.colorKey].main;

  return (
    <Chip
      size="small"
      icon={config.icon}
      label={config.label}
      sx={{
        height: 22,
        fontSize: "0.6875rem",
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        borderRadius: 1.5,
        px: 0.5,
        bgcolor: alpha(paletteColor, 0.1),
        color: paletteColor,
        border: "1px solid",
        borderColor: alpha(paletteColor, 0.25),
        "& .MuiChip-icon": {
          color: "inherit",
          ml: 0.5,
          mr: -0.25,
        },
      }}
    />
  );
}
