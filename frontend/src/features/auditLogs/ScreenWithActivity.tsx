import type { ReactNode } from "react";
import { useState } from "react";
import { Box } from "@mui/material";
import { ScreenActivityPanel, type ActivityScreen } from "./ScreenActivityPanel";

export function ScreenWithActivity({ screen, children }: { screen: ActivityScreen; children: ReactNode }) {
  const [activityExpanded, setActivityExpanded] = useState(false);

  return (
    <Box
      sx={{
        display: "grid",
        width: "100%",
        minWidth: 0,
        gridTemplateColumns: {
          xs: "minmax(0, 1fr)",
          xl: activityExpanded
            ? "minmax(0, 1fr) minmax(280px, 320px)"
            : "minmax(0, 1fr) 48px",
        },
        gap: 2,
        alignItems: "start",
      }}
    >
      <Box sx={{ minWidth: 0, width: "100%" }}>{children}</Box>
      <ScreenActivityPanel
        screen={screen}
        expanded={activityExpanded}
        onToggle={() => setActivityExpanded((value) => !value)}
      />
    </Box>
  );
}
