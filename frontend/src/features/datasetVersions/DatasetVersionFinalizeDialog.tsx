import React, { useState } from "react";
import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import type { DatasetVersion } from "./api";
import { useFinalizeDatasetVersion } from "./hooks";

interface DatasetVersionFinalizeDialogProps {
  open: boolean;
  version: DatasetVersion | null;
  onClose: () => void;
}

export function DatasetVersionFinalizeDialog({
  open,
  version,
  onClose,
}: DatasetVersionFinalizeDialogProps) {
  const finalizeMutation = useFinalizeDatasetVersion();
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => {
    if (finalizeMutation.isPending) return;
    setError(null);
    onClose();
  };

  const handleConfirm = async () => {
    if (!version || version.case_count === 0) return;

    setError(null);
    try {
      await finalizeMutation.mutateAsync(version.id);
      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to finalize dataset version. Please try again.",
      );
    }
  };

  const hasNoCases = (version?.case_count ?? 0) === 0;

  return (
    <ConfirmDialog
      open={open}
      title={`Finalize Dataset Version ${version ? `v${version.version}` : ""}`}
      message={
        hasNoCases
          ? `Version v${version?.version} has 0 cases. You must add at least one test case before finalizing.`
          : version
            ? `Finalizing transitions version v${version.version} from Draft to Ready state. Once finalized, it will be locked against further case edits.`
            : ""
      }
      confirmLabel={
        hasNoCases ? "Cannot Finalize (0 Cases)" : "Finalize Version"
      }
      loading={finalizeMutation.isPending}
      onConfirm={() => {
        if (!hasNoCases) {
          void handleConfirm();
        }
      }}
      onCancel={handleClose}
    />
  );
}
