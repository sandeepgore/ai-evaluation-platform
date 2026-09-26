import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { OrganizationForm } from "./OrganizationForm";
import type { CreateOrganizationPayload } from "./api";
import { useCreateOrganization } from "./hooks";

interface OrganizationCreateDialogProps {
  open: boolean;
  onClose: () => void;
}

export function OrganizationCreateDialog({
  open,
  onClose,
}: OrganizationCreateDialogProps) {
  const createMutation = useCreateOrganization();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof OrganizationForm>["onSubmit"]
    >[0],
  ) => {
    const payload: CreateOrganizationPayload = {
      name: values.name,
      slug: values.slug,
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
      <DialogTitle>Create Organization</DialogTitle>

      <DialogContent>
        <OrganizationForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}