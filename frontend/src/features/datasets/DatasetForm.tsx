import { zodResolver } from "@hookform/resolvers/zod";
import { Button, MenuItem, Stack, TextField } from "@mui/material";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import type { Dataset, DatasetType } from "./api";

const datasetFormSchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(150, "Name must be 150 characters or fewer"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .max(100, "Slug must be 100 characters or fewer")
    .regex(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      "Slug must contain only lowercase letters, numbers, and hyphens",
    ),
  description: z.string(),
  dataset_type: z.enum([
    "generation",
    "classification",
    "rag",
    "conversation",
    "custom",
  ]),
});

type DatasetFormValues = z.infer<typeof datasetFormSchema>;

interface DatasetFormProps {
  dataset?: Dataset;
  submitting?: boolean;
  onSubmit: (values: DatasetFormValues) => void | Promise<void>;
  onCancel: () => void;
}

const datasetTypes: Array<{
  value: DatasetType;
  label: string;
}> = [
  { value: "generation", label: "Generation" },
  { value: "classification", label: "Classification" },
  { value: "rag", label: "RAG" },
  { value: "conversation", label: "Conversation" },
  { value: "custom", label: "Custom" },
];

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function DatasetForm({
  dataset,
  submitting = false,
  onSubmit,
  onCancel,
}: DatasetFormProps) {
  const isEdit = Boolean(dataset);

  const {
    register,
    control,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, dirtyFields },
  } = useForm<DatasetFormValues>({
    resolver: zodResolver(datasetFormSchema),
    defaultValues: {
      name: dataset?.name ?? "",
      slug: dataset?.slug ?? "",
      description: dataset?.description ?? "",
      dataset_type: dataset?.dataset_type ?? "custom",
    },
  });

  const nameValue = watch("name");

  // Auto-generate slug when creating a new dataset if slug hasn't been manually modified
  useEffect(() => {
    if (!isEdit && !dirtyFields.slug && nameValue) {
      setValue("slug", slugify(nameValue), { shouldValidate: true });
    }
  }, [nameValue, isEdit, dirtyFields.slug, setValue]);

  useEffect(() => {
    reset({
      name: dataset?.name ?? "",
      slug: dataset?.slug ?? "",
      description: dataset?.description ?? "",
      dataset_type: dataset?.dataset_type ?? "custom",
    });
  }, [dataset, reset]);

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit(onSubmit)}>
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

      <Controller
        name="dataset_type"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            select
            label="Dataset Type"
            fullWidth
            error={Boolean(errors.dataset_type)}
            helperText={errors.dataset_type?.message}
            disabled={submitting}
          >
            {datasetTypes.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </TextField>
        )}
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
        sx={{ justifyContent: "flex-end", pt: 1 }}
      >
        <Button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          sx={{ textTransform: "none", fontWeight: 600 }}
        >
          Cancel
        </Button>

        <Button
          type="submit"
          variant="contained"
          disableElevation
          disabled={submitting}
          sx={{ textTransform: "none", fontWeight: 600, borderRadius: 2 }}
        >
          {submitting
            ? "Saving..."
            : isEdit
              ? "Save Changes"
              : "Create Dataset"}
        </Button>
      </Stack>
    </Stack>
  );
}
