import React, { useState } from "react";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  Stack,
} from "@mui/material";
import { DatasetVersionForm } from "./DatasetVersionForm";
import type { UpdateDatasetVersionPayload, DatasetVersion } from "./api";
import { useUpdateDatasetVersion } from "./hooks";

interface DatasetVersionEditDialogProps {
  open: boolean;
  version: DatasetVersion | null;
  onClose: () => void;
}

export function DatasetVersionEditDialog({
  open,
  version,
  onClose,
}: DatasetVersionEditDialogProps) {
  const updateMutation = useUpdateDatasetVersion();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (updateMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetVersionForm>["onSubmit"]
    >[0],
  ) => {
    if (!version) return;

    setError(null);
    try {
      const payload: UpdateDatasetVersionPayload = {
        description: values.description || null,
      };

      await updateMutation.mutateAsync({
        versionId: version.id,
        payload,
      });

      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update dataset version. Please try again.",
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
      <DialogTitle sx={{ pb: 1, fontWeight: 700 }}>
        {version
          ? `Edit Dataset Version v${version.version}`
          : "Edit Dataset Version"}
      </DialogTitle>

      <DialogContent sx={{ pt: 1 }}>
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

          {version && (
            <DatasetVersionForm
              version={version}
              submitting={updateMutation.isPending}
              onSubmit={handleSubmit}
              onCancel={handleClose}
            />
          )}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
