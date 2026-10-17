import { useEffect, useMemo, useState } from "react";
import { PlayCircleOutlined } from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  MenuItem,
  Paper,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { AppBreadcrumbs } from "../../components/common/AppBreadcrumbs";

import { useAppContextStore } from "../../store/appContextStore";
import { useDatasets } from "../datasets/hooks";
import { useDatasetVersions } from "../datasetVersions/hooks";
import { useModels } from "../models/hooks";
import type { EvaluationRunMode, EvaluationType } from "./api";
import {
  useCreateEvaluationRun,
  useCreateEvaluationSchedule,
  useEvaluators,
} from "./hooks";

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

function defaultScheduleDateTime() {
  const date = new Date(Date.now() + 60 * 60 * 1000);
  date.setMinutes(0, 0, 0);
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 16);
}

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
  const [mode, setMode] = useState<EvaluationRunMode>("default");
  const [dataPolicy, setDataPolicy] = useState("partial");
  const [threshold, setThreshold] = useState("0.8");
  const [promptChoice, setPromptChoice] = useState("dataset");
  const [promptInstruction, setPromptInstruction] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userTemplate, setUserTemplate] = useState("{{input}}");
  const [selectedEvaluators, setSelectedEvaluators] = useState<string[]>([]);
  const [evaluatorWeights, setEvaluatorWeights] = useState<Record<string, string>>({});
  const [executionMode, setExecutionMode] = useState("sequential");
  const [batchSize, setBatchSize] = useState("10");
  const [judgeModelId, setJudgeModelId] = useState("");
  const [formError, setFormError] = useState("");
  const [runTiming, setRunTiming] = useState<"now" | "scheduled">("now");
  const [scheduleType, setScheduleType] = useState<"one_time" | "recurring">("one_time");
  const [scheduledAt, setScheduledAt] = useState(defaultScheduleDateTime);
  const [scheduleExpression, setScheduleExpression] = useState("0 9 * * *");
  const [scheduleTimezone, setScheduleTimezone] = useState(
    () => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
  );

  const {
    data: versions,
    isLoading: isVersionsLoading,
    isError: isVersionsError,
  } = useDatasetVersions(datasetId || null);

  const createMutation = useCreateEvaluationRun();
  const createScheduleMutation = useCreateEvaluationSchedule();
  const {
    data: evaluators,
    isLoading: isEvaluatorsLoading,
    isError: isEvaluatorsError,
  } = useEvaluators(mode === "advanced");

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

  const availableEvaluators = (evaluators ?? []).filter(
    (evaluator) =>
      evaluator.applicable_to.length === 0 ||
      evaluator.applicable_to.includes(evaluationType),
  );
  const selectedAvailableEvaluators = selectedEvaluators.filter((name) =>
    availableEvaluators.some((evaluator) => evaluator.name === name),
  );

  const promptConfiguration =
    promptChoice === "instruction" && promptInstruction.trim()
      ? { mode: "simple", instruction: promptInstruction.trim() }
      : promptChoice === "template" &&
          (systemPrompt.trim() || userTemplate.trim())
        ? {
            mode: "advanced",
            ...(systemPrompt.trim() ? { system: systemPrompt.trim() } : {}),
            ...(userTemplate.trim() ? { user_template: userTemplate.trim() } : {}),
          }
        : undefined;

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

    if (dataPolicy === "threshold") {
      const parsedThreshold = Number(threshold);
      if (!Number.isFinite(parsedThreshold) || parsedThreshold < 0 || parsedThreshold > 1) {
        setFormError("Data policy threshold must be between 0 and 1.");
        return;
      }
    }

    if (promptChoice === "instruction" && !promptInstruction.trim()) {
      setFormError("Enter an instruction or choose the dataset prompt.");
      return;
    }

    if (promptChoice === "template" && !systemPrompt.trim() && !userTemplate.trim()) {
      setFormError("Enter a system prompt or user template.");
      return;
    }

    if (promptChoice === "template") {
      const unsupportedTemplateVariable = [systemPrompt, userTemplate]
        .join("\n")
        .match(/\{\{\s*(?!input\s*\}|context\s*\})[a-zA-Z_][a-zA-Z0-9_]*\s*\}\}/);
      if (unsupportedTemplateVariable) {
        setFormError("Prompt templates support only {{input}} and {{context}} variables.");
        return;
      }
    }

    if (mode === "advanced" && selectedAvailableEvaluators.length === 0) {
      setFormError("Select at least one evaluator for advanced mode.");
      return;
    }

    const configuration: Record<string, unknown> = {
      data_policy: {
        type: dataPolicy,
        ...(dataPolicy === "threshold" ? { threshold: Number(threshold) } : {}),
      },
      ...(promptConfiguration ? { prompt: promptConfiguration } : {}),
    };

    if (mode === "advanced") {
      const selectedEvaluatorConfigs = selectedAvailableEvaluators.map((evaluatorName) => {
        const weight = Number(evaluatorWeights[evaluatorName] ?? "1");
        return { name: evaluatorName, weight };
      });
      if (selectedEvaluatorConfigs.some(({ weight }) => !Number.isFinite(weight) || weight <= 0)) {
        setFormError("Evaluator weights must be greater than zero.");
        return;
      }
      configuration.evaluators = selectedEvaluatorConfigs;
      configuration.execution_mode = executionMode;
      if (executionMode === "batch") {
        const parsedBatchSize = Number(batchSize);
        if (!Number.isInteger(parsedBatchSize) || parsedBatchSize <= 0) {
          setFormError("Batch size must be a positive whole number.");
          return;
        }
        configuration.batch_size = parsedBatchSize;
      }
      if (judgeModelId) configuration.judge_model_id = judgeModelId;
    }

    try {
      const runPayload = {
        dataset_version_id: datasetVersionId,
        model_id: modelId,
        name: name.trim(),
        evaluation_type: evaluationType,
        mode,
        configuration,
      };

      if (runTiming === "scheduled") {
        if (!scheduleTimezone.trim()) {
          setFormError("Enter a timezone for the schedule.");
          return;
        }

        if (scheduleType === "one_time") {
          const scheduledDate = new Date(scheduledAt);
          if (Number.isNaN(scheduledDate.getTime()) || scheduledDate.getTime() <= Date.now()) {
            setFormError("Choose a future date and time for the evaluation.");
            return;
          }
          await createScheduleMutation.mutateAsync({
            ...runPayload,
            schedule_type: "one_time",
            timezone: scheduleTimezone,
            next_run_at: scheduledDate.toISOString(),
          });
        } else {
          if (!scheduleExpression.trim()) {
            setFormError("Enter a cron expression for the recurring schedule.");
            return;
          }
          await createScheduleMutation.mutateAsync({
            ...runPayload,
            schedule_type: "recurring",
            schedule_expression: scheduleExpression.trim(),
            timezone: scheduleTimezone,
          });
        }
        navigate("/evaluations");
        return;
      }

      const run = await createMutation.mutateAsync(runPayload);

      navigate(`/evaluations/${run.id}`);
    } catch {
      // The mutation hook displays the API error notification.
    }
  };

  if (!selectedProjectId) {
    return (
      <Stack spacing={2}>
        <AppBreadcrumbs items={[{ label: "Evaluations", to: "/evaluations" }, { label: "Create" }]} />
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
    <Stack spacing={3} sx={{ maxWidth: 960, mx: "auto", width: "100%" }}>
      <AppBreadcrumbs items={[{ label: "Evaluations", to: "/evaluations" }, { label: "Create" }]} />

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

          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              When should this evaluation run?
            </Typography>
            <RadioGroup
              row
              value={runTiming}
              onChange={(event) => setRunTiming(event.target.value as "now" | "scheduled")}
              sx={{ mt: 0.5 }}
            >
              <FormControlLabel value="now" control={<Radio />} label="Run now" />
              <FormControlLabel value="scheduled" control={<Radio />} label="Schedule" />
            </RadioGroup>
            {runTiming === "scheduled" && (
              <Stack spacing={2} sx={{ mt: 1.5 }}>
                <Alert severity="info">
                  The scheduler creates and queues the evaluation when it is due. The selected evaluation settings are saved with the schedule.
                </Alert>
                <TextField
                  select
                  label="Schedule type"
                  value={scheduleType}
                  onChange={(event) => setScheduleType(event.target.value as "one_time" | "recurring")}
                  fullWidth
                >
                  <MenuItem value="one_time">Run once</MenuItem>
                  <MenuItem value="recurring">Repeat on a schedule</MenuItem>
                </TextField>
                {scheduleType === "one_time" ? (
                  <TextField
                    type="datetime-local"
                    label="Run at"
                    value={scheduledAt}
                    onChange={(event) => setScheduledAt(event.target.value)}
                    fullWidth
                    slotProps={{ inputLabel: { shrink: true } }}
                    helperText={`Uses your selected timezone: ${scheduleTimezone}`}
                  />
                ) : (
                  <TextField
                    label="Cron expression"
                    value={scheduleExpression}
                    onChange={(event) => setScheduleExpression(event.target.value)}
                    fullWidth
                    helperText="Five fields: minute hour day-of-month month day-of-week. Example: 0 9 * * 1 runs every Monday at 9:00."
                  />
                )}
                <TextField
                  label="Timezone"
                  value={scheduleTimezone}
                  onChange={(event) => setScheduleTimezone(event.target.value)}
                  fullWidth
                  helperText="Use an IANA timezone such as America/New_York or Asia/Kolkata."
                />
              </Stack>
            )}
          </Box>

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

          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Evaluation mode
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Use the recommended evaluator set or configure evaluators and execution options yourself.
            </Typography>
            <RadioGroup
              row
              value={mode}
              onChange={(event) => setMode(event.target.value as EvaluationRunMode)}
              sx={{ mt: 1 }}
            >
              <FormControlLabel
                value="default"
                control={<Radio />}
                label="Default"
                sx={{ mr: 3 }}
              />
              <FormControlLabel
                value="advanced"
                control={<Radio />}
                label="Advanced"
              />
            </RadioGroup>
          </Box>

          <Divider />

          <Stack spacing={2}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Data policy
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Choose how the evaluation handles cases missing data required by its evaluators.
              </Typography>
            </Box>
            <TextField
              select
              label="Missing-data policy"
              value={dataPolicy}
              onChange={(event) => setDataPolicy(event.target.value)}
              fullWidth
            >
              <MenuItem value="strict">Strict — require all evaluator data</MenuItem>
              <MenuItem value="partial">Partial — allow evaluators with available data</MenuItem>
              <MenuItem value="threshold">Threshold — require minimum data coverage</MenuItem>
            </TextField>
            {dataPolicy === "threshold" && (
              <TextField
                label="Minimum data coverage"
                type="number"
                value={threshold}
                onChange={(event) => setThreshold(event.target.value)}
                fullWidth
                inputProps={{ min: 0, max: 1, step: 0.05 }}
                helperText="Enter a value from 0 to 1. For example, 0.8 requires 80% coverage."
              />
            )}
          </Stack>

          <Divider />

          <Stack spacing={2}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Prompt
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Choose the prompt sent to the model for each dataset case.
              </Typography>
            </Box>
            <TextField
              select
              label="Prompt selection"
              value={promptChoice}
              onChange={(event) => setPromptChoice(event.target.value)}
              fullWidth
            >
              <MenuItem value="dataset">Use the prompt from each dataset case</MenuItem>
              <MenuItem value="instruction">Add an instruction to each case prompt</MenuItem>
              <MenuItem value="template">Build a custom prompt template</MenuItem>
            </TextField>
            {promptChoice === "instruction" && (
              <TextField
                label="Additional instruction"
                value={promptInstruction}
                onChange={(event) => setPromptInstruction(event.target.value)}
                multiline
                minRows={3}
                fullWidth
                helperText="This instruction is prepended to each case's input."
                inputProps={{ maxLength: 10_000 }}
              />
            )}
            {promptChoice === "template" && (
              <Stack spacing={2}>
                <TextField
                  label="System prompt"
                  value={systemPrompt}
                  onChange={(event) => setSystemPrompt(event.target.value)}
                  multiline
                  minRows={3}
                  fullWidth
                  helperText="Optional. Use {{input}} for the case input and {{context}} for retrieved context."
                  inputProps={{ maxLength: 10_000 }}
                />
                <TextField
                  label="User prompt template"
                  value={userTemplate}
                  onChange={(event) => setUserTemplate(event.target.value)}
                  multiline
                  minRows={3}
                  fullWidth
                  helperText="Use {{input}} and {{context}} where case data should be inserted."
                  inputProps={{ maxLength: 10_000 }}
                />
              </Stack>
            )}
          </Stack>

          {mode === "advanced" && (
            <>
              <Divider />
              <Stack spacing={2}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Advanced configuration
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    Select the metrics available for the chosen evaluation type, then optionally tune their weights, execution, and judge model.
                  </Typography>
                </Box>

                <Box
                  sx={{
                    px: 1.5,
                    py: 1,
                    borderRadius: 1.5,
                    bgcolor: "action.hover",
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Available metrics: {selectedType?.label ?? evaluationType}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {availableEvaluators.length} applicable {availableEvaluators.length === 1 ? "metric" : "metrics"}. Change the Evaluation Type above to update this list.
                  </Typography>
                </Box>

                {isEvaluatorsLoading && (
                  <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <CircularProgress size={18} />
                    <Typography variant="body2" color="text.secondary">
                      Loading available evaluators…
                    </Typography>
                  </Stack>
                )}
                {isEvaluatorsError && (
                  <Alert severity="error">
                    Available evaluators could not be loaded. Try again by switching modes or refreshing the page.
                  </Alert>
                )}
                {!isEvaluatorsLoading && !isEvaluatorsError && availableEvaluators.length === 0 && (
                  <Alert severity="warning">
                    No metrics are available for this evaluation type.
                  </Alert>
                )}
                {availableEvaluators.length > 0 && (
                  <Stack spacing={1}>
                    {availableEvaluators.map((evaluator) => {
                      const checked = selectedEvaluators.includes(evaluator.name);
                      return (
                        <Paper key={evaluator.name} variant="outlined" sx={{ p: 1.5, borderRadius: 2 }}>
                          <Stack
                            direction={{ xs: "column", sm: "row" }}
                            spacing={1}
                            sx={{ justifyContent: "space-between", alignItems: { sm: "center" } }}
                          >
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={checked}
                                  onChange={(event) => {
                                    setSelectedEvaluators((current) =>
                                      event.target.checked
                                        ? [...current, evaluator.name]
                                        : current.filter((item) => item !== evaluator.name),
                                    );
                                  }}
                                />
                              }
                              label={
                                <Box>
                                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                    {evaluator.name.replaceAll("_", " ")}
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary">
                                    {evaluator.description}
                                    {evaluator.required_inputs.length > 0
                                      ? ` Required data: ${evaluator.required_inputs.join(", ")}.`
                                      : ""}
                                  </Typography>
                                </Box>
                              }
                              sx={{ m: 0, flex: 1, minWidth: 0, alignItems: "flex-start" }}
                            />
                            {checked && (
                              <TextField
                                label="Weight"
                                type="number"
                                size="small"
                                value={evaluatorWeights[evaluator.name] ?? "1"}
                                onChange={(event) =>
                                  setEvaluatorWeights((current) => ({
                                    ...current,
                                    [evaluator.name]: event.target.value,
                                  }))
                                }
                                inputProps={{ min: 0.01, step: 0.1 }}
                                sx={{ width: { xs: "100%", sm: 130 } }}
                              />
                            )}
                          </Stack>
                        </Paper>
                      );
                    })}
                  </Stack>
                )}

                <TextField
                  select
                  label="Execution strategy"
                  value={executionMode}
                  onChange={(event) => setExecutionMode(event.target.value)}
                  fullWidth
                >
                  <MenuItem value="sequential">Sequential — process one case at a time</MenuItem>
                  <MenuItem value="batch">Batch — process cases in groups</MenuItem>
                </TextField>
                {executionMode === "batch" && (
                  <TextField
                    label="Cases per batch"
                    type="number"
                    value={batchSize}
                    onChange={(event) => setBatchSize(event.target.value)}
                    fullWidth
                    inputProps={{ min: 1, step: 1 }}
                  />
                )}
                <TextField
                  select
                  label="Judge model (optional)"
                  value={judgeModelId}
                  onChange={(event) => setJudgeModelId(event.target.value)}
                  fullWidth
                  helperText="Used by LLM-based evaluators when they need a separate judge model."
                >
                  <MenuItem value="">Use the default model</MenuItem>
                  {activeModels.map((model) => (
                    <MenuItem key={model.id} value={model.id}>
                      {model.name} — {model.provider}
                    </MenuItem>
                  ))}
                </TextField>
              </Stack>
            </>
          )}

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
                createMutation.isPending || createScheduleMutation.isPending ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <PlayCircleOutlined />
                )
              }
              disabled={
                createMutation.isPending || createScheduleMutation.isPending ||
                !name.trim() ||
                !datasetId ||
                !datasetVersionId ||
                !modelId ||
                activeDatasets.length === 0 ||
                activeModels.length === 0 ||
                (mode === "advanced" &&
                  (isEvaluatorsLoading ||
                    isEvaluatorsError ||
                    selectedAvailableEvaluators.length === 0))
              }
              sx={{
                textTransform: "none",
                borderRadius: 2,
                fontWeight: 600,
                px: 3,
              }}
            >
              {createMutation.isPending || createScheduleMutation.isPending
                ? "Saving..."
                : runTiming === "scheduled"
                  ? "Create Schedule"
                  : "Create Evaluation"}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
