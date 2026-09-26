import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { OrganizationForm } from "./OrganizationForm";
import type { UpdateOrganizationPayload } from "./api";
import { useUpdateOrganization } from "./hooks";
import type { Organization } from "./api";

interface OrganizationEditDialogProps {
  open: boolean;
  organization: Organization | null;
  onClose: () => void;
}

export function OrganizationEditDialog({
  open,
  organization,
  onClose,
}: OrganizationEditDialogProps) {
  const updateMutation = useUpdateOrganization();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof OrganizationForm>["onSubmit"]
    >[0],
  ) => {
    if (!organization) {
      return;
    }

    const payload: UpdateOrganizationPayload = {
      name: values.name,
      slug: values.slug,
      description: values.description || null,
      is_active: values.is_active,
    };

    await updateMutation.mutateAsync({
      organizationId: organization.id,
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
      <DialogTitle>Edit Organization</DialogTitle>

      <DialogContent>
        {organization && (
          <OrganizationForm
            organization={organization}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}