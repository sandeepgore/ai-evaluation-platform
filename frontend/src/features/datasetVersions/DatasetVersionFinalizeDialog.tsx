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

  const handleConfirm = async () => {
    if (!version) {
      return;
    }

    await finalizeMutation.mutateAsync(version.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Finalize Dataset Version"
      message={
        version
          ? `Are you sure you want to finalize version ${version.version}? Once finalized, it will be marked as ready.`
          : ""
      }
      confirmLabel="Finalize"
      loading={finalizeMutation.isPending}
      onConfirm={() => {
        void handleConfirm();
      }}
      onCancel={onClose}
    />
  );
}
