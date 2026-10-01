import { ConfirmDialog } from "../../components/common/ConfirmDialog";
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

  const handleConfirm = async () => {
    if (!datasetCase) {
      return;
    }

    await deleteMutation.mutateAsync(datasetCase.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Dataset Case"
      message={
        datasetCase
          ? "Are you sure you want to delete this dataset case? This action cannot be undone."
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
