import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { ProjectForm } from "./ProjectForm";
import type { CreateProjectPayload } from "./api";
import { useCreateProject } from "./hooks";

interface ProjectCreateDialogProps {
  open: boolean;
  organizationId: string;
  onClose: () => void;
}

export function ProjectCreateDialog({
  open,
  organizationId,
  onClose,
}: ProjectCreateDialogProps) {
  const createMutation = useCreateProject();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof ProjectForm>["onSubmit"]
    >[0],
  ) => {
    const payload: CreateProjectPayload = {
      organization_id: organizationId,
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
      <DialogTitle>Create Project</DialogTitle>

      <DialogContent>
        <ProjectForm
          submitting={createMutation.isPending}
          onSubmit={handleSubmit}
          onCancel={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
