import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import type { Organization } from "./api";
import { useDeleteOrganization } from "./hooks";

interface OrganizationDeleteDialogProps {
  open: boolean;
  organization: Organization | null;
  onClose: () => void;
}

export function OrganizationDeleteDialog({
  open,
  organization,
  onClose,
}: OrganizationDeleteDialogProps) {
  const deleteMutation = useDeleteOrganization();

  const handleConfirm = async () => {
    if (!organization) {
      return;
    }

    await deleteMutation.mutateAsync(organization.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Organization"
      message={
        organization
          ? `Are you sure you want to delete "${organization.name}"? This action cannot be undone.`
          : ""
      }
      confirmLabel="Delete"
      loading={deleteMutation.isPending}
      onConfirm={() => {
        void handleConfirm();
      }}
      onCancel={onClose}
    />
  );
}