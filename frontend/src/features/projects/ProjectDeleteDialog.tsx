import { ConfirmDialog } from "../../components/common/ConfirmDialog";
import type { Project } from "./api";
import { useDeleteProject } from "./hooks";

interface ProjectDeleteDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
}

export function ProjectDeleteDialog({
  open,
  project,
  onClose,
}: ProjectDeleteDialogProps) {
  const deleteMutation = useDeleteProject();

  const handleConfirm = async () => {
    if (!project) {
      return;
    }

    await deleteMutation.mutateAsync(project.id);
    onClose();
  };

  return (
    <ConfirmDialog
      open={open}
      title="Delete Project"
      message={
        project
          ? `Are you sure you want to delete "${project.name}"? This action cannot be undone.`
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
