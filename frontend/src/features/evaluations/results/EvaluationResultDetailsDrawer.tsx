import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import { CloseOutlined } from "@mui/icons-material";

import type { EvaluationResult } from "../api";
import EvaluationResultJsonSection from "./EvaluationResultJsonSection";
import EvaluationScores from "./EvaluationScores";
import { StatusChip } from "../../../components/common/StatusChip";

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
    <Dialog
      open={open && result !== null}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      scroll="paper"
      aria-labelledby="evaluation-result-dialog-title"
      slotProps={{ paper: { sx: { borderRadius: 3, maxHeight: "calc(100% - 32px)" } } }}
    >
      {result && (
        <>
          <DialogTitle
            id="evaluation-result-dialog-title"
            sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, pb: 1.5 }}
          >
            <Stack spacing={1}>
              <Typography variant="h6" sx={{ fontWeight: 700 }}>Case result</Typography>
              <StatusChip status={result.status} />
            </Stack>
            <IconButton aria-label="Close result details" title="Close result details" onClick={onClose}>
              <CloseOutlined />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ py: 0.5 }}>

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
              Input
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
              {result.input || "No input available."}
            </Typography>
          </Box>

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

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Scores</Typography>
            <EvaluationScores value={result.scores} />
          </Box>

          <EvaluationResultJsonSection
            title="Execution trace"
            value={result.trace}
          />
            </Stack>
          </DialogContent>
        </>
      )}
    </Dialog>
  );
}
