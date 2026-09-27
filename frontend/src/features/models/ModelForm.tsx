import { zodResolver } from "@hookform/resolvers/zod";
import {
  Button,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import type {
  Model,
  ModelProvider,
  ModelType,
} from "./api";

const modelFormSchema = z.object({
  name: z
    .string()
    .min(1, "Name is required")
    .max(150, "Name must be 150 characters or fewer"),
  provider: z.string().min(1, "Provider is required"),
  model_identifier: z
    .string()
    .min(1, "Model identifier is required")
    .max(
      150,
      "Model identifier must be 150 characters or fewer",
    ),
  model_type: z.string().min(1, "Model type is required"),
  configuration: z
    .string()
    .refine((value) => {
      if (!value.trim()) {
        return true;
      }

      try {
        const parsed = JSON.parse(value);
        return (
          parsed !== null &&
          typeof parsed === "object" &&
          !Array.isArray(parsed)
        );
      } catch {
        return false;
      }
    }, "Configuration must be a valid JSON object"),
  input_price_per_million: z.coerce
    .number()
    .min(0, "Input price cannot be negative"),
  output_price_per_million: z.coerce
    .number()
    .min(0, "Output price cannot be negative"),
  pricing_currency: z
    .string()
    .min(3, "Currency must be at least 3 characters")
    .max(10, "Currency must be 10 characters or fewer"),
});

type ModelFormValues = z.infer<typeof modelFormSchema>;

interface ModelFormProps {
  model?: Model;
  submitting?: boolean;
  onSubmit: (values: {
    name: string;
    provider: ModelProvider;
    model_identifier: string;
    model_type: ModelType;
    configuration: Record<string, unknown> | null;
    input_price_per_million: number;
    output_price_per_million: number;
    pricing_currency: string;
  }) => void | Promise<void>;
  onCancel: () => void;
}

const providers: { value: ModelProvider; label: string }[] = [
  { value: "mock", label: "Mock" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "google", label: "Google" },
  { value: "ollama", label: "Ollama" },
  { value: "huggingface", label: "Hugging Face" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "custom", label: "Custom" },
];

const modelTypes: { value: ModelType; label: string }[] = [
  { value: "chat", label: "Chat" },
  { value: "completion", label: "Completion" },
  { value: "embedding", label: "Embedding" },
  { value: "reranker", label: "Reranker" },
  { value: "custom", label: "Custom" },
];

function configurationToString(
  configuration: Record<string, unknown> | null,
): string {
  return configuration
    ? JSON.stringify(configuration, null, 2)
    : "";
}

export function ModelForm({
  model,
  submitting = false,
  onSubmit,
  onCancel,
}: ModelFormProps) {
  const isEdit = Boolean(model);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ModelFormValues>({
    resolver: zodResolver(modelFormSchema),
    defaultValues: {
      name: model?.name ?? "",
      provider: model?.provider ?? "",
      model_identifier: model?.model_identifier ?? "",
      model_type: model?.model_type ?? "chat",
      configuration: configurationToString(
        model?.configuration ?? null,
      ),
      input_price_per_million:
        model?.input_price_per_million ?? 0,
      output_price_per_million:
        model?.output_price_per_million ?? 0,
      pricing_currency: model?.pricing_currency ?? "USD",
    },
  });

  useEffect(() => {
    reset({
      name: model?.name ?? "",
      provider: model?.provider ?? "",
      model_identifier: model?.model_identifier ?? "",
      model_type: model?.model_type ?? "chat",
      configuration: configurationToString(
        model?.configuration ?? null,
      ),
      input_price_per_million:
        model?.input_price_per_million ?? 0,
      output_price_per_million:
        model?.output_price_per_million ?? 0,
      pricing_currency: model?.pricing_currency ?? "USD",
    });
  }, [model, reset]);

  const handleFormSubmit = (values: ModelFormValues) => {
    const configuration = values.configuration.trim()
      ? JSON.parse(values.configuration)
      : null;

    return onSubmit({
      name: values.name,
      provider: values.provider as ModelProvider,
      model_identifier: values.model_identifier,
      model_type: values.model_type as ModelType,
      configuration,
      input_price_per_million:
        values.input_price_per_million,
      output_price_per_million:
        values.output_price_per_million,
      pricing_currency: values.pricing_currency,
    });
  };

  return (
    <Stack
      component="form"
      spacing={2.5}
      onSubmit={handleSubmit(handleFormSubmit)}
    >
      <TextField
        label="Name"
        fullWidth
        {...register("name")}
        error={Boolean(errors.name)}
        helperText={errors.name?.message}
        disabled={submitting}
      />

      <FormControl
        fullWidth
        error={Boolean(errors.provider)}
        disabled={submitting}
      >
        <InputLabel id="model-provider-label">
          Provider
        </InputLabel>

        <Select
          labelId="model-provider-label"
          label="Provider"
          defaultValue={model?.provider ?? ""}
          {...register("provider")}
        >
          {providers.map((provider) => (
            <MenuItem
              key={provider.value}
              value={provider.value}
            >
              {provider.label}
            </MenuItem>
          ))}
        </Select>

        <FormHelperText>
          {errors.provider?.message}
        </FormHelperText>
      </FormControl>

      <TextField
        label="Model Identifier"
        fullWidth
        {...register("model_identifier")}
        error={Boolean(errors.model_identifier)}
        helperText={errors.model_identifier?.message}
        disabled={submitting}
      />

      <FormControl
        fullWidth
        error={Boolean(errors.model_type)}
        disabled={submitting}
      >
        <InputLabel id="model-type-label">
          Model Type
        </InputLabel>

        <Select
          labelId="model-type-label"
          label="Model Type"
          defaultValue={model?.model_type ?? "chat"}
          {...register("model_type")}
        >
          {modelTypes.map((modelType) => (
            <MenuItem
              key={modelType.value}
              value={modelType.value}
            >
              {modelType.label}
            </MenuItem>
          ))}
        </Select>

        <FormHelperText>
          {errors.model_type?.message}
        </FormHelperText>
      </FormControl>

      <TextField
        label="Configuration"
        fullWidth
        multiline
        minRows={6}
        placeholder={'{\n  "temperature": 0.2\n}'}
        {...register("configuration")}
        error={Boolean(errors.configuration)}
        helperText={
          errors.configuration?.message ??
          "Optional JSON object for model-specific configuration."
        }
        disabled={submitting}
        slotProps={{
          htmlInput: {
            spellCheck: false,
          },
        }}
      />

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
      >
        <TextField
          label="Input Price / 1M"
          type="number"
          fullWidth
          {...register("input_price_per_million")}
          error={Boolean(errors.input_price_per_million)}
          helperText={
            errors.input_price_per_million?.message
          }
          disabled={submitting}
          slotProps={{
            htmlInput: {
              min: 0,
              step: "any",
            },
          }}
        />

        <TextField
          label="Output Price / 1M"
          type="number"
          fullWidth
          {...register("output_price_per_million")}
          error={Boolean(errors.output_price_per_million)}
          helperText={
            errors.output_price_per_million?.message
          }
          disabled={submitting}
          slotProps={{
            htmlInput: {
              min: 0,
              step: "any",
            },
          }}
        />

        <TextField
          label="Currency"
          fullWidth
          {...register("pricing_currency")}
          error={Boolean(errors.pricing_currency)}
          helperText={errors.pricing_currency?.message}
          disabled={submitting}
        />
      </Stack>

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
              : "Create Model"}
        </Button>
      </Stack>
    </Stack>
  );
}
