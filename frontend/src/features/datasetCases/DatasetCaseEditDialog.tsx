import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { DatasetCaseForm } from "./DatasetCaseForm";
import type { UpdateDatasetCasePayload } from "./api";
import { useUpdateDatasetCase } from "./hooks";
import type { DatasetCase } from "./api";

interface DatasetCaseEditDialogProps {
  open: boolean;
  datasetCase: DatasetCase | null;
  onClose: () => void;
}

export function DatasetCaseEditDialog({
  open,
  datasetCase,
  onClose,
}: DatasetCaseEditDialogProps) {
  const updateMutation = useUpdateDatasetCase();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof DatasetCaseForm>["onSubmit"]
    >[0],
  ) => {
    if (!datasetCase) {
      return;
    }

    let caseMetadata: Record<string, unknown> | null = null;

    if (values.case_metadata.trim()) {
      caseMetadata = JSON.parse(values.case_metadata);
    }

    const payload: UpdateDatasetCasePayload = {
      input: values.input,
      expected_output: values.expected_output || null,
      case_metadata: caseMetadata,
    };

    await updateMutation.mutateAsync({
      caseId: datasetCase.id,
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
      <DialogTitle>Edit Dataset Case</DialogTitle>

      <DialogContent>
        {datasetCase && (
          <DatasetCaseForm
            datasetCase={datasetCase}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
