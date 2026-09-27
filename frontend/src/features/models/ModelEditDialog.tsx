import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { ModelForm } from "./ModelForm";
import type {
  Model,
  UpdateModelPayload,
} from "./api";
import { useUpdateModel } from "./hooks";

interface ModelEditDialogProps {
  open: boolean;
  model: Model | null;
  onClose: () => void;
}

export function ModelEditDialog({
  open,
  model,
  onClose,
}: ModelEditDialogProps) {
  const updateMutation = useUpdateModel();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof ModelForm>["onSubmit"]
    >[0],
  ) => {
    if (!model) {
      return;
    }

    const payload: UpdateModelPayload = {
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

    await updateMutation.mutateAsync({
      modelId: model.id,
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
      <DialogTitle>Edit Model</DialogTitle>

      <DialogContent>
        {model && (
          <ModelForm
            model={model}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
