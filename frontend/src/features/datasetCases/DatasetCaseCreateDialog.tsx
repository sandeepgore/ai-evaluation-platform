import React, { useState } from "react";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  Stack,
} from "@mui/material";
import { DatasetCaseForm } from "./DatasetCaseForm";
import type { CreateDatasetCasePayload } from "./api";
import { useCreateDatasetCase } from "./hooks";

interface DatasetCaseCreateDialogProps {
  open: boolean;
  datasetVersionId: string;
  onClose: () => void;
}

export function DatasetCaseCreateDialog({
  open,
  datasetVersionId,
  onClose,
}: DatasetCaseCreateDialogProps) {
  const createMutation = useCreateDatasetCase();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (createMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetCaseForm>["onSubmit"]
    >[0],
  ) => {
    setError(null);

    let caseMetadata: Record<string, unknown> | null = null;

    if (values.case_metadata && values.case_metadata.trim()) {
      try {
        caseMetadata = JSON.parse(values.case_metadata);
      } catch {
        setError(
          "Invalid JSON format in Case Metadata. Please check your syntax.",
        );
        return;
      }
    }

    const payload: CreateDatasetCasePayload = {
      dataset_version_id: datasetVersionId,
      input: values.input,
      expected_output: values.expected_output || null,
      case_metadata: caseMetadata,
    };

    try {
      await createMutation.mutateAsync(payload);
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to add dataset case. Please try again.",
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
        Add Dataset Case
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

          <DatasetCaseForm
            submitting={createMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={handleClose}
          />
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
