import { zodResolver } from "@hookform/resolvers/zod";
import { Button, MenuItem, Stack, TextField } from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
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
    .max(100, "Slug must be 100 characters or fewer"),
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

export function DatasetForm({
  dataset,
  submitting = false,
  onSubmit,
  onCancel,
}: DatasetFormProps) {
  const isEdit = Boolean(dataset);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatasetFormValues>({
    resolver: zodResolver(datasetFormSchema),
    defaultValues: {
      name: dataset?.name ?? "",
      slug: dataset?.slug ?? "",
      description: dataset?.description ?? "",
      dataset_type: dataset?.dataset_type ?? "custom",
    },
  });

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

      <TextField
        select
        label="Dataset Type"
        fullWidth
        defaultValue={dataset?.dataset_type ?? "custom"}
        {...register("dataset_type")}
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

      <Stack direction="row" spacing={1.5} sx={{ justifyContent: "flex-end" }}>
        <Button type="button" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>

        <Button type="submit" variant="contained" disabled={submitting}>
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
