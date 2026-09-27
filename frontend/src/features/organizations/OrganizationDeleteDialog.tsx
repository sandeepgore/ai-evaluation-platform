import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import { useAppContextStore } from "../../store/appContextStore";
import type { Organization } from "./api";
import { useDeleteOrganization, useOrganizations } from "./hooks";

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
  const { data: organizations = [] } = useOrganizations();

  const selectedOrganizationId = useAppContextStore(
    (state) => state.selectedOrganizationId,
  );

  const setSelectedOrganizationId = useAppContextStore(
    (state) => state.setSelectedOrganizationId,
  );

  const handleConfirm = async () => {
    if (!organization) {
      return;
    }

    await deleteMutation.mutateAsync(organization.id);

    if (selectedOrganizationId === organization.id) {
      const remainingOrganizations = organizations.filter(
        (item) => item.id !== organization.id,
      );

      setSelectedOrganizationId(
        remainingOrganizations[0]?.id ?? null,
      );
    }

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
