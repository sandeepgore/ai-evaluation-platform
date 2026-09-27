import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { ProjectForm } from "./ProjectForm";
import type {
  Project,
  UpdateProjectPayload,
} from "./api";
import { useUpdateProject } from "./hooks";

interface ProjectEditDialogProps {
  open: boolean;
  project: Project | null;
  onClose: () => void;
}

export function ProjectEditDialog({
  open,
  project,
  onClose,
}: ProjectEditDialogProps) {
  const updateMutation = useUpdateProject();

  const handleSubmit = async (
    values: Parameters<
      React.ComponentProps<typeof ProjectForm>["onSubmit"]
    >[0],
  ) => {
    if (!project) {
      return;
    }

    const payload: UpdateProjectPayload = {
      name: values.name,
      slug: values.slug,
      description: values.description || null,
    };

    await updateMutation.mutateAsync({
      projectId: project.id,
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
      <DialogTitle>Edit Project</DialogTitle>

      <DialogContent>
        {project && (
          <ProjectForm
            project={project}
            submitting={updateMutation.isPending}
            onSubmit={handleSubmit}
            onCancel={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
