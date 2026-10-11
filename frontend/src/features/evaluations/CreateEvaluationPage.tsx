import { useEffect, useMemo, useState } from "react";
import { ArrowBackOutlined, PlayCircleOutlined } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import { useAppContextStore } from "../../store/appContextStore";
import { useDatasets } from "../datasets/hooks";
import { useDatasetVersions } from "../datasetVersions/hooks";
import { useModels } from "../models/hooks";
import type { EvaluationType } from "./api";
import { useCreateEvaluationRun } from "./hooks";

const EVALUATION_TYPES: {
  value: EvaluationType;
  label: string;
  description: string;
}[] = [
  {
    value: "text",
    label: "Text Generation",
    description: "Evaluate generated responses against expected answers.",
  },
  {
    value: "rag",
    label: "RAG Evaluation",
    description: "Evaluate responses produced using retrieved context.",
  },
  {
    value: "conversation",
    label: "Conversational AI",
    description: "Evaluate multi-turn conversational responses.",
  },
  {
    value: "safety",
    label: "Safety & Guardrails",
    description: "Evaluate safety-related behavior and guardrails.",
  },
];

export function CreateEvaluationPage() {
  const navigate = useNavigate();

  const selectedProjectId = useAppContextStore(
    (state) => state.selectedProjectId,
  );

  const { data: datasets, isLoading: isDatasetsLoading } =
    useDatasets(selectedProjectId);

  const { data: models, isLoading: isModelsLoading } =
    useModels(selectedProjectId);

  const [datasetId, setDatasetId] = useState("");
  const [datasetVersionId, setDatasetVersionId] = useState("");
  const [modelId, setModelId] = useState("");
  const [name, setName] = useState("");
  const [evaluationType, setEvaluationType] = useState<EvaluationType>("text");
  const [formError, setFormError] = useState("");

  const {
    data: versions,
    isLoading: isVersionsLoading,
    isError: isVersionsError,
  } = useDatasetVersions(datasetId || null);

  const createMutation = useCreateEvaluationRun();

  const readyVersions = useMemo(
    () =>
      (versions ?? []).filter(
        (version) => version.is_active && version.status === "ready",
      ),
    [versions],
  );

  const activeDatasets = useMemo(
    () => (datasets ?? []).filter((dataset) => dataset.is_active),
    [datasets],
  );

  const activeModels = useMemo(
    () => (models ?? []).filter((model) => model.is_active),
    [models],
  );

  useEffect(() => {
    setDatasetVersionId("");
  }, [datasetId]);

  useEffect(() => {
    if (!readyVersions.some((version) => version.id === datasetVersionId)) {
      setDatasetVersionId("");
    }
  }, [readyVersions, datasetVersionId]);

  useEffect(() => {
    if (!activeDatasets.some((dataset) => dataset.id === datasetId)) {
      setDatasetId("");
    }
  }, [activeDatasets, datasetId]);

  useEffect(() => {
    if (!activeModels.some((model) => model.id === modelId)) {
      setModelId("");
    }
  }, [activeModels, modelId]);

  const isLoading = isDatasetsLoading || isModelsLoading;

  const selectedType = EVALUATION_TYPES.find(
    (type) => type.value === evaluationType,
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError("");

    if (!selectedProjectId) {
      setFormError("Select a project before creating an evaluation.");
      return;
    }

    if (!datasetId || !datasetVersionId || !modelId || !name.trim()) {
      setFormError("Complete all required fields before continuing.");
      return;
    }

    const selectedVersion = readyVersions.find(
      (version) => version.id === datasetVersionId,
    );

    if (!selectedVersion) {
      setFormError(
        "Select an active, finalized dataset version before continuing.",
      );
      return;
    }

    try {
      const run = await createMutation.mutateAsync({
        dataset_version_id: datasetVersionId,
        model_id: modelId,
        name: name.trim(),
        evaluation_type: evaluationType,
        mode: "default",
        configuration: {
          data_policy: {
            type: "partial",
          },
        },
      });

      navigate(`/evaluations/${run.id}`);
    } catch {
      // The mutation hook displays the API error notification.
    }
  };

  if (!selectedProjectId) {
    return (
      <Stack spacing={2}>
        <Button
          startIcon={<ArrowBackOutlined />}
          onClick={() => navigate("/evaluations")}
          sx={{ alignSelf: "flex-start", textTransform: "none" }}
        >
          Back to Evaluations
        </Button>

        <Alert severity="info">
          Select a project from the application context before creating an
          evaluation.
        </Alert>
      </Stack>
    );
  }

  if (isLoading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          py: 8,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={3} sx={{ maxWidth: 800, mx: "auto", width: "100%" }}>
      <Button
        startIcon={<ArrowBackOutlined />}
        onClick={() => navigate("/evaluations")}
        sx={{ alignSelf: "flex-start", textTransform: "none" }}
      >
        Back to Evaluations
      </Button>

      <Box>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>
          Create Evaluation
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Configure a new evaluation run using a finalized dataset version and
          an active model.
        </Typography>
      </Box>

      {formError && (
        <Alert severity="error" onClose={() => setFormError("")}>
          {formError}
        </Alert>
      )}

      {activeDatasets.length === 0 && (
        <Alert severity="info">
          No active datasets are available in the selected project.
        </Alert>
      )}

      {activeModels.length === 0 && (
        <Alert severity="info">
          No active models are available in the selected project.
        </Alert>
      )}

      <Paper
        component="form"
        variant="outlined"
        onSubmit={handleSubmit}
        sx={{ p: { xs: 2, sm: 4 }, borderRadius: 3 }}
      >
        <Stack spacing={3}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Evaluation Configuration
          </Typography>

          <TextField
            label="Evaluation Name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
            fullWidth
            slotProps={{
              htmlInput: {
                maxLength: 150,
              },
            }}
            helperText="Choose a name that identifies this evaluation run."
          />

          <TextField
            select
            label="Dataset"
            value={datasetId}
            onChange={(event) => setDatasetId(event.target.value)}
            required
            fullWidth
            disabled={activeDatasets.length === 0}
            helperText="Choose an active dataset from the selected project."
          >
            {activeDatasets.map((dataset) => (
              <MenuItem key={dataset.id} value={dataset.id}>
                {dataset.name}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Dataset Version"
            value={datasetVersionId}
            onChange={(event) => setDatasetVersionId(event.target.value)}
            required
            fullWidth
            disabled={!datasetId || isVersionsLoading || isVersionsError}
            helperText={
              !datasetId
                ? "Select a dataset first."
                : isVersionsLoading
                  ? "Loading dataset versions..."
                  : isVersionsError
                    ? "Unable to load versions. Please try again."
                    : readyVersions.length === 0
                      ? "No active, finalized versions are available."
                      : "Only active, finalized versions are selectable."
            }
          >
            {readyVersions.map((version) => (
              <MenuItem key={version.id} value={version.id}>
                Version {version.version} ({version.case_count} cases)
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Model"
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
            required
            fullWidth
            disabled={activeModels.length === 0}
            helperText="Choose an active model from the selected project."
          >
            {activeModels.map((model) => (
              <MenuItem key={model.id} value={model.id}>
                {model.name} — {model.provider}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            select
            label="Evaluation Type"
            value={evaluationType}
            onChange={(event) =>
              setEvaluationType(event.target.value as EvaluationType)
            }
            required
            fullWidth
          >
            {EVALUATION_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </TextField>

          {selectedType && (
            <Alert severity="info" icon={false}>
              {selectedType.description}
            </Alert>
          )}

          <Divider />

          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Execution Mode
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Default mode uses the platform's default evaluation configuration.
              Advanced configuration can be added separately.
            </Typography>
          </Box>

          <Stack
            direction={{ xs: "column-reverse", sm: "row" }}
            spacing={1.5}
            sx={{ justifyContent: "flex-end" }}
          >
            <Button
              variant="outlined"
              onClick={() => navigate("/evaluations")}
              disabled={createMutation.isPending}
              sx={{ textTransform: "none", borderRadius: 2 }}
            >
              Cancel
            </Button>

            <Button
              type="submit"
              variant="contained"
              disableElevation
              startIcon={
                createMutation.isPending ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <PlayCircleOutlined />
                )
              }
              disabled={
                createMutation.isPending ||
                !name.trim() ||
                !datasetId ||
                !datasetVersionId ||
                !modelId ||
                activeDatasets.length === 0 ||
                activeModels.length === 0
              }
              sx={{
                textTransform: "none",
                borderRadius: 2,
                fontWeight: 600,
                px: 3,
              }}
            >
              {createMutation.isPending ? "Creating..." : "Create Evaluation"}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
