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

  const handleClose = () => {
    if (deleteMutation.isPending) return;
    deleteMutation.reset();
    onClose();
  };

  const handleConfirm = async () => {
    if (!dataset) return;

    try {
      await deleteMutation.mutateAsync(dataset.id);
      handleClose();
    } catch {
      // Error state is handled at hook level or caught by React Query
    }
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Dataset"
      message={
        dataset
          ? `Are you sure you want to delete "${dataset.name}"? This will permanently remove the dataset and all associated versions and test cases. This action cannot be undone.`
          : "Are you sure you want to delete this dataset?"
      }
      confirmLabel="Delete Dataset"
      loading={deleteMutation.isPending}
      onConfirm={() => {
        void handleConfirm();
      }}
      onCancel={handleClose}
    />
  );
}
