import { ErrorOutlineOutlined } from "@mui/icons-material";
import { Alert, Stack, Typography } from "@mui/material";

interface ErrorStateProps {
  title?: string;
  message?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "We couldn't load the requested data.",
}: ErrorStateProps) {
  return (
    <Stack spacing={2} sx={{ py: 4 }}>
      <Alert severity="error" icon={<ErrorOutlineOutlined />}>
        <Typography variant="subtitle2">{title}</Typography>
        <Typography variant="body2">{message}</Typography>
      </Alert>
    </Stack>
  );
}