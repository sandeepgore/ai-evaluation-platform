import React, { useState } from "react";
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import CodeIcon from "@mui/icons-material/Code";
import InputIcon from "@mui/icons-material/Input";
import OutputIcon from "@mui/icons-material/Output";

import type { DatasetCase } from "./api";

interface DatasetCaseViewDialogProps {
  open: boolean;
  datasetCase: DatasetCase | null;
  onClose: () => void;
}

function safeJsonStringify(data: unknown): string {
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return "// Error: Unable to serialize metadata JSON";
  }
}

export function DatasetCaseViewDialog({
  open,
  datasetCase,
  onClose,
}: DatasetCaseViewDialogProps) {
  const theme = useTheme();
  const [copied, setCopied] = useState(false);

  const handleCopyMetadata = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback handling if clipboard API is restricted
    }
  };

  const formattedMetadata = datasetCase?.case_metadata
    ? safeJsonStringify(datasetCase.case_metadata)
    : null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      aria-labelledby="dataset-case-dialog-title"
      scroll="paper"
      slotProps={{
        paper: {
          elevation: 12,
          sx: {
            borderRadius: 2.5,
            overflow: "hidden",
          },
        },
      }}
    >
      {/* Header */}
      <DialogTitle
        id="dataset-case-dialog-title"
        sx={{
          m: 0,
          px: 3,
          py: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          bgcolor: (theme) =>
            theme.palette.mode === "dark"
              ? alpha(theme.palette.common.white, 0.03)
              : alpha(theme.palette.common.black, 0.02),
        }}
      >
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
          <Typography
            variant="h6"
            sx={{ fontWeight: 600, fontSize: "1.125rem" }}
          >
            Dataset Case Details
          </Typography>
          {datasetCase?.id && (
            <Chip
              label={`ID: ${datasetCase.id}`}
              size="small"
              sx={{
                fontFamily: "monospace",
                fontSize: "0.75rem",
                bgcolor: alpha(theme.palette.primary.main, 0.08),
                color: theme.palette.primary.main,
                fontWeight: 600,
                border: "none",
              }}
            />
          )}
        </Stack>

        <IconButton
          aria-label="close"
          onClick={onClose}
          size="small"
          sx={{
            color: theme.palette.text.secondary,
            "&:hover": {
              color: theme.palette.text.primary,
              bgcolor: alpha(theme.palette.text.primary, 0.06),
            },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <Divider />

      {/* Content */}
      <DialogContent sx={{ p: 3 }}>
        {datasetCase ? (
          <Stack spacing={3}>
            {/* Input Card */}
            <Box>
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: "center", mb: 1 }}
              >
                <InputIcon color="action" fontSize="small" />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    fontWeight: 700,
                    letterSpacing: 0.8,
                    textTransform: "uppercase",
                  }}
                >
                  Prompt Input
                </Typography>
              </Stack>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  bgcolor: (theme) =>
                    theme.palette.mode === "dark"
                      ? alpha(theme.palette.common.white, 0.02)
                      : alpha(theme.palette.common.black, 0.01),
                  borderColor: theme.palette.divider,
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    lineHeight: 1.6,
                    fontFamily: "inherit",
                    color: "text.primary",
                  }}
                >
                  {datasetCase.input || "No input prompt available."}
                </Typography>
              </Paper>
            </Box>

            {/* Expected Output Card */}
            <Box>
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: "center", mb: 1 }}
              >
                <OutputIcon color="action" fontSize="small" />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    fontWeight: 700,
                    letterSpacing: 0.8,
                    textTransform: "uppercase",
                  }}
                >
                  Expected Output
                </Typography>
              </Stack>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  bgcolor: (theme) =>
                    theme.palette.mode === "dark"
                      ? alpha(theme.palette.common.white, 0.02)
                      : alpha(theme.palette.common.black, 0.01),
                  borderColor: theme.palette.divider,
                  borderRadius: 2,
                }}
              >
                <Typography
                  variant="body2"
                  color={
                    datasetCase.expected_output
                      ? "text.primary"
                      : "text.secondary"
                  }
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    fontStyle: datasetCase.expected_output
                      ? "normal"
                      : "italic",
                    lineHeight: 1.6,
                  }}
                >
                  {datasetCase.expected_output ?? "Not provided for this case."}
                </Typography>
              </Paper>
            </Box>

            {/* Metadata Section */}
            {formattedMetadata && (
              <Box>
                <Stack
                  direction="row"
                  sx={{
                    justifyContent: "space-between",
                    alignItems: "center",
                    mb: 1,
                  }}
                >
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: "center" }}
                  >
                    <CodeIcon color="action" fontSize="small" />
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{
                        fontWeight: 700,
                        letterSpacing: 0.8,
                        textTransform: "uppercase",
                      }}
                    >
                      Case Metadata
                    </Typography>
                  </Stack>

                  <Tooltip
                    title={copied ? "Copied!" : "Copy JSON to clipboard"}
                    placement="top"
                  >
                    <Button
                      size="small"
                      startIcon={
                        copied ? (
                          <CheckIcon fontSize="small" />
                        ) : (
                          <ContentCopyIcon fontSize="small" />
                        )
                      }
                      onClick={() => handleCopyMetadata(formattedMetadata)}
                      sx={{
                        textTransform: "none",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        px: 1.2,
                        py: 0.4,
                      }}
                    >
                      {copied ? "Copied" : "Copy JSON"}
                    </Button>
                  </Tooltip>
                </Stack>

                <Paper
                  variant="outlined"
                  sx={{
                    borderRadius: 2,
                    overflow: "hidden",
                    borderColor: theme.palette.divider,
                  }}
                >
                  <Box
                    component="pre"
                    sx={{
                      m: 0,
                      p: 2,
                      bgcolor: (theme) =>
                        theme.palette.mode === "dark" ? "#0D1117" : "#F6F8FA",
                      overflowX: "auto",
                      fontSize: "0.8125rem",
                      fontFamily:
                        'ui-monospace, SFMono-Regular, "SF Pro Text", "Roboto Mono", Consolas, monospace',
                      lineHeight: 1.5,
                      color: (theme) =>
                        theme.palette.mode === "dark" ? "#C9D1D9" : "#24292E",
                      "&::-webkit-scrollbar": {
                        height: 6,
                        width: 6,
                      },
                      "&::-webkit-scrollbar-thumb": {
                        bgcolor: alpha(theme.palette.text.primary, 0.15),
                        borderRadius: 3,
                      },
                    }}
                  >
                    <code>{formattedMetadata}</code>
                  </Box>
                </Paper>
              </Box>
            )}
          </Stack>
        ) : (
          <Box sx={{ py: 6, textAlign: "center" }}>
            <Typography color="text.secondary" variant="body2">
              No dataset case selected.
            </Typography>
          </Box>
        )}
      </DialogContent>

      <Divider />

      {/* Action Footer */}
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          onClick={onClose}
          variant="contained"
          disableElevation
          sx={{
            px: 3,
            borderRadius: 1.5,
            textTransform: "none",
            fontWeight: 600,
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
