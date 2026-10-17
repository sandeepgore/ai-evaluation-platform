import {
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import { CloseOutlined } from "@mui/icons-material";

import type { EvaluationResult } from "../api";
import EvaluationResultJsonSection from "./EvaluationResultJsonSection";

interface EvaluationResultDetailsDrawerProps {
  result: EvaluationResult | null;
  open: boolean;
  onClose: () => void;
}

export default function EvaluationResultDetailsDrawer({
  result,
  open,
  onClose,
}: EvaluationResultDetailsDrawerProps) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      slotProps={{
        paper: {
          sx: {
            width: { xs: "100%", sm: 560 },
            maxWidth: "100%",
            p: 0,
          },
        },
      }}
    >
      {result && (
        <Stack spacing={2} sx={{ p: { xs: 2, sm: 3 } }}>
          <Stack
            sx={{
              display: "flex",
              flexDirection: "row",
              alignItems: "flex-start",
              gap: 1,
            }}
          >
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>
                Case result
              </Typography>
            </Box>

            <IconButton aria-label="Close result details" onClick={onClose}>
              <CloseOutlined />
            </IconButton>
          </Stack>

          <Chip
            label={result.status.replaceAll("_", " ")}
            variant="outlined"
            sx={{ alignSelf: "flex-start" }}
          />

          <Divider />

          {result.error_message && (
            <Box
              sx={{
                p: 2,
                borderRadius: 1,
                border: 1,
                borderColor: "error.light",
                bgcolor: "error.lighter",
              }}
            >
              <Typography variant="subtitle2" color="error.main">
                Error
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  mt: 0.5,
                  whiteSpace: "pre-wrap",
                  overflowWrap: "anywhere",
                }}
              >
                {result.error_message}
              </Typography>
            </Box>
          )}

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Expected output
            </Typography>
            <Typography
              variant="body2"
              sx={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                p: 1.5,
                borderRadius: 1,
                bgcolor: "action.hover",
              }}
            >
              {result.expected_output || "No expected output available."}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Actual output
            </Typography>
            <Typography
              variant="body2"
              sx={{
                whiteSpace: "pre-wrap",
                overflowWrap: "anywhere",
                p: 1.5,
                borderRadius: 1,
                bgcolor: "action.hover",
              }}
            >
              {result.actual_output || "No actual output available."}
            </Typography>
          </Box>

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Evaluator feedback
            </Typography>
            <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
              {result.feedback || "No feedback available."}
            </Typography>
          </Box>

          <EvaluationResultJsonSection
            title="Scores"
            value={result.scores}
            defaultExpanded
          />

          <EvaluationResultJsonSection
            title="Execution trace"
            value={result.trace}
          />
        </Stack>
      )}
    </Drawer>
  );
}
