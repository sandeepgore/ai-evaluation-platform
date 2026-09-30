import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { DatasetVersionForm } from "./DatasetVersionForm";
import type { CreateDatasetVersionPayload } from "./api";
import { useCreateDatasetVersion } from "./hooks";

interface DatasetVersionCreateDialogProps {
  open: boolean;
  datasetId: string;
  onClose: () => void;
}

export function DatasetVersionCreateDialog({
  open,
  datasetId,
  onClose,
}: DatasetVersionCreateDialogProps) {
  const createMutation = useCreateDatasetVersion();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetVersionForm>["onSubmit"]
    >[0],
  ) => {
    const payload: CreateDatasetVersionPayload = {
      dataset_id: datasetId,
      description: values.description || null,
    };

    await createMutation.mutateAsync(payload);

    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={createMutation.isPending ? undefined : onClose}
      fullWidth
      maxWidth="sm"
    >
      <DialogTitle>Create Dataset Version</DialogTitle>

      <DialogContent>
        <DatasetVersionForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
