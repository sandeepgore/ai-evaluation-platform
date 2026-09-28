import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { DatasetForm } from "./DatasetForm";
import type {
  Dataset,
  UpdateDatasetPayload,
} from "./api";
import { useUpdateDataset } from "./hooks";

interface DatasetEditDialogProps {
  open: boolean;
  dataset: Dataset | null;
  onClose: () => void;
}

export function DatasetEditDialog({
  open,
  dataset,
  onClose,
}: DatasetEditDialogProps) {
  const updateMutation = useUpdateDataset();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetForm>["onSubmit"]
    >[0],
  ) => {
    if (!dataset) {
      return;
    }

    const payload: UpdateDatasetPayload = {
      name: values.name,
      slug: values.slug,
      description: values.description || null,
      dataset_type: values.dataset_type,
    };

    await updateMutation.mutateAsync({
      datasetId: dataset.id,
      payload,
    });

    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={updateMutation.isPending ? undefined : onClose}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Edit Dataset</DialogTitle>

      <DialogContent>
        {dataset && (
          <DatasetForm
            dataset={dataset}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
