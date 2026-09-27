import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { ModelForm } from "./ModelForm";
import type { CreateModelPayload } from "./api";
import { useCreateModel } from "./hooks";

interface ModelCreateDialogProps {
  open: boolean;
  projectId: string;
  onClose: () => void;
}

export function ModelCreateDialog({
  open,
  projectId,
  onClose,
}: ModelCreateDialogProps) {
  const createMutation = useCreateModel();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof ModelForm>["onSubmit"]
    >[0],
  ) => {
    const payload: CreateModelPayload = {
      project_id: projectId,
      name: values.name,
      provider: values.provider,
      model_identifier: values.model_identifier,
      model_type: values.model_type,
      configuration: values.configuration,
      input_price_per_million:
        values.input_price_per_million,
      output_price_per_million:
        values.output_price_per_million,
      pricing_currency: values.pricing_currency,
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
      <DialogTitle>Create Model</DialogTitle>

      <DialogContent>
        <ModelForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
