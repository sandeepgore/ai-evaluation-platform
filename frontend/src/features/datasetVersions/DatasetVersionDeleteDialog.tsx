import React, { useState } from "react";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Button,
  CircularProgress,
  Typography,
  Stack,
} from "@mui/material";
import type { DatasetVersion } from "./api";
import { useDeleteDatasetVersion } from "./hooks";

interface DatasetVersionDeleteDialogProps {
  open: boolean;
  version: DatasetVersion | null;
  onClose: () => void;
}

export function DatasetVersionDeleteDialog({
  open,
  version,
  onClose,
}: DatasetVersionDeleteDialogProps) {
  const deleteMutation = useDeleteDatasetVersion();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (deleteMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleConfirm = async () => {
    if (!version) return;

    setError(null);
    try {
      await deleteMutation.mutateAsync(version.id);
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete dataset version. Please try again.",
      );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="xs"
      fullWidth
      slotProps={{
        paper: {
          sx: { borderRadius: 3, p: 1 },
        },
      }}
    >
      <DialogTitle sx={{ fontWeight: 700 }}>Delete Dataset Version</DialogTitle>

      <DialogContent>
        <Stack spacing={1.5}>
          <Typography variant="body2" color="text.secondary">
            {version
              ? `Are you sure you want to delete version v${version.version}? This action cannot be undone.`
              : ""}
          </Typography>

          {error && (
            <Alert
              severity="error"
              sx={{ borderRadius: 2 }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={handleClose}
          disabled={deleteMutation.isPending}
          sx={{ borderRadius: 2, textTransform: "none", fontWeight: 600 }}
        >
          Cancel
        </Button>

        <Button
          variant="contained"
          color="error"
          disableElevation
          onClick={() => {
            void handleConfirm();
          }}
          disabled={deleteMutation.isPending}
          startIcon={
            deleteMutation.isPending ? (
              <CircularProgress size={16} color="inherit" />
            ) : null
          }
          sx={{
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
            px: 2.5,
          }}
        >
          {deleteMutation.isPending ? "Deleting..." : "Delete Version"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
