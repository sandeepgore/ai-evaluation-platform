import React, { useState } from "react";
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import type { DatasetCase } from "./api";
import { useDeleteDatasetCase } from "./hooks";

interface DatasetCaseDeleteDialogProps {
  open: boolean;
  datasetCase: DatasetCase | null;
  onClose: () => void;
}

export function DatasetCaseDeleteDialog({
  open,
  datasetCase,
  onClose,
}: DatasetCaseDeleteDialogProps) {
  const deleteMutation = useDeleteDatasetCase();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (deleteMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleConfirm = async () => {
    if (!datasetCase) return;

    setError(null);
    try {
      await deleteMutation.mutateAsync(datasetCase.id);
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete dataset case. Please try again.",
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
      <DialogTitle sx={{ fontWeight: 700, pb: 1 }}>
        Delete Dataset Case
      </DialogTitle>

      <DialogContent>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: error ? 2 : 0 }}
        >
          {datasetCase
            ? "Are you sure you want to delete this dataset case? This action cannot be undone."
            : ""}
        </Typography>

        {error && (
          <Alert
            severity="error"
            sx={{ borderRadius: 2, mt: 1 }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}
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
          {deleteMutation.isPending ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
