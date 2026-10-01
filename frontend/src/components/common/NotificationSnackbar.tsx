import { Alert, Snackbar } from "@mui/material";

export type NotificationSeverity = "success" | "error" | "warning" | "info";

interface NotificationSnackbarProps {
  open: boolean;
  message: string;
  severity: NotificationSeverity;
  onClose: () => void;
}

export function NotificationSnackbar({
  open,
  message,
  severity,
  onClose,
}: NotificationSnackbarProps) {
  return (
    <Snackbar
      open={open}
      autoHideDuration={5000}
      onClose={onClose}
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
    >
      <Alert
        onClose={onClose}
        severity={severity}
        variant="filled"
        sx={{ width: "100%" }}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}
