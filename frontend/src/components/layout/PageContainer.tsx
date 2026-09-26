import { Box, Container } from "@mui/material";
import type { ReactNode } from "react";

interface PageContainerProps {
  children: ReactNode;
}

export function PageContainer({ children }: PageContainerProps) {
  return (
    <Container
      maxWidth={false}
      component="main"
      sx={{
        flex: 1,
        px: { xs: 2, md: 3 },
        py: 3,
      }}
    >
      <Box sx={{ width: "100%" }}>{children}</Box>
    </Container>
  );
}