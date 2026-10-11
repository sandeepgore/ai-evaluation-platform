import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Typography,
} from "@mui/material";
import { ExpandMore } from "@mui/icons-material";

interface EvaluationResultJsonSectionProps {
  title: string;
  value: unknown;
  defaultExpanded?: boolean;
}

function formatJson(value: unknown): string {
  if (typeof value === "string") return value;

  try {
    const serialized = JSON.stringify(value, null, 2);
    return serialized ?? "No data available.";
  } catch {
    return "Unable to display this data.";
  }
}

export default function EvaluationResultJsonSection({
  title,
  value,
  defaultExpanded = false,
}: EvaluationResultJsonSectionProps) {
  const hasValue = value !== null && value !== undefined;

  return (
    <Accordion
      variant="outlined"
      defaultExpanded={defaultExpanded}
      disableGutters
    >
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Typography sx={{ fontWeight: 600 }}>{title}</Typography>
      </AccordionSummary>

      <AccordionDetails>
        {hasValue ? (
          <Box
            component="pre"
            sx={{
              m: 0,
              p: 1.5,
              maxWidth: "100%",
              overflowX: "auto",
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              fontFamily: "monospace",
              fontSize: 12,
              bgcolor: "action.hover",
              borderRadius: 1,
            }}
          >
            {formatJson(value)}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No data available.
          </Typography>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
