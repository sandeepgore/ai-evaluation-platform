import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import type { DatasetCase } from "./api";

interface DatasetCaseViewDialogProps {
  open: boolean;
  datasetCase: DatasetCase | null;
  onClose: () => void;
}

export function DatasetCaseViewDialog({
  open,
  datasetCase,
  onClose,
}: DatasetCaseViewDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
    >
      <DialogTitle>Dataset Case</DialogTitle>

      <DialogContent>
        {datasetCase && (
          <Stack spacing={2.5}>
            <Box>
              <Typography
                variant="overline"
                color="text.secondary"
              >
                Input
              </Typography>
              <Typography
                variant="body1"
                sx={{ whiteSpace: "pre-wrap" }}
              >
                {datasetCase.input}
              </Typography>
            </Box>

            <Divider />

            <Box>
              <Typography
                variant="overline"
                color="text.secondary"
              >
                Expected Output
              </Typography>
              <Typography
                variant="body1"
                color={
                  datasetCase.expected_output
                    ? "text.primary"
                    : "text.secondary"
                }
                sx={{ whiteSpace: "pre-wrap" }}
              >
                {datasetCase.expected_output ?? "Not provided"}
              </Typography>
            </Box>

            {datasetCase.case_metadata && (
              <>
                <Divider />

                <Box>
                  <Typography
                    variant="overline"
                    color="text.secondary"
                  >
                    Metadata
                  </Typography>

                  <Box
                    component="pre"
                    sx={{
                      mt: 1,
                      mb: 0,
                      p: 2,
                      borderRadius: 1,
                      bgcolor: "action.hover",
                      overflowX: "auto",
                      fontSize: "0.875rem",
                      fontFamily: "monospace",
                    }}
                  >
                    {JSON.stringify(
                      datasetCase.case_metadata,
                      null,
                      2,
                    )}
                  </Box>
                </Box>
              </>
            )}
          </Stack>
        )}
      </DialogContent>
    </Dialog>
  );
}
