import { ConfirmDialog } from "../../components/common/ConfirmDialog";
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

  const handleConfirm = async () => {
    if (!version) {
      return;
    }

    await deleteMutation.mutateAsync(version.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Dataset Version"
      message={
        version
          ? `Are you sure you want to delete version ${version.version}? This action cannot be undone.`
          : ""
      }
      confirmLabel="Delete"
      loading={deleteMutation.isPending}
      onConfirm={() => {
        void handleConfirm();
      }}
      onCancel={onClose}
    />
  );
}
