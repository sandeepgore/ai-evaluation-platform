import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { DatasetForm } from "./DatasetForm";
import type { CreateDatasetPayload } from "./api";
import { useCreateDataset } from "./hooks";

interface DatasetCreateDialogProps {
  open: boolean;
  projectId: string;
  onClose: () => void;
}

export function DatasetCreateDialog({
  open,
  projectId,
  onClose,
}: DatasetCreateDialogProps) {
  const createMutation = useCreateDataset();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetForm>["onSubmit"]
    >[0],
  ) => {
    const payload: CreateDatasetPayload = {
      project_id: projectId,
      name: values.name,
      slug: values.slug,
      description: values.description || null,
      dataset_type: values.dataset_type,
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
      <DialogTitle>Create Dataset</DialogTitle>

      <DialogContent>
        <DatasetForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
