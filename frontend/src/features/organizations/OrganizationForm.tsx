import { zodResolver } from "@hookform/resolvers/zod";
import {
  Button,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
} from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type { Organization } from "./api";

const organizationFormSchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(150, "Name must be 150 characters or fewer"),
  slug: z
    .string()
    .min(1, "Slug is required")
    .max(100, "Slug must be 100 characters or fewer"),
  description: z.string(),
  is_active: z.boolean(),
});

type OrganizationFormValues = z.infer<typeof organizationFormSchema>;

interface OrganizationFormProps {
  organization?: Organization;
  submitting?: boolean;
  onSubmit: (
    values: OrganizationFormValues,
  ) => void | Promise<void>;
  onCancel: () => void;
}

export function OrganizationForm({
  organization,
  submitting = false,
  onSubmit,
  onCancel,
}: OrganizationFormProps) {
  const isEdit = Boolean(organization);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
    setValue,
    watch,
  } = useForm<OrganizationFormValues>({
    resolver: zodResolver(organizationFormSchema),
    defaultValues: {
      name: organization?.name ?? "",
      slug: organization?.slug ?? "",
      description: organization?.description ?? "",
      is_active: organization?.is_active ?? true,
    },
  });

  useEffect(() => {
    reset({
      name: organization?.name ?? "",
      slug: organization?.slug ?? "",
      description: organization?.description ?? "",
      is_active: organization?.is_active ?? true,
    });
  }, [organization, reset]);

  const isActive = watch("is_active");

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

      {isEdit && (
        <FormControlLabel
          control={
            <Switch
              checked={isActive}
              onChange={(event) =>
                setValue("is_active", event.target.checked, {
                  shouldDirty: true,
                })
              }
              disabled={submitting}
            />
          }
          label="Active"
        />
      )}

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
              : "Create Organization"}
        </Button>
      </Stack>
    </Stack>
  );
}