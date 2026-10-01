import { zodResolver } from "@hookform/resolvers/zod";
import { Button, Stack, TextField } from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { DatasetCase } from "./api";

const datasetCaseFormSchema = z.object({
  input: z.string().min(1, "Input is required"),
  expected_output: z.string(),
  case_metadata: z.string().refine(
    (value) => {
      if (!value.trim()) {
        return true;
      }

      try {
        const parsed: unknown = JSON.parse(value);
        return (
          typeof parsed === "object" &&
          parsed !== null &&
          !Array.isArray(parsed)
        );
      } catch {
        return false;
      }
    },
    {
      message: "Metadata must be valid JSON containing an object.",
    },
  ),
});

type DatasetCaseFormValues = z.infer<typeof datasetCaseFormSchema>;

interface DatasetCaseFormProps {
  datasetCase?: DatasetCase;
  submitting?: boolean;
  onSubmit: (values: DatasetCaseFormValues) => void | Promise<void>;
  onCancel: () => void;
}

export function DatasetCaseForm({
  datasetCase,
  submitting = false,
  onSubmit,
  onCancel,
}: DatasetCaseFormProps) {
  const isEdit = Boolean(datasetCase);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DatasetCaseFormValues>({
    resolver: zodResolver(datasetCaseFormSchema),
    defaultValues: {
      input: datasetCase?.input ?? "",
      expected_output: datasetCase?.expected_output ?? "",
      case_metadata: datasetCase?.case_metadata
        ? JSON.stringify(datasetCase.case_metadata, null, 2)
        : "",
    },
  });

  useEffect(() => {
    reset({
      input: datasetCase?.input ?? "",
      expected_output: datasetCase?.expected_output ?? "",
      case_metadata: datasetCase?.case_metadata
        ? JSON.stringify(datasetCase.case_metadata, null, 2)
        : "",
    });
  }, [datasetCase, reset]);

  return (
    <Stack component="form" spacing={2.5} onSubmit={handleSubmit(onSubmit)}>
      <TextField
        label="Input"
        fullWidth
        multiline
        minRows={4}
        {...register("input")}
        error={Boolean(errors.input)}
        helperText={errors.input?.message}
        disabled={submitting}
      />

      <TextField
        label="Expected Output"
        fullWidth
        multiline
        minRows={4}
        {...register("expected_output")}
        disabled={submitting}
      />

      <TextField
        label="Metadata (JSON)"
        fullWidth
        multiline
        minRows={5}
        placeholder={'{\n  "category": "example"\n}'}
        {...register("case_metadata")}
        error={Boolean(errors.case_metadata)}
        helperText={
          errors.case_metadata?.message ??
          "Optional. Must be a valid JSON object."
        }
        disabled={submitting}
      />

      <Stack direction="row" spacing={1.5} sx={{ justifyContent: "flex-end" }}>
        <Button type="button" onClick={onCancel} disabled={submitting}>
          Cancel
        </Button>

        <Button type="submit" variant="contained" disabled={submitting}>
          {submitting ? "Saving..." : isEdit ? "Save Changes" : "Add Case"}
        </Button>
      </Stack>
    </Stack>
  );
}
