import React, { useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import FileUploadOutlinedIcon from "@mui/icons-material/FileUploadOutlined";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import CloseIcon from "@mui/icons-material/Close";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";

import { useImportDataset, useImportDatasetFile } from "./hooks";
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

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function DatasetVersionImportDialog({
  open,
  datasetId,
  onClose,
}: DatasetVersionImportDialogProps) {
  const theme = useTheme();
  const importMutation = useImportDataset();
  const importFileMutation = useImportDatasetFile();
  const isImportPending =
    importMutation.isPending || importFileMutation.isPending;
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);

  const resetState = () => {
    setSelectedFile(null);
    setError("");
    setIsDragOver(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClose = () => {
    if (isImportPending) {
      return;
    }
    resetState();
    onClose();
  };

  const processFile = async (file?: File) => {
    setError("");

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("Dataset files must be 10 MB or smaller.");
      setSelectedFile(null);
      return;
    }

    const extension = file.name.toLowerCase().split(".").pop();
    if (!extension || !["json", "csv", "xlsx"].includes(extension)) {
      setError("Choose a JSON, CSV, or Excel (.xlsx) file.");
      setSelectedFile(null);
      return;
    }

    try {
      if (extension === "json") {
        parseImportFile(await file.text());
      }
      setSelectedFile(file);
    } catch (err) {
      setSelectedFile(null);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to read the selected file.",
      );
    }
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    await processFile(file);
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    await processFile(file);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleImport = async () => {
    if (!selectedFile) {
      setError("Please select a dataset file to import.");
      return;
    }

    try {
      setError("");
      if (selectedFile.name.toLowerCase().endsWith(".json")) {
        const payload = parseImportFile(await selectedFile.text());
        await importMutation.mutateAsync({
          datasetId,
          payload,
          filename: selectedFile.name,
        });
      } else {
        await importFileMutation.mutateAsync({ datasetId, file: selectedFile });
      }

      handleClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete dataset import.",
      );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
      slotProps={{
        paper: {
          sx: {
            borderRadius: 3,
            p: 1,
          },
        },
      }}
    >
      <DialogTitle sx={{ pb: 1, fontWeight: 700 }}>
        Import Golden Dataset
      </DialogTitle>

      <DialogContent sx={{ pt: 1 }}>
        <Stack spacing={2.5}>
          {/* Subtitle Header & Helper Link */}
          <Stack spacing={1}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ lineHeight: 1.5 }}
            >
              Upload JSON, CSV, or Excel (.xlsx) evaluation cases. CSV and
              Excel files need an <strong>input</strong> column;{" "}
              <strong>expected_output</strong> and <strong>metadata</strong> are
              optional. Other columns are saved as metadata. A new golden
              dataset version will be created automatically upon import.
            </Typography>

            <Stack
              direction="row"
              spacing={1}
              useFlexGap
              flexWrap="wrap"
              sx={{ alignItems: "center" }}
            >
              <Typography variant="caption" color="text.secondary">
                Download a sample:
              </Typography>
              {[
                { label: "JSON", extension: "json" },
                { label: "CSV", extension: "csv" },
                { label: "Excel", extension: "xlsx" },
              ].map(({ label, extension }) => (
                <Button
                  key={extension}
                  component="a"
                  href={`/examples/dataset-import-sample.${extension}`}
                  download={`dataset-import-sample.${extension}`}
                  variant="text"
                  size="small"
                  startIcon={<FileDownloadOutlinedIcon fontSize="small" />}
                  sx={{
                    textTransform: "none",
                    fontWeight: 600,
                    fontSize: "0.8125rem",
                    px: 0.5,
                    minWidth: 0,
                  }}
                >
                  {label}
                </Button>
              ))}
            </Stack>
          </Stack>

          {/* Interactive Drag & Drop File Box */}
          <Paper
            variant="outlined"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            sx={{
              p: 3,
              borderRadius: 2.5,
              borderStyle: "dashed",
              borderWidth: 2,
              borderColor: isDragOver
                ? "primary.main"
                : selectedFile
                  ? "success.main"
                  : "divider",
              bgcolor: isDragOver
                ? alpha(theme.palette.primary.main, 0.04)
                : selectedFile
                  ? alpha(theme.palette.success.main, 0.02)
                  : alpha(theme.palette.action.hover, 0.05),
              cursor: isImportPending ? "not-allowed" : "pointer",
              transition: "all 0.2s ease-in-out",
              textAlign: "center",
              "&:hover": {
                borderColor: selectedFile ? "success.main" : "primary.main",
                bgcolor: alpha(theme.palette.primary.main, 0.03),
              },
            }}
          >
            <input
              ref={fileInputRef}
              hidden
              type="file"
              accept=".json,.csv,.xlsx,application/json,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(event) => {
                void handleFileChange(event);
              }}
              disabled={isImportPending}
            />

            <Stack spacing={1.5} sx={{ alignItems: "center" }}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  bgcolor: selectedFile
                    ? alpha(theme.palette.success.main, 0.1)
                    : alpha(theme.palette.primary.main, 0.1),
                  color: selectedFile ? "success.main" : "primary.main",
                }}
              >
                {selectedFile ? (
                  <CheckCircleOutlinedIcon />
                ) : (
                  <FileUploadOutlinedIcon />
                )}
              </Box>

              <Stack spacing={0.5}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {selectedFile
                    ? "File loaded successfully"
                    : "Click to upload or drag & drop"}
                </Typography>

                <Typography variant="caption" color="text.secondary">
                  JSON, CSV, or Excel (.xlsx), up to 10 MB
                </Typography>
              </Stack>
            </Stack>
          </Paper>

          {/* Selected File Details Card */}
          {selectedFile && (
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: alpha(theme.palette.background.paper, 0.8),
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Stack
                direction="row"
                spacing={1.5}
                sx={{ alignItems: "center", minWidth: 0 }}
              >
                <InsertDriveFileOutlinedIcon color="primary" fontSize="small" />
                <Stack spacing={0} sx={{ minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatBytes(selectedFile.size)}
                  </Typography>
                </Stack>
              </Stack>

              <Tooltip title="Remove file">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    resetState();
                  }}
                  disabled={isImportPending}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Paper>
          )}

          {/* Validation & Backend Errors */}
          {error && (
            <Alert
              severity="error"
              sx={{ borderRadius: 2 }}
              onClose={() => setError("")}
            >
              <Typography variant="body2">{error}</Typography>
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2, pt: 1 }}>
        <Button
          onClick={handleClose}
          disabled={isImportPending}
          sx={{ borderRadius: 2, textTransform: "none", fontWeight: 600 }}
        >
          Cancel
        </Button>

        <Button
          variant="contained"
          disableElevation
          onClick={() => {
            void handleImport();
          }}
          disabled={!selectedFile || isImportPending}
          startIcon={
            isImportPending ? (
              <CircularProgress size={16} color="inherit" />
            ) : null
          }
          sx={{
            borderRadius: 2,
            textTransform: "none",
            fontWeight: 600,
            px: 3,
          }}
        >
          {isImportPending ? "Importing..." : "Import Dataset"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
