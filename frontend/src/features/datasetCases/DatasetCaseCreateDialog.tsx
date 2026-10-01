import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { DatasetCaseForm } from "./DatasetCaseForm";
import type { CreateDatasetCasePayload } from "./api";
import { useCreateDatasetCase } from "./hooks";

interface DatasetCaseCreateDialogProps {
  open: boolean;
  datasetVersionId: string;
  onClose: () => void;
}

export function DatasetCaseCreateDialog({
  open,
  datasetVersionId,
  onClose,
}: DatasetCaseCreateDialogProps) {
  const createMutation = useCreateDatasetCase();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetCaseForm>["onSubmit"]
    >[0],
  ) => {
    let caseMetadata: Record<string, unknown> | null = null;

    if (values.case_metadata.trim()) {
      caseMetadata = JSON.parse(values.case_metadata);
    }

    const payload: CreateDatasetCasePayload = {
      dataset_version_id: datasetVersionId,
      input: values.input,
      expected_output: values.expected_output || null,
      case_metadata: caseMetadata,
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
      <DialogTitle>Add Dataset Case</DialogTitle>

      <DialogContent>
        <DatasetCaseForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
