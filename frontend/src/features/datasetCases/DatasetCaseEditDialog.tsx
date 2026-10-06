import React, { useState } from "react";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  Stack,
} from "@mui/material";
import { DatasetCaseForm } from "./DatasetCaseForm";
import type { DatasetCase, UpdateDatasetCasePayload } from "./api";
import { useUpdateDatasetCase } from "./hooks";

interface DatasetCaseEditDialogProps {
  open: boolean;
  datasetCase: DatasetCase | null;
  onClose: () => void;
}

export function DatasetCaseEditDialog({
  open,
  datasetCase,
  onClose,
}: DatasetCaseEditDialogProps) {
  const updateMutation = useUpdateDatasetCase();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (updateMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetCaseForm>["onSubmit"]
    >[0],
  ) => {
    if (!datasetCase) return;

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

    const payload: UpdateDatasetCasePayload = {
      input: values.input,
      expected_output: values.expected_output || null,
      case_metadata: caseMetadata,
    };

    try {
      await updateMutation.mutateAsync({
        caseId: datasetCase.id,
        payload,
      });
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update dataset case. Please try again.",
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
        Edit Dataset Case
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

          {datasetCase && (
            <DatasetCaseForm
              datasetCase={datasetCase}
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
