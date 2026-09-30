import { zodResolver } from "@hookform/resolvers/zod";
import { Button, Stack, TextField } from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { DatasetVersion } from "./api";

const datasetVersionFormSchema = z.object({
  description: z.string(),
});

type DatasetVersionFormValues = z.infer<typeof datasetVersionFormSchema>;

interface DatasetVersionFormProps {
  version?: DatasetVersion;
  submitting?: boolean;
  onSubmit: (values: DatasetVersionFormValues) => void | Promise<void>;
  onCancel: () => void;
}

export function DatasetVersionForm({
  version,
  submitting = false,
  onSubmit,
  onCancel,
}: DatasetVersionFormProps) {
  const isEdit = Boolean(version);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatasetVersionFormValues>({
    resolver: zodResolver(datasetVersionFormSchema),
    defaultValues: {
      description: version?.description ?? "",
    },
  });

  useEffect(() => {
    reset({
      description: version?.description ?? "",
    });
  }, [version, reset]);

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit(onSubmit)}>
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
              : "Create Version"}
        </Button>
      </Stack>
    </Stack>
  );
}
