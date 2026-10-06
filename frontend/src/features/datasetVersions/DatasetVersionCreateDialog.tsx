import React, { useState } from "react";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  Stack,
} from "@mui/material";
import { DatasetVersionForm } from "./DatasetVersionForm";
import type { CreateDatasetVersionPayload } from "./api";
import { useCreateDatasetVersion } from "./hooks";

interface DatasetVersionCreateDialogProps {
  open: boolean;
  datasetId: string;
  onClose: () => void;
}

export function DatasetVersionCreateDialog({
  open,
  datasetId,
  onClose,
}: DatasetVersionCreateDialogProps) {
  const createMutation = useCreateDatasetVersion();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (createMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetVersionForm>["onSubmit"]
    >[0],
  ) => {
    setError(null);

    const payload: CreateDatasetVersionPayload = {
      dataset_id: datasetId,
      description: values.description || null,
    };

    try {
      await createMutation.mutateAsync(payload);
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create dataset version. Please try again.",
      );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      slotProps={{
        paper: {
          sx: {
            borderRadius: 3,
            p: 1,
          },
        },
      }}
    >
      <DialogTitle sx={{ fontWeight: 700, pb: 1 }}>
        Create Dataset Version
      </DialogTitle>

      <DialogContent sx={{ pt: "8px !important" }}>
        <Stack spacing={2}>
          {error && (
            <Alert
              severity="error"
              sx={{ borderRadius: 2 }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}

          <DatasetVersionForm
            submitting={createMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={handleClose}
          />
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
