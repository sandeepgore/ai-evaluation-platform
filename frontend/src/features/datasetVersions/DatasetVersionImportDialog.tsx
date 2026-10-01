import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Typography,
} from "@mui/material";
import { useRef, useState } from "react";
import { useImportDataset } from "./hooks";
import type { DatasetImportPayload } from "./api";

interface DatasetVersionImportDialogProps {
  open: boolean;
  datasetId: string;
  onClose: () => void;
}

function parseImportFile(content: string): DatasetImportPayload {
  const parsed: unknown = JSON.parse(content);

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("JSON root must be an object.");
  }

  const root = parsed as Record<string, unknown>;

  if (!Array.isArray(root.cases) || root.cases.length === 0) {
    throw new Error("JSON must contain a non-empty cases array.");
  }

  const allowedRootFields = new Set(["cases"]);
  for (const field of Object.keys(root)) {
    if (!allowedRootFields.has(field)) {
      throw new Error(`Unexpected field: ${field}`);
    }
  }

  const cases = root.cases.map((item, index) => {
    if (typeof item !== "object" || item === null || Array.isArray(item)) {
      throw new Error(`Case ${index + 1} must be an object.`);
    }

    const caseItem = item as Record<string, unknown>;
    const allowedCaseFields = new Set(["input", "expected_output", "metadata"]);

    for (const field of Object.keys(caseItem)) {
      if (!allowedCaseFields.has(field)) {
        throw new Error(
          `Case ${index + 1} contains unexpected field: ${field}`,
        );
      }
    }

    if (
      typeof caseItem.input !== "string" ||
      caseItem.input.trim().length === 0
    ) {
      throw new Error(`Case ${index + 1} must contain a non-empty input.`);
    }

    if (
      caseItem.expected_output !== undefined &&
      caseItem.expected_output !== null &&
      typeof caseItem.expected_output !== "string"
    ) {
      throw new Error(
        `Case ${index + 1} expected_output must be a string or null.`,
      );
    }

    if (
      caseItem.metadata !== undefined &&
      caseItem.metadata !== null &&
      (typeof caseItem.metadata !== "object" ||
        Array.isArray(caseItem.metadata))
    ) {
      throw new Error(`Case ${index + 1} metadata must be an object or null.`);
    }

    return {
      input: caseItem.input,
      expected_output:
        caseItem.expected_output === undefined
          ? undefined
          : caseItem.expected_output,
      metadata:
        caseItem.metadata === undefined
          ? undefined
          : (caseItem.metadata as Record<string, unknown> | null),
    };
  });

  return { cases };
}

export function DatasetVersionImportDialog({
  open,
  datasetId,
  onClose,
}: DatasetVersionImportDialogProps) {
  const importMutation = useImportDataset();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");

  const resetState = () => {
    setFileName("");
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClose = () => {
    if (importMutation.isPending) {
      return;
    }

    resetState();
    onClose();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];

    setError("");
    setFileName("");

    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".json")) {
      setError("Please select a JSON file.");
      return;
    }

    try {
      const content = await file.text();
      parseImportFile(content);
      setFileName(file.name);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to read the JSON file.",
      );
    }
  };

  const handleImport = async () => {
    const file = fileInputRef.current?.files?.[0];

    if (!file) {
      setError("Please select a JSON file.");
      return;
    }

    try {
      const content = await file.text();
      const payload = parseImportFile(content);

      setError("");

      await importMutation.mutateAsync({
        datasetId,
        payload,
      });

      handleClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to import the dataset.",
      );
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Import Dataset JSON</DialogTitle>

      <DialogContent>
        <Stack spacing={2.5} sx={{ pt: 1 }}>
          <Stack spacing={0.75}>
            <Typography variant="body2" color="text.secondary">
              Upload a JSON file containing dataset cases. A new ready version
              will be created automatically.
            </Typography>

            <Button
              component="a"
              href="/examples/dataset-import-sample.json"
              download="dataset-import-sample.json"
              variant="text"
              sx={{ alignSelf: "flex-start", px: 0 }}
            >
              Download Sample JSON
            </Button>
          </Stack>

          <Button
            variant="outlined"
            component="label"
            disabled={importMutation.isPending}
          >
            Select JSON File
            <input
              ref={fileInputRef}
              hidden
              type="file"
              accept=".json,application/json"
              onChange={(event) => {
                void handleFileChange(event);
              }}
            />
          </Button>

          {fileName && (
            <Typography variant="body2">Selected: {fileName}</Typography>
          )}

          {error && <Alert severity="error">{error}</Alert>}
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={importMutation.isPending}>
          Cancel
        </Button>

        <Button
          variant="contained"
          onClick={() => {
            void handleImport();
          }}
          disabled={!fileName || importMutation.isPending}
        >
          {importMutation.isPending ? "Importing..." : "Import JSON"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
