import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import type { Dataset } from "./api";
import { useDeleteDataset } from "./hooks";

interface DatasetDeleteDialogProps {
  open: boolean;
  dataset: Dataset | null;
  onClose: () => void;
}

export function DatasetDeleteDialog({
  open,
  dataset,
  onClose,
}: DatasetDeleteDialogProps) {
  const deleteMutation = useDeleteDataset();

  const handleConfirm = async () => {
    if (!dataset) {
      return;
    }

    await deleteMutation.mutateAsync(dataset.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Dataset"
      message={
        dataset
          ? `Are you sure you want to delete "${dataset.name}"? This action cannot be undone.`
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
