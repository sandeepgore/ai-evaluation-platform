import { InboxOutlined } from "@mui/icons-material";
import { Stack, Typography } from "@mui/material";

interface EmptyStateProps {
  title: string;
  description?: string;
}

export function EmptyState({
  title,
  description,
}: EmptyStateProps) {
  return (
    <Stack
      spacing={1}
      sx={{
        alignItems: "center",
        justifyContent: "center",
        py: 8,
        textAlign: "center",
      }}
    >
      <InboxOutlined color="disabled" sx={{ fontSize: 48 }} />
      <Typography variant="h6">{title}</Typography>
      {description && (
        <Typography color="text.secondary">
          {description}
        </Typography>
      )}
    </Stack>
  );
}