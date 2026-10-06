import React, { useEffect } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button, CircularProgress, Stack, TextField } from "@mui/material";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { DatasetVersion } from "./api";

const datasetVersionFormSchema = z.object({
  description: z
    .string()
    .max(500, "Description cannot exceed 500 characters.")
    .transform((val) => val.trim()),
});

export type DatasetVersionFormValues = z.infer<typeof datasetVersionFormSchema>;

interface DatasetVersionFormProps {
  version?: DatasetVersion | null;
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
    watch,
    formState: { errors },
  } = useForm<DatasetVersionFormValues>({
    resolver: zodResolver(datasetVersionFormSchema),
    defaultValues: {
      description: version?.description ?? "",
    },
  });

  const descriptionValue = watch("description", "");

  useEffect(() => {
    reset({
      description: version?.description ?? "",
    });
  }, [version, reset]);

  return (
    <Stack
      component="form"
      spacing={3}
      onSubmit={handleSubmit(onSubmit)}
      noValidate
    >
      <TextField
        label="Version Description"
        placeholder="Provide details about the context, changes, or focus of this dataset version..."
        fullWidth
        multiline
        minRows={3}
        maxRows={6}
        {...register("description")}
        error={Boolean(errors.description)}
        helperText={
          errors.description?.message ??
          `${descriptionValue.length}/500 characters`
        }
        disabled={submitting}
        slotProps={{
          input: {
            sx: { borderRadius: 2 },
          },
          formHelperText: {
            sx: {
              display: "flex",
              justifyContent: errors.description ? "flex-start" : "flex-end",
            },
          },
        }}
      />

      <Stack direction="row" spacing={1.5} sx={{ justifyContent: "flex-end" }}>
        <Button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          sx={{ borderRadius: 2, textTransform: "none", fontWeight: 600 }}
        >
          Cancel
        </Button>

        <Button
          type="submit"
          variant="contained"
          disableElevation
          disabled={submitting}
          startIcon={
            submitting ? <CircularProgress size={16} color="inherit" /> : null
          }
          sx={{
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
            px: 3,
          }}
        >
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
