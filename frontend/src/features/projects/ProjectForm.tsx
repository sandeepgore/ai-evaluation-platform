import { zodResolver } from "@hookform/resolvers/zod";
import {
  Button,
  Stack,
  TextField,
} from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Project } from "./api";

const projectFormSchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(150, "Name must be 150 characters or fewer"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .max(100, "Slug must be 100 characters or fewer"),
  description: z.string(),
});

type ProjectFormValues = z.infer<typeof projectFormSchema>;

interface ProjectFormProps {
  project?: Project;
  submitting?: boolean;
  onSubmit: (
    values: ProjectFormValues,
  ) => void | Promise<void>;
  onCancel: () => void;
}

export function ProjectForm({
  project,
  submitting = false,
  onSubmit,
  onCancel,
}: ProjectFormProps) {
  const isEdit = Boolean(project);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: project?.name ?? "",
      slug: project?.slug ?? "",
      description: project?.description ?? "",
    },
  });

  useEffect(() => {
    reset({
      name: project?.name ?? "",
      slug: project?.slug ?? "",
      description: project?.description ?? "",
    });
  }, [project, reset]);

  return (
    <Stack
      component="form"
      spacing={2.5}
      onSubmit={handleSubmit(onSubmit)}
    >
      <TextField
        label="Name"
        fullWidth
        {...register("name")}
        error={Boolean(errors.name)}
        helperText={errors.name?.message}
        disabled={submitting}
      />

      <TextField
        label="Slug"
        fullWidth
        {...register("slug")}
        error={Boolean(errors.slug)}
        helperText={errors.slug?.message}
        disabled={submitting}
      />

      <TextField
        label="Description"
        fullWidth
        multiline
        minRows={3}
        {...register("description")}
        error={Boolean(errors.description)}
        helperText={errors.description?.message}
        disabled={submitting}
      />

      <Stack
        direction="row"
        spacing={1.5}
        sx={{ justifyContent: "flex-end" }}
      >
        <Button
          type="button"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </Button>

        <Button
          type="submit"
          variant="contained"
          disabled={submitting}
        >
          {submitting
            ? "Saving..."
            : isEdit
              ? "Save Changes"
              : "Create Project"}
        </Button>
      </Stack>
    </Stack>
  );
}
