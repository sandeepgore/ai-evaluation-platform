import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import { DatasetVersionForm } from "./DatasetVersionForm";
import type { UpdateDatasetVersionPayload } from "./api";
import { useUpdateDatasetVersion } from "./hooks";
import type { DatasetVersion } from "./api";

interface DatasetVersionEditDialogProps {
  open: boolean;
  version: DatasetVersion | null;
  onClose: () => void;
}

export function DatasetVersionEditDialog({
  open,
  version,
  onClose,
}: DatasetVersionEditDialogProps) {
  const updateMutation = useUpdateDatasetVersion();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetVersionForm>["onSubmit"]
    >[0],
  ) => {
    if (!version) {
      return;
    }

    const payload: UpdateDatasetVersionPayload = {
      description: values.description || null,
    };

    await updateMutation.mutateAsync({
      versionId: version.id,
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
      <DialogTitle>Edit Dataset Version</DialogTitle>

      <DialogContent>
        {version && (
          <DatasetVersionForm
            version={version}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
