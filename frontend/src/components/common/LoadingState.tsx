import { CircularProgress, Stack, Typography } from "@mui/material";

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({
  message = "Loading...",
}: LoadingStateProps) {
  return (
    <Stack
      spacing={2}
      sx={{
        alignItems: "center",
        justifyContent: "center",
        py: 8,
      }}
    >
      <CircularProgress />
      <Typography color="text.secondary">{message}</Typography>
    </Stack>
  );
}